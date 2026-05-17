"""Socket.IO fanout helpers for approval events."""

from __future__ import annotations

from typing import Any

import frappe

EVENT_NAME = "fateh_approval_update"


def _payload(doc) -> dict[str, Any]:
    return {
        "name": doc.name,
        "status": doc.status,
        "requester": doc.requester,
        "customer": doc.customer,
        "source_doctype": doc.source_doctype,
        "source_name": doc.source_name,
        "variance_pct": float(doc.variance_pct or 0),
        "variance_amount": float(doc.variance_amount or 0),
    }


def publish_approval_created(doc) -> None:
    payload = _payload(doc)
    for approver in _approver_users():
        frappe.publish_realtime(event=EVENT_NAME, message=payload, user=approver)


def publish_approval_decided(doc) -> None:
    payload = _payload(doc)
    if doc.requester:
        frappe.publish_realtime(event=EVENT_NAME, message=payload, user=doc.requester)
    if doc.approver and doc.approver != doc.requester:
        frappe.publish_realtime(event=EVENT_NAME, message=payload, user=doc.approver)


def _approver_users() -> list[str]:
    return [
        u[0]
        for u in frappe.db.sql(
            """
            SELECT DISTINCT `tabHas Role`.parent
            FROM `tabHas Role`
            JOIN `tabUser` u ON u.name = `tabHas Role`.parent
            WHERE `tabHas Role`.role IN ('Price Approver', 'System Manager')
              AND u.enabled = 1
              AND u.user_type != 'Website User'
            """
        )
    ]
