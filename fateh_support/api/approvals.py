"""Approval Request API — list, detail, decide, and requester history."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, cstr, now_datetime


def _is_approver(user: str | None = None) -> bool:
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    return bool(roles & {"Price Approver", "System Manager"})


def _require_viewer() -> None:
    roles = set(frappe.get_roles(frappe.session.user))
    if roles.isdisjoint({"Fateh Viewer", "Price Approver", "System Manager"}):
        frappe.throw(_("Not authorised"), frappe.PermissionError)


def _require_approver() -> None:
    if not _is_approver():
        frappe.throw(_("Approver role required"), frappe.PermissionError)


@frappe.whitelist()
def list_requests(
    status: str = "Pending",
    mine: int | str = 0,
    limit: int = 20,
    offset: int = 0,
    search: str = "",
) -> dict[str, Any]:
    _require_viewer()
    mine_flag = cint(mine)
    limit = max(1, min(int(limit or 20), 100))
    offset = max(0, int(offset or 0))

    filters: dict[str, Any] = {}
    if status and status != "All":
        filters["status"] = status
    if mine_flag or not _is_approver():
        filters["requester"] = frappe.session.user
    if search:
        filters["source_name"] = ["like", f"%{search}%"]

    rows = frappe.get_all(
        "Sales Price Approval Request",
        filters=filters,
        fields=[
            "name",
            "status",
            "requester",
            "requested_at",
            "customer",
            "source_doctype",
            "source_name",
            "currency",
            "variance_amount",
            "variance_pct",
            "line_total_impact",
            "approver",
            "decided_at",
        ],
        order_by="requested_at desc, creation desc",
        limit=limit,
        start=offset,
    )
    for r in rows:
        r["requester_full_name"] = frappe.db.get_value("User", r["requester"], "full_name") or r["requester"]
        r["age_seconds"] = (now_datetime() - r["requested_at"]).total_seconds() if r.get("requested_at") else None
        lines = frappe.get_all(
            "Sales Price Approval Line",
            filters={"parent": r["name"]},
            fields=["item_code", "item_name", "qty", "proposed_rate", "cost_floor_rate", "variance_pct"],
            order_by="idx asc",
            limit=5,
        )
        r["line_preview"] = lines

    total = frappe.db.count("Sales Price Approval Request", filters=filters)
    return {"rows": rows, "total": total, "offset": offset, "limit": limit}


# Keep a shorter alias for the router rule.
@frappe.whitelist()
def list(  # noqa: A001 — match REST verbs
    status: str = "Pending",
    mine: int | str = 0,
    limit: int = 20,
    offset: int = 0,
    search: str = "",
) -> dict[str, Any]:
    return list_requests(status=status, mine=mine, limit=limit, offset=offset, search=search)


@frappe.whitelist()
def get(name: str) -> dict[str, Any]:
    _require_viewer()
    if not name:
        frappe.throw(_("name is required"))

    doc = frappe.get_doc("Sales Price Approval Request", name)
    if not (_is_approver() or doc.requester == frappe.session.user):
        frappe.throw(_("Not authorised for this request"), frappe.PermissionError)

    settings = frappe.get_cached_doc("Fateh Support Settings")
    show_cost = _is_approver() and cint(settings.get("show_valuation_to_approvers"))

    lines = []
    for line in doc.lines or []:
        item = {
            "item_code": line.item_code,
            "item_name": line.item_name,
            "item_name_ar": frappe.db.get_value("Item", line.item_code, "item_name_ar"),
            "uom": line.uom,
            "qty": float(line.qty or 0),
            "proposed_rate": float(line.proposed_rate or 0),
            "cost_floor_rate": float(line.cost_floor_rate or 0),
            "variance_amount": float(line.variance_amount or 0),
            "variance_pct": float(line.variance_pct or 0),
            "line_total": float(line.line_total or 0),
        }
        if show_cost:
            item["valuation_rate"] = float(line.valuation_rate or 0)
            item["last_purchase_rate"] = float(line.last_purchase_rate or 0)
        lines.append(item)

    source_link = _source_url(doc.source_doctype, doc.source_name)

    return {
        "name": doc.name,
        "status": doc.status,
        "requester": doc.requester,
        "requester_full_name": frappe.db.get_value("User", doc.requester, "full_name") or doc.requester,
        "requested_at": doc.requested_at,
        "customer": doc.customer,
        "customer_name": frappe.db.get_value("Customer", doc.customer, "customer_name") if doc.customer else None,
        "source_doctype": doc.source_doctype,
        "source_name": doc.source_name,
        "source_url": source_link,
        "currency": doc.currency,
        "total_proposed": float(doc.total_proposed or 0),
        "total_cost_floor": float(doc.total_cost_floor or 0),
        "variance_amount": float(doc.variance_amount or 0),
        "variance_pct": float(doc.variance_pct or 0),
        "line_total_impact": float(doc.line_total_impact or 0),
        "justification": doc.justification,
        "lines": lines,
        "approver": doc.approver,
        "approver_full_name": frappe.db.get_value("User", doc.approver, "full_name") if doc.approver else None,
        "decided_at": doc.decided_at,
        "decision_note": doc.decision_note,
        "can_decide": _is_approver() and doc.status == "Pending",
    }


def _source_url(source_dt: str | None, source_name: str | None) -> str | None:
    if not source_dt or not source_name:
        return None
    slug = source_dt.replace(" ", "-").lower()
    base = frappe.utils.get_url()
    return f"{base}/app/{slug}/{source_name}"


@frappe.whitelist(methods=["POST"])
def decide(name: str, action: str, note: str = "") -> dict[str, Any]:
    _require_approver()

    if action not in ("approve", "reject"):
        frappe.throw(_("action must be 'approve' or 'reject'"))

    if action == "reject" and not (note or "").strip():
        frappe.throw(_("A rejection note is required."))

    doc = frappe.get_doc("Sales Price Approval Request", name)
    if doc.status != "Pending":
        frappe.throw(_("This request has already been decided."))

    doc.status = "Approved" if action == "approve" else "Rejected"
    doc.approver = frappe.session.user
    doc.decided_at = now_datetime()
    doc.decision_note = (note or "").strip() or None
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)

    _apply_decision_to_source(doc)
    frappe.db.commit()

    return {"name": doc.name, "status": doc.status}


def _apply_decision_to_source(doc) -> None:
    """Flip the custom approval fields on the source Quotation / Sales Order."""
    if not (doc.source_doctype and doc.source_name):
        return
    updates = {
        "custom_approval_status": "Approved" if doc.status == "Approved" else "Rejected",
        "custom_approval_approver": doc.approver,
        "custom_approval_decision_note": doc.decision_note,
    }
    frappe.db.set_value(
        doc.source_doctype,
        doc.source_name,
        updates,
        update_modified=False,
    )


@frappe.whitelist(methods=["POST"])
def decide_bulk(names: str | list[str], action: str, note: str = "") -> dict[str, Any]:
    """Decide several requests in one round-trip (desk list-view bulk action).

    Each request is decided independently: one failure does not abandon the
    rest. Returns per-name outcomes so the caller can report partial success.
    """
    _require_approver()

    if isinstance(names, str):
        names = json.loads(names)
    # NB: `list` is shadowed by the REST alias defined above — never use the
    # bare builtin in this module.
    names = [cstr(n) for n in (names or []) if cstr(n)]
    if not names:
        frappe.throw(_("Select at least one request."))

    done: list[str] = []
    failed: list[dict[str, str]] = []
    for name in names:
        try:
            decide(name=name, action=action, note=note)
            done.append(name)
        except Exception as exc:
            frappe.db.rollback()
            failed.append({"name": name, "error": str(exc)})

    return {"done": done, "failed": failed}


@frappe.whitelist(methods=["POST"])
def set_justification(name: str, justification: str) -> dict[str, Any]:
    """Requester-side helper to attach a justification after the gate fires."""
    _require_viewer()
    doc = frappe.get_doc("Sales Price Approval Request", name)
    if doc.requester != frappe.session.user:
        frappe.throw(_("You can only attach a justification to your own request."), frappe.PermissionError)
    if doc.status != "Pending":
        frappe.throw(_("Request already decided."))
    doc.justification = (justification or "").strip() or None
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    return {"ok": True}


@frappe.whitelist()
def mine(limit: int = 20, offset: int = 0) -> dict[str, Any]:
    return list_requests(status="", mine=1, limit=limit, offset=offset)


@frappe.whitelist()
def pending_count() -> dict[str, int]:
    if not _is_approver():
        count = frappe.db.count(
            "Sales Price Approval Request",
            filters={"requester": frappe.session.user, "status": "Pending"},
        )
    else:
        count = frappe.db.count("Sales Price Approval Request", filters={"status": "Pending"})
    return {"count": int(count)}
