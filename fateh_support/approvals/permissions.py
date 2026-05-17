"""Row-level and field-level permission helpers for approval requests."""

from __future__ import annotations

import frappe


def get_permission_query_conditions(user: str | None = None) -> str:
    """Restrict list queries so viewers see only their own requests.

    Approvers and System Managers see everything.
    """
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    user_roles = set(frappe.get_roles(user))
    if {"Price Approver", "System Manager"} & user_roles:
        return ""
    safe_user = frappe.db.escape(user)
    return f"(`tabSales Price Approval Request`.requester = {safe_user})"


def has_permission(doc, ptype: str, user: str | None = None) -> bool:
    """Single-document permission check mirroring the list query."""
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    user_roles = set(frappe.get_roles(user))
    if {"Price Approver", "System Manager"} & user_roles:
        return True
    return doc.requester == user
