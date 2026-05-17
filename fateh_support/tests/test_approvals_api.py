"""Tests for the approval-decide API."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from fateh_support.api import approvals as approvals_api
from fateh_support.tests.setup_fixtures import reset_test_sandbox


def _make_request(ctx) -> str:
    req = frappe.new_doc("Sales Price Approval Request")
    req.status = "Pending"
    req.source_doctype = "Quotation"
    req.source_name = "QUO-TEST-X"
    req.customer = None
    req.currency = "USD"
    req.requester = ctx["requester"]
    req.append(
        "lines",
        {
            "item_code": ctx["item"],
            "qty": 1,
            "proposed_rate": 50,
            "cost_floor_rate": 100,
        },
    )
    req.insert(ignore_permissions=True)
    return req.name


class TestApprovalsApi(FrappeTestCase):
    def setUp(self) -> None:
        self.ctx = reset_test_sandbox()
        self.name = _make_request(self.ctx)
        self._orig_user = frappe.session.user

    def tearDown(self) -> None:
        frappe.set_user(self._orig_user)

    def test_non_approver_cannot_decide(self) -> None:
        frappe.set_user(self.ctx["requester"])
        with self.assertRaises(frappe.PermissionError):
            approvals_api.decide(name=self.name, action="approve", note="")

    def test_reject_requires_note(self) -> None:
        frappe.set_user(self.ctx["approver"])
        with self.assertRaises(frappe.ValidationError):
            approvals_api.decide(name=self.name, action="reject", note="")

    def test_approve_transitions_status(self) -> None:
        frappe.set_user(self.ctx["approver"])
        result = approvals_api.decide(name=self.name, action="approve", note="OK")
        self.assertEqual(result["status"], "Approved")
        refreshed = frappe.get_doc("Sales Price Approval Request", self.name)
        self.assertEqual(refreshed.status, "Approved")
        self.assertEqual(refreshed.approver, self.ctx["approver"])

    def test_cannot_decide_twice(self) -> None:
        frappe.set_user(self.ctx["approver"])
        approvals_api.decide(name=self.name, action="approve", note="OK")
        with self.assertRaises(frappe.ValidationError):
            approvals_api.decide(name=self.name, action="reject", note="changed mind")
