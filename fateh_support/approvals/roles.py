"""Who may decide which approval request.

Price requests go to Price Approvers, credit-limit requests to Credit
Approvers (the role a site makes its ERPNext Credit Controller). System
Managers may decide both. Every permission check and every notification
reads this module, so the two kinds never leak into each other's inbox.
"""

from __future__ import annotations

import frappe

PRICE = "Price"
CREDIT = "Credit Limit"

APPROVER_ROLES = {
	PRICE: ("Price Approver",),
	CREDIT: ("Credit Approver",),
}
ADMIN_ROLES = ("System Manager",)
VIEWER_ROLES = ("Fateh Viewer",)


def request_type_of(doc) -> str:
	return (doc.get("request_type") if doc else None) or PRICE


def approver_roles(request_type: str | None) -> set[str]:
	return set(APPROVER_ROLES.get(request_type or PRICE, ())) | set(ADMIN_ROLES)


def all_approver_roles() -> set[str]:
	roles = set(ADMIN_ROLES)
	for r in APPROVER_ROLES.values():
		roles |= set(r)
	return roles


def types_user_can_approve(user: str | None = None) -> list[str]:
	user = user or frappe.session.user
	if user == "Administrator":
		return list(APPROVER_ROLES)
	roles = set(frappe.get_roles(user))
	return [t for t in APPROVER_ROLES if roles & approver_roles(t)]


def can_approve(request_type: str | None, user: str | None = None) -> bool:
	return (request_type or PRICE) in types_user_can_approve(user)


def approver_users(request_type: str | None) -> list[str]:
	return frappe.db.sql_list(
		"""
		SELECT DISTINCT hr.parent
		FROM `tabHas Role` hr
		JOIN `tabUser` u ON u.name = hr.parent
		WHERE hr.role IN %(roles)s
		  AND u.enabled = 1
		  AND u.user_type != 'Website User'
		""",
		{"roles": tuple(approver_roles(request_type))},
	)


def approver_emails(request_type: str | None) -> list[str]:
	return frappe.db.sql_list(
		"""
		SELECT DISTINCT u.email
		FROM `tabHas Role` hr
		JOIN `tabUser` u ON u.name = hr.parent
		WHERE hr.role IN %(roles)s
		  AND u.enabled = 1
		  AND u.user_type != 'Website User'
		  AND IFNULL(u.email, '') != ''
		""",
		{"roles": tuple(approver_roles(request_type))},
	)
