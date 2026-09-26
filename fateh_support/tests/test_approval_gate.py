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
        customer: str | None = None,
    ):
        self.doctype = doctype
        self.name = name
        self.items = items
        # Must be a real Customer when a request gets built — the request's
        # `customer` is a Link and link validation runs on insert.
        self.customer = customer
        self.currency = "USD"
        self.selling_price_list = selling_price_list
        self.custom_approval_status = None
        self.custom_approval_request = None
        self.docstatus = 0
        self._action = "save"
        self.flags = frappe._dict()

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
            "Quotation",
            self.ctx["quotation"],
            [_FakeItem(self.ctx["item"], rate=50.0)],
            customer=self.ctx["customer"],
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
        doc.docstatus = 1
        doc._action = "submit"
        check_cost_floor(doc)
        # Not exempt, so the gate acts: this document has no DB row, so it is
        # deferred to a draft rather than allowed through.
        self.assertEqual(doc.docstatus, 0)
        self.assertTrue(doc.flags.get("fateh_pending_violations"))

    def test_unsaved_document_is_deferred_not_discarded(self) -> None:
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
        # The stand-in has no DB row, so the gate defers rather than throwing:
        # it downgrades to a draft and leaves the request to after_insert.
        doc.docstatus = 1
        doc._action = "submit"
        check_cost_floor(doc)

        self.assertEqual(doc.docstatus, 0)
        self.assertEqual(doc._action, "save")
        self.assertTrue(doc.flags.get("fateh_pending_violations"))
        self.assertIsNone(doc.custom_approval_request)
        self.assertEqual(frappe.db.count("Sales Price Approval Request"), before)


class TestApprovalGateEndToEnd(FrappeTestCase):
    """Real documents, real inserts — no stubbed `frappe.db.set_value`.

    TestApprovalGate stubs set_value so its stand-in documents can run, which
    silently hides whether the gate's write-back actually lands. These go
    through Frappe's genuine insert path instead.
    """

    def setUp(self) -> None:
        self.ctx = reset_test_sandbox()

    def _new_quotation(self, rate: float):
        return frappe.get_doc({
            "doctype": "Quotation",
            "quotation_to": "Customer",
            "party_name": self.ctx["customer"],
            "company": self.ctx["company"],
            "currency": "USD",
            "conversion_rate": 1,
            "selling_price_list": "Standard Selling",
            "transaction_date": frappe.utils.nowdate(),
            "items": [{
                "item_code": self.ctx["item"],
                "qty": 1,
                "rate": rate,
                "uom": "Nos",
                "conversion_factor": 1,
            }],
        })
    def test_new_document_submitted_directly_lands_as_a_draft(self) -> None:
        """The real RMAX flow: save+submit in one call, from a blank form.

        There is no draft step in production — `frm.save("Submit")` is called
        on a brand-new document. The gate must not discard that work: it lands
        the document as a draft and raises the request against it.
        """
        before = frappe.db.count("Sales Price Approval Request")

        quotation = self._new_quotation(50.0)  # below the 100.0 floor
        quotation.docstatus = 1          # exactly what save("Submit") does
        quotation.insert(ignore_permissions=True)

        self.assertEqual(quotation.docstatus, 0, "must be held back as a draft")
        self.assertTrue(frappe.db.exists("Quotation", quotation.name))
        self.assertEqual(
            frappe.db.get_value("Quotation", quotation.name, "docstatus"), 0
        )
        self.assertEqual(frappe.db.count("Sales Price Approval Request"), before + 1)

        req_name = frappe.db.get_value(
            "Quotation", quotation.name, "custom_approval_request"
        )
        self.assertTrue(req_name)
        req = frappe.get_doc("Sales Price Approval Request", req_name)
        self.assertEqual(req.status, "Pending")
        self.assertEqual(req.source_name, quotation.name)
        self.assertEqual(
            frappe.db.get_value("Quotation", quotation.name, "custom_approval_status"),
            "Pending Approval",
        )

    def test_new_document_above_floor_still_submits(self) -> None:
        """Regression guard: the gate must not hold back a compliant document."""
        quotation = self._new_quotation(150.0)  # above the floor
        quotation.docstatus = 1
        quotation.insert(ignore_permissions=True)
        self.assertEqual(quotation.docstatus, 1, "compliant document must submit")



