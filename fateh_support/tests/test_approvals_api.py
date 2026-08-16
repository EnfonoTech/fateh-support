"""Tests for the approval-decide API."""

from __future__ import annotations

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from fateh_support.api import approvals as approvals_api
from fateh_support.tests.setup_fixtures import reset_test_sandbox


def _make_request(ctx) -> str:
    req = frappe.new_doc("Sales Price Approval Request")
    req.status = "Pending"
    req.source_doctype = "Quotation"
    req.source_name = ctx["quotation"]
    req.customer = ctx["customer"]
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

    def test_bulk_decide_approves_every_request(self) -> None:
        second = _make_request(self.ctx)
        frappe.set_user(self.ctx["approver"])
        result = approvals_api.decide_bulk(
            names=[self.name, second], action="approve", note="batch"
        )
        self.assertEqual(sorted(result["done"]), sorted([self.name, second]))
        self.assertEqual(result["failed"], [])
        for name in (self.name, second):
            self.assertEqual(
                frappe.db.get_value("Sales Price Approval Request", name, "status"), "Approved"
            )

    def test_bulk_decide_accepts_json_names(self) -> None:
        """The desk list view posts `names` as a JSON string, not a list."""
        frappe.set_user(self.ctx["approver"])
        result = approvals_api.decide_bulk(
            names=json.dumps([self.name]), action="approve", note=""
        )
        self.assertEqual(result["done"], [self.name])

    def test_bulk_decide_isolates_failures(self) -> None:
        already = _make_request(self.ctx)
        frappe.set_user(self.ctx["approver"])
        approvals_api.decide(name=already, action="approve", note="first")

        result = approvals_api.decide_bulk(
            names=[self.name, already], action="approve", note="batch"
        )
        self.assertEqual(result["done"], [self.name])
        self.assertEqual([f["name"] for f in result["failed"]], [already])

    def test_search_matches_source_name(self) -> None:
        """Approvers search by the quotation number read out to them."""
        frappe.set_user(self.ctx["approver"])
        quotation = self.ctx["quotation"]

        hit = approvals_api.list_requests(status="Pending", search=quotation)
        self.assertIn(self.name, [r["name"] for r in hit["rows"]])

        miss = approvals_api.list_requests(status="Pending", search="QUO-NOPE-9999")
        self.assertEqual(miss["rows"], [])
        self.assertEqual(miss["total"], 0)

    def test_mine_passes_search_through(self) -> None:
        frappe.set_user(self.ctx["requester"])
        hit = approvals_api.mine(search=self.ctx["quotation"])
        self.assertIn(self.name, [r["name"] for r in hit["rows"]])

        miss = approvals_api.mine(search="QUO-NOPE-9999")
        self.assertEqual(miss["rows"], [])

    def test_bulk_decide_requires_approver(self) -> None:
        frappe.set_user(self.ctx["requester"])
        with self.assertRaises(frappe.PermissionError):
            approvals_api.decide_bulk(names=[self.name], action="approve", note="")
