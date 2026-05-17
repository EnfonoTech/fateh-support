"""Unit tests for the before_submit gate on Quotation."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from fateh_support.approvals.gate import check_cost_floor
from fateh_support.tests.setup_fixtures import reset_test_sandbox


class _FakeItem:
    def __init__(self, item_code: str, rate: float, qty: float = 1.0, uom: str = "Nos"):
        self.item_code = item_code
        self.item_name = item_code
        self.rate = rate
        self.qty = qty
        self.uom = uom
        self.stock_uom = uom


class _FakeDoc:
    """Enough of a Quotation/SO surface for the gate to run without full DB writes."""

    def __init__(self, doctype: str, name: str, items: list[_FakeItem]):
        self.doctype = doctype
        self.name = name
        self.items = items
        self.customer = "__Test Customer"
        self.currency = "USD"
        self.custom_approval_status = None
        self.custom_approval_request = None

    def get(self, key, default=None):
        return getattr(self, key, default)


class TestApprovalGate(FrappeTestCase):
    def setUp(self) -> None:
        self.ctx = reset_test_sandbox()
        # Stub frappe.db.set_value for the doc mutation path so the gate can run
        # without a real Quotation record.
        self._orig_set_value = frappe.db.set_value

        def _set_value(doctype, name, fieldname, value=None, *args, **kwargs):
            return None

        frappe.db.set_value = _set_value  # type: ignore[assignment]

    def tearDown(self) -> None:
        frappe.db.set_value = self._orig_set_value  # type: ignore[assignment]

    def test_rate_above_floor_passes(self) -> None:
        doc = _FakeDoc("Quotation", "QUO-TEST-1", [_FakeItem(self.ctx["item"], rate=150.0)])
        check_cost_floor(doc)  # must not raise
        self.assertIsNone(doc.custom_approval_request)

    def test_rate_below_floor_blocks_and_creates_request(self) -> None:
        doc = _FakeDoc("Quotation", "QUO-TEST-2", [_FakeItem(self.ctx["item"], rate=50.0)])
        with self.assertRaises(frappe.ValidationError):
            check_cost_floor(doc)
        self.assertIsNotNone(doc.custom_approval_request)
        req = frappe.get_doc("Sales Price Approval Request", doc.custom_approval_request)
        self.assertEqual(req.status, "Pending")
        self.assertEqual(len(req.lines), 1)
        self.assertAlmostEqual(req.lines[0].proposed_rate, 50.0)
        self.assertAlmostEqual(req.lines[0].cost_floor_rate, 100.0)

    def test_approved_status_bypasses_gate(self) -> None:
        doc = _FakeDoc("Quotation", "QUO-TEST-3", [_FakeItem(self.ctx["item"], rate=50.0)])
        doc.custom_approval_status = "Approved"
        check_cost_floor(doc)  # must not raise

    def test_missing_cost_floor_config_passes_silently(self) -> None:
        settings = frappe.get_single("Fateh Support Settings")
        settings.cost_floor_price_list = ""
        settings.flags.ignore_permissions = True
        settings.save(ignore_permissions=True)
        doc = _FakeDoc("Quotation", "QUO-TEST-4", [_FakeItem(self.ctx["item"], rate=10.0)])
        check_cost_floor(doc)  # must not raise
