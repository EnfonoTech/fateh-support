"""Before-submit gate for Quotation, Sales Order, Sales Invoice.

Blocks submission when any item rate falls below the configured cost-floor
Price List, and creates a `Sales Price Approval Request` holding the details.
The originating document remains draft with `custom_approval_status =
"Pending Approval"` until an approver decides via the mobile app.

On re-submit after rejection:
- If the rate is still below floor, a fresh approval request is raised.
- If the requester has revised the rate above the floor, the old Rejected
  flag is cleared so the source doc submits cleanly.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, fmt_money


def _get_applicable_price_list(doc, settings) -> str:
    """Return the correct floor price list based on customer type."""
    customer = getattr(doc, "customer", None) or getattr(doc, "party_name", None)
    if customer:
        is_internal, represents = frappe.db.get_value(
            "Customer", customer, ["is_internal_customer", "represents_company"]
        ) or (0, None)
        if is_internal and represents:
            return (settings.get("inter_company_price_list") or "").strip()
    return (settings.get("cost_floor_price_list") or "").strip()


def _is_exempt_price_list(doc, settings) -> bool:
    """True when the document prices off a list that bypasses the gate.

    Some price lists are not customer pricing at all — inter-company transfers
    move stock between our own branches at cost, so comparing them against a
    customer-facing minimum blocks every one of them for no reason.
    """
    selling_list = (getattr(doc, "selling_price_list", None) or "").strip()
    if not selling_list:
        return False
    exempt = {
        (row.price_list or "").strip().lower()
        for row in (settings.get("exempt_price_lists") or [])
        if row.price_list
    }
    return selling_list.lower() in exempt


def _scrub_stale_flag(doc) -> None:
    """Clear a leftover Pending/Rejected flag so the document submits cleanly."""
    if getattr(doc, "custom_approval_status", None) not in ("Pending Approval", "Rejected"):
        return
    doc.custom_approval_status = ""
    doc.custom_approval_request = None
    frappe.db.set_value(
        doc.doctype,
        doc.name,
        {"custom_approval_status": "", "custom_approval_request": None},
        update_modified=False,
    )


def check_cost_floor(doc, method: str | None = None) -> None:
    """`before_submit` hook. May `frappe.throw()` to block submit."""
    if getattr(doc, "custom_approval_status", None) == "Approved":
        return

    settings = frappe.get_cached_doc("Fateh Support Settings")

    if _is_exempt_price_list(doc, settings):
        # Also clear any flag raised before the list was exempted, or the doc
        # would stay stuck behind a request nobody needs to decide.
        _scrub_stale_flag(doc)
        return

    cost_floor_list = _get_applicable_price_list(doc, settings)
    if not cost_floor_list:
        return

    violations = _collect_violations(doc, cost_floor_list)

    existing = getattr(doc, "custom_approval_request", None)
    existing_status = (
        frappe.db.get_value("Sales Price Approval Request", existing, "status")
        if existing
        else None
    )

    if not violations:
        # Rates now above floor. Drop any stale flag so submit proceeds cleanly
        # and the desk view no longer shows a red banner.
        _scrub_stale_flag(doc)
        return

    if not frappe.db.exists(doc.doctype, doc.name):
        # The document has never been saved. Frappe's insert() runs
        # before_submit BEFORE db_insert, so there is no row to hang an
        # approval request off yet, and throwing here would throw the
        # operator's work away with it — RMAX submits straight from a blank
        # form, there is no draft step to fall back on.
        #
        # Land it as a draft instead: run_post_save_methods dispatches on
        # `_action`, so downgrading both fields makes db_insert write
        # docstatus 0 and run on_update rather than on_submit. The request is
        # then raised from after_insert, once the row is really on disk.
        doc.docstatus = 0
        doc._action = "save"
        doc.flags.fateh_pending_violations = violations
        return

    if existing_status == "Pending":
        frappe.throw(
            _("Price approval already pending on {0}.").format(
                frappe.get_desk_link("Sales Price Approval Request", existing)
            )
        )

    if existing_status == "Approved":
        # Previously approved but then item rate was lowered again. Safer to
        # force a fresh approval rather than reuse the stale approval.
        pass

    # Rejected or fresh → create a new request
    request = _build_request(doc, violations)
    doc.custom_approval_request = request.name
    doc.custom_approval_status = "Pending Approval"
    frappe.db.set_value(
        doc.doctype,
        doc.name,
        {
            "custom_approval_status": "Pending Approval",
            "custom_approval_request": request.name,
            "custom_approval_decision_note": None,
            "custom_approval_approver": None,
        },
        update_modified=False,
    )

    # Persist the SPAR + source-doc flag BEFORE raising. `frappe.throw` will
    # roll back the outer transaction — without this commit the request we
    # just inserted disappears and the approver inbox stays empty forever.
    frappe.db.commit()

    frappe.throw(
        _("Price is below the minimum selling price on {0} of {1} line(s).").format(
            len(violations), len(doc.get("items") or [])
        )
        + _violation_table(violations, getattr(doc, "currency", None))
        + "<p>"
        + _("Approval request {0} raised.").format(
            frappe.get_desk_link("Sales Price Approval Request", request.name)
        )
        + "</p>",
        title=_("Approval Required"),
    )


def _violation_table(violations: list[dict[str, Any]], currency: str | None = None) -> str:
    """Name the offending items, with the shortfall on each.

    The message used to give a count and nothing else. On an order of twenty
    lines with one below floor, the salesperson had no way to tell WHICH one
    without opening the approval request — and multi-line requests are common:
    89 of the 408 raised on production carry two or more lines, one of them 46.

    Every figure here is already gathered by `_collect_violations`; it was
    simply never shown.
    """
    if not violations:
        return ""

    cur = frappe.utils.escape_html(currency or "")
    head = "".join(
        f"<th style='text-align:{align}; padding:4px 8px;'>{label}</th>"
        for label, align in (
            (_("Item"), "left"), (_("Qty"), "right"),
            (_("Your Rate"), "right"), (_("Minimum"), "right"), (_("Short By"), "right"),
        )
    )

    rows = []
    for v in violations:
        short = flt(v["cost_floor_rate"]) - flt(v["proposed_rate"])
        label = frappe.utils.escape_html(v["item_code"])
        name = frappe.utils.escape_html(v.get("item_name") or "")
        if name and name != v["item_code"]:
            label += f"<div style='font-size:0.85em; color:#6b7280;'>{name}</div>"
        rows.append(
            "<tr>"
            f"<td style='padding:4px 8px;'>{label}</td>"
            f"<td style='text-align:right; padding:4px 8px;'>{flt(v.get('qty')):g}</td>"
            f"<td style='text-align:right; padding:4px 8px;'>{fmt_money(v['proposed_rate'], currency=cur)}</td>"
            f"<td style='text-align:right; padding:4px 8px;'>{fmt_money(v['cost_floor_rate'], currency=cur)}</td>"
            f"<td style='text-align:right; padding:4px 8px; color:#b82a20; font-weight:600;'>"
            f"{fmt_money(short, currency=cur)}</td>"
            "</tr>"
        )

    return (
        "<table class='table table-bordered table-sm' style='margin-top:10px;'>"
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def _collect_violations(doc, cost_floor_list: str) -> list[dict[str, Any]]:
    currency = getattr(doc, "currency", None) or frappe.db.get_default("currency")
    violations: list[dict[str, Any]] = []
    for row in doc.get("items") or []:
        floor_rate = _resolve_cost_floor_rate(row.item_code, cost_floor_list, currency)
        if not floor_rate:
            continue
        proposed = float(row.rate or 0)
        if proposed >= float(floor_rate):
            continue
        violations.append(
            {
                "item_code": row.item_code,
                "item_name": row.item_name,
                "uom": getattr(row, "uom", None) or getattr(row, "stock_uom", None),
                "qty": float(row.qty or 0),
                "proposed_rate": proposed,
                "cost_floor_rate": float(floor_rate),
                "valuation_rate": _valuation_rate(row.item_code),
                "last_purchase_rate": _last_purchase_rate(row.item_code),
            }
        )
    return violations


def _resolve_cost_floor_rate(item_code: str, price_list: str, currency: str | None) -> float | None:
    filters: dict[str, Any] = {"item_code": item_code, "price_list": price_list}
    if currency:
        filters["currency"] = currency
    rate = frappe.db.get_value("Item Price", filters, "price_list_rate")
    if rate is None and currency:
        rate = frappe.db.get_value(
            "Item Price",
            {"item_code": item_code, "price_list": price_list},
            "price_list_rate",
        )
    return float(rate) if rate else None


def _valuation_rate(item_code: str) -> float:
    rate = frappe.db.get_value("Item", item_code, "valuation_rate")
    return float(rate or 0)


def _last_purchase_rate(item_code: str) -> float:
    rate = frappe.db.get_value("Item", item_code, "last_purchase_rate")
    return float(rate or 0)


def _build_request(doc, violations: list[dict[str, Any]]):
    req = frappe.new_doc("Sales Price Approval Request")
    req.status = "Pending"
    req.source_doctype = doc.doctype
    req.source_name = doc.name
    req.customer = getattr(doc, "customer", None) or getattr(doc, "party_name", None)
    req.currency = getattr(doc, "currency", None)
    for v in violations:
        req.append("lines", v)
    req.insert(ignore_permissions=True)
    return req


def release_request_on_trash(doc, method: str | None = None) -> None:
    """`on_trash` hook. Clear the approval request so the draft can be deleted.

    The request points back at its source through `source_name`, a Dynamic
    Link, so Frappe's link guard refuses to delete the source document while
    the request exists — and nothing ever cleaned it up. Sixteen draft Sales
    Invoices were stuck on production because of it, with no way forward
    except deleting the request by hand first.

    Frappe runs `on_trash` BEFORE `check_if_doc_is_linked`
    (`frappe/model/delete_doc.py`, lines 126 and 133), so removing the request
    here clears the link in time.

    An APPROVED request is not removed. Someone made a pricing decision and it
    is the audit record of that decision; deleting the invoice under it would
    destroy the evidence silently. Those are blocked with an explanation.
    Pending and Rejected requests carry no decision worth keeping and go
    quietly.
    """
    requests = frappe.get_all(
        "Sales Price Approval Request",
        filters={"source_doctype": doc.doctype, "source_name": doc.name},
        fields=["name", "status"],
    )
    if not requests:
        return

    approved = [r.name for r in requests if r.status == "Approved"]
    if approved:
        frappe.throw(
            _(
                "This {0} carries an approved price approval ({1}), which records who "
                "authorised the below-cost price. Cancel or reject that request first "
                "if the document really has to go."
            ).format(
                _(doc.doctype),
                ", ".join(
                    frappe.get_desk_link("Sales Price Approval Request", n) for n in approved
                ),
            ),
            title=_("Approved Price Approval Exists"),
        )

    for r in requests:
        frappe.delete_doc(
            "Sales Price Approval Request",
            r.name,
            ignore_permissions=True,
            delete_permanently=True,
        )


def raise_request_for_saved_draft(doc, method: str | None = None) -> None:
    """`after_insert` hook — finish the work `check_cost_floor` deferred.

    Only fires for a document the gate just downgraded to a draft. The row
    exists by now, so the request's Dynamic Link resolves and the approver
    gets something they can actually open.
    """
    violations = (doc.flags or {}).get("fateh_pending_violations")
    if not violations:
        return
    doc.flags.fateh_pending_violations = None

    request = _build_request(doc, violations)
    frappe.db.set_value(
        doc.doctype,
        doc.name,
        {
            "custom_approval_status": "Pending Approval",
            "custom_approval_request": request.name,
            "custom_approval_decision_note": None,
            "custom_approval_approver": None,
        },
        update_modified=False,
    )
    doc.custom_approval_status = "Pending Approval"
    doc.custom_approval_request = request.name

    frappe.msgprint(
        _("Price is below the minimum selling price on {0} line(s). "
          "Saved as a draft and sent for approval: {1}. "
          "Submit it once the request is approved.").format(
            len(violations),
            frappe.get_desk_link("Sales Price Approval Request", request.name),
        ),
        title=_("Sent for Approval"),
        indicator="orange",
    )
