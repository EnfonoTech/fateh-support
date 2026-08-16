"""Unit tests for the before_submit gate on Quotation."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from fateh_support.approvals.gate import check_cost_floor
from fateh_support.tests.setup_fixtures import configure_cost_floor, reset_test_sandbox


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

    def __init__(
        self,
        doctype: str,
        name: str,
        items: list[_FakeItem],
        selling_price_list: str | None = None,
    ):
        self.doctype = doctype
        self.name = name
        self.items = items
        self.customer = "__Test Customer"
        self.currency = "USD"
        self.selling_price_list = selling_price_list
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
        doc = _FakeDoc(
            "Quotation", self.ctx["quotation"], [_FakeItem(self.ctx["item"], rate=150.0)]
        )
        check_cost_floor(doc)  # must not raise
        self.assertIsNone(doc.custom_approval_request)

    def test_rate_below_floor_blocks_and_creates_request(self) -> None:
        # Must be a document that actually exists: `source_name` is a Dynamic
        # Link, and the gate refuses to build a request for an unsaved doc.
        doc = _FakeDoc(
            "Quotation", self.ctx["quotation"], [_FakeItem(self.ctx["item"], rate=50.0)]
        )
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

    def test_exempt_price_list_skips_the_gate(self) -> None:
        """Inter-company transfers are not customer pricing — never gate them."""
        configure_cost_floor(self.ctx["cost_floor"], exempt=["Fateh Inter Company"])
        doc = _FakeDoc(
            "Sales Invoice",
            "SINV-TEST-EXEMPT",
            [_FakeItem(self.ctx["item"], rate=1.0)],  # far below the floor
            selling_price_list="Fateh Inter Company",
        )
        check_cost_floor(doc)  # must not raise
        self.assertIsNone(doc.custom_approval_request)

    def test_exempt_match_ignores_case(self) -> None:
        configure_cost_floor(self.ctx["cost_floor"], exempt=["Fateh Inter Company"])
        doc = _FakeDoc(
            "Sales Invoice",
            "SINV-TEST-EXEMPT-CASE",
            [_FakeItem(self.ctx["item"], rate=1.0)],
            selling_price_list="fateh inter company",
        )
        check_cost_floor(doc)
        self.assertIsNone(doc.custom_approval_request)

    def test_exempting_clears_a_flag_raised_before(self) -> None:
        """A doc already stuck behind a request must not stay stuck."""
        configure_cost_floor(self.ctx["cost_floor"], exempt=["Fateh Inter Company"])
        doc = _FakeDoc(
            "Sales Invoice",
            "SINV-TEST-EXEMPT-STALE",
            [_FakeItem(self.ctx["item"], rate=1.0)],
            selling_price_list="Fateh Inter Company",
        )
        doc.custom_approval_status = "Pending Approval"
        doc.custom_approval_request = "SPAR-TEST-OLD"

        check_cost_floor(doc)

        self.assertEqual(doc.custom_approval_status, "")
        self.assertIsNone(doc.custom_approval_request)

    def test_non_exempt_price_list_still_blocks(self) -> None:
        configure_cost_floor(self.ctx["cost_floor"], exempt=["Fateh Inter Company"])
        doc = _FakeDoc(
            "Sales Invoice",
            "SINV-TEST-GATED",
            [_FakeItem(self.ctx["item"], rate=1.0)],
            selling_price_list="Standard Selling",
        )
        with self.assertRaises(frappe.ValidationError):
            check_cost_floor(doc)

    def test_unsaved_document_asks_for_a_draft(self) -> None:
        """Regression: submitting a never-saved doc used to die on link validation.

        Frappe's insert() runs before_submit BEFORE db_insert, so the source
        row does not exist when the gate fires. Building the request then
        failed on the Dynamic Link with "Could not find Source Name: <doc>".
        The gate must ask for a draft instead, and must NOT leave an approval
        request pointing at a document that will never exist.
        """
        before = frappe.db.count("Sales Price Approval Request")

        doc = _FakeDoc(
            "Sales Invoice",
            "SINV-DOES-NOT-EXIST-YET",
            [_FakeItem(self.ctx["item"], rate=50.0)],
        )
        with self.assertRaises(frappe.ValidationError) as caught:
            check_cost_floor(doc)

        message = str(caught.exception)
        self.assertIn("draft", message.lower())
        self.assertNotIn("Could not find", message)
        self.assertIsNone(doc.custom_approval_request)
        self.assertEqual(frappe.db.count("Sales Price Approval Request"), before)
