"""Tests for items.search / stock / prices endpoints."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from fateh_support.api import items as items_api
from fateh_support.tests.setup_fixtures import reset_test_sandbox


class TestItemsApi(FrappeTestCase):
    def setUp(self) -> None:
        self.ctx = reset_test_sandbox()
        self._orig_user = frappe.session.user

    def tearDown(self) -> None:
        frappe.set_user(self._orig_user)

    def test_search_returns_matches(self) -> None:
        frappe.set_user(self.ctx["viewer"])
        rows = items_api.search(q="FATEH-TEST", limit=5)
        codes = {r["item_code"] for r in rows}
        self.assertIn(self.ctx["item"], codes)

    def test_prices_omits_cost_floor_for_viewers(self) -> None:
        frappe.set_user(self.ctx["viewer"])
        result = items_api.prices(item_code=self.ctx["item"])
        price_lists = {r["price_list"] for r in result["rows"]}
        self.assertNotIn(self.ctx["cost_floor"], price_lists)
        self.assertIn("Standard Selling", price_lists)
        self.assertFalse(result.get("is_approver"))

    def test_prices_shows_cost_floor_for_approvers(self) -> None:
        frappe.set_user(self.ctx["approver"])
        result = items_api.prices(item_code=self.ctx["item"])
        price_lists = {r["price_list"] for r in result["rows"]}
        self.assertIn(self.ctx["cost_floor"], price_lists)
        self.assertTrue(result.get("is_approver"))
        self.assertIn("valuation_rate", result)

    def test_non_viewer_is_blocked(self) -> None:
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            items_api.prices(item_code=self.ctx["item"])
