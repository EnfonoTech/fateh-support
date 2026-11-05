"""Socket.IO fanout helpers for approval events."""

from __future__ import annotations

from typing import Any

import frappe

EVENT_NAME = "fateh_approval_update"


def _payload(doc) -> dict[str, Any]:
    return {
        "name": doc.name,
        "status": doc.status,
        "request_type": doc.get("request_type") or "Price",
        "requester": doc.requester,
        "customer": doc.customer,
        "source_doctype": doc.source_doctype,
        "source_name": doc.source_name,
        "variance_pct": float(doc.variance_pct or 0),
        "variance_amount": float(doc.variance_amount or 0),
    }


def publish_approval_created(doc) -> None:
    payload = _payload(doc)
    for approver in _approver_users(doc):
        frappe.publish_realtime(event=EVENT_NAME, message=payload, user=approver)


def publish_approval_decided(doc) -> None:
    payload = _payload(doc)
    if doc.requester:
        frappe.publish_realtime(event=EVENT_NAME, message=payload, user=doc.requester)
    if doc.approver and doc.approver != doc.requester:
        frappe.publish_realtime(event=EVENT_NAME, message=payload, user=doc.approver)


def _approver_users(doc=None) -> list[str]:
    from fateh_support.approvals.roles import approver_users, request_type_of

    return approver_users(request_type_of(doc))
