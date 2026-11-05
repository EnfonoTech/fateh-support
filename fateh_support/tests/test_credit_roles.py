"""Price and credit requests reach only their own approvers."""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from fateh_support.approvals import roles
from fateh_support.approvals.permissions import has_permission


class TestCreditRoles(FrappeTestCase):
	def test_role_per_type(self):
		self.assertIn("Price Approver", roles.approver_roles(roles.PRICE))
		self.assertIn("Credit Approver", roles.approver_roles(roles.CREDIT))
		self.assertNotIn("Price Approver", roles.approver_roles(roles.CREDIT))
		self.assertIn("System Manager", roles.approver_roles(roles.CREDIT))
		self.assertEqual(roles.request_type_of(frappe._dict()), roles.PRICE)

	@patch("frappe.get_roles", return_value=["Credit Approver"])
	def test_credit_approver_sees_credit_not_price(self, _roles):
		self.assertEqual(roles.types_user_can_approve("ca@example.com"), [roles.CREDIT])
		credit = frappe._dict(request_type=roles.CREDIT, requester="someone@example.com")
		price = frappe._dict(request_type=roles.PRICE, requester="someone@example.com")
		self.assertTrue(has_permission(credit, "read", "ca@example.com"))
		self.assertFalse(has_permission(price, "read", "ca@example.com"))

	@patch("frappe.get_roles", return_value=["Fateh Viewer"])
	def test_requester_sees_own_request(self, _roles):
		mine = frappe._dict(request_type=roles.CREDIT, requester="me@example.com")
		self.assertTrue(has_permission(mine, "read", "me@example.com"))
		self.assertFalse(has_permission(mine, "read", "other@example.com"))