class TestDraftDeletionWithApprovalRequest(FrappeTestCase):
    """A draft holding a price approval must be deletable.

    The request Dynamic-Links back to its source, so Frappe's link guard
    refused to delete the source and nothing cleaned the request up. Sixteen
    draft Sales Invoices were stuck on production with no way forward.
    """

    def setUp(self) -> None:
        self.ctx = reset_test_sandbox()

    def _draft_below_floor(self):
        quotation = frappe.get_doc({
            "doctype": "Quotation",
            "quotation_to": "Customer",
            "party_name": self.ctx["customer"],
            "company": self.ctx["company"],
            "currency": "USD",
            "conversion_rate": 1,
            "selling_price_list": "Standard Selling",
            "transaction_date": frappe.utils.nowdate(),
            "items": [{
                "item_code": self.ctx["item"], "qty": 1, "rate": 50.0,
                "uom": "Nos", "conversion_factor": 1,
            }],
        })
        quotation.docstatus = 1          # save("Submit") from a blank form
        quotation.insert(ignore_permissions=True)
        req = frappe.db.get_value("Quotation", quotation.name, "custom_approval_request")
        self.assertTrue(req, "fixture must have raised a request")
        return quotation, req

    def test_pending_request_is_removed_and_the_draft_deletes(self) -> None:
        quotation, req = self._draft_below_floor()

        frappe.delete_doc("Quotation", quotation.name, ignore_permissions=True)

        self.assertFalse(frappe.db.exists("Quotation", quotation.name))
        self.assertFalse(
            frappe.db.exists("Sales Price Approval Request", req),
            "a pending request carries no decision and must go with the draft",
        )

    def test_approved_request_blocks_the_deletion(self) -> None:
        """An approved request records who authorised a below-cost price."""
        quotation, req = self._draft_below_floor()
        frappe.db.set_value("Sales Price Approval Request", req, "status", "Approved")

        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc("Quotation", quotation.name, ignore_permissions=True)

        self.assertTrue(frappe.db.exists("Quotation", quotation.name))
        self.assertTrue(frappe.db.exists("Sales Price Approval Request", req))

    def test_rejected_request_does_not_block(self) -> None:
        quotation, req = self._draft_below_floor()
        frappe.db.set_value("Sales Price Approval Request", req, "status", "Rejected")

        frappe.delete_doc("Quotation", quotation.name, ignore_permissions=True)

        self.assertFalse(frappe.db.exists("Quotation", quotation.name))
        self.assertFalse(frappe.db.exists("Sales Price Approval Request", req))

    def test_document_without_a_request_deletes_normally(self) -> None:
        quotation = frappe.get_doc({
            "doctype": "Quotation",
            "quotation_to": "Customer",
            "party_name": self.ctx["customer"],
            "company": self.ctx["company"],
            "currency": "USD",
            "conversion_rate": 1,
            "selling_price_list": "Standard Selling",
            "transaction_date": frappe.utils.nowdate(),
            "items": [{
                "item_code": self.ctx["item"], "qty": 1, "rate": 150.0,
                "uom": "Nos", "conversion_factor": 1,
            }],
        })
        quotation.insert(ignore_permissions=True)
        frappe.delete_doc("Quotation", quotation.name, ignore_permissions=True)
        self.assertFalse(frappe.db.exists("Quotation", quotation.name))


class TestViolationTable(FrappeTestCase):
    """The message must name the offending items, not just count them."""

    def test_table_names_each_item_and_its_shortfall(self) -> None:
        from fateh_support.approvals.gate import _violation_table

        html = _violation_table([
            {"item_code": "WIDGET-1", "item_name": "Blue Widget", "qty": 3,
             "proposed_rate": 80.0, "cost_floor_rate": 100.0},
        ], "SAR")

        self.assertIn("WIDGET-1", html)
        self.assertIn("Blue Widget", html)
        self.assertIn("20", html, "the shortfall of 20 must be shown")

    def test_empty_violations_render_nothing(self) -> None:
        from fateh_support.approvals.gate import _violation_table

        self.assertEqual(_violation_table([], "SAR"), "")

    def test_item_name_is_escaped(self) -> None:
        from fateh_support.approvals.gate import _violation_table

        html = _violation_table([
            {"item_code": "X", "item_name": "<script>alert(1)</script>", "qty": 1,
             "proposed_rate": 1.0, "cost_floor_rate": 2.0},
        ], "SAR")

        self.assertNotIn("<script>", html)


class TestRequestLink(FrappeTestCase):
    """The link must name the REQUEST, not the document it was raised from."""

    def test_link_is_labelled_with_the_request_id(self) -> None:
        from fateh_support.approvals.gate import _request_link

        html = _request_link("SPAR-2026-00116")

        self.assertIn("SPAR-2026-00116", html)
        self.assertIn("/app/sales-price-approval-request/SPAR-2026-00116", html)
        self.assertNotIn("INV-", html)

    def test_name_is_escaped(self) -> None:
        from fateh_support.approvals.gate import _request_link

        self.assertNotIn("<script>", _request_link("<script>alert(1)</script>"))
