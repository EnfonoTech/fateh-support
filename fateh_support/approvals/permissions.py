"""Row-level and field-level permission helpers for approval requests."""

from __future__ import annotations

import frappe

from fateh_support.approvals.roles import request_type_of, types_user_can_approve


def get_permission_query_conditions(user: str | None = None) -> str:
	"""Requesters see their own requests; approvers see the kinds they decide.

	Price Approvers see price requests, Credit Approvers credit requests,
	System Managers both.
	"""
	user = user or frappe.session.user
	if user == "Administrator":
		return ""
	safe_user = frappe.db.escape(user)
	own = f"`tabSales Price Approval Request`.requester = {safe_user}"
	types = types_user_can_approve(user)
	if not types:
		return f"({own})"
	type_list = ", ".join(frappe.db.escape(t) for t in types)
	return (
		f"({own} OR IFNULL(`tabSales Price Approval Request`.request_type, 'Price') IN ({type_list}))"
	)


def has_permission(doc, ptype: str, user: str | None = None) -> bool:
	"""Single-document permission check mirroring the list query."""
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	if request_type_of(doc) in types_user_can_approve(user):
		return True
	return doc.requester == user
