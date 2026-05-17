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


def check_cost_floor(doc, method: str | None = None) -> None:
    """`before_submit` hook. May `frappe.throw()` to block submit."""
    if getattr(doc, "custom_approval_status", None) == "Approved":
        return

    settings = frappe.get_cached_doc("Fateh Support Settings")
    cost_floor_list = (settings.get("cost_floor_price_list") or "").strip()
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
        # Rates now above floor. If the source doc still carries a stale
        # Pending Approval / Rejected flag, scrub it so submit can proceed
        # cleanly and the desk view no longer shows a red banner.
        if getattr(doc, "custom_approval_status", None) in ("Pending Approval", "Rejected"):
            doc.custom_approval_status = ""
            doc.custom_approval_request = None
            frappe.db.set_value(
                doc.doctype,
                doc.name,
                {"custom_approval_status": "", "custom_approval_request": None},
                update_modified=False,
            )
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
        _("Price is below cost floor on {0} line(s). Approval request {1} raised.").format(
            len(violations),
            frappe.get_desk_link("Sales Price Approval Request", request.name),
        )
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
