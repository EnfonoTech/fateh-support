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

    def _set_hide_minimum(self, value: int) -> None:
        settings = frappe.get_single("Fateh Support Settings")
        settings.hide_minimum_price_from_non_approvers = value
        settings.flags.ignore_permissions = True
        settings.save(ignore_permissions=True)

    def test_minimum_price_visible_to_viewers_by_default(self) -> None:
        """Regression: configuring the floor list used to hide it from branch users.

        The minimum price is a selling tier, not cost — a salesperson has to
        see the floor they must not go under. It vanished from the app the
        moment `cost_floor_price_list` was first set, with no code change and
        no warning.
        """
        self._set_hide_minimum(0)
        frappe.set_user(self.ctx["viewer"])
        result = items_api.prices(item_code=self.ctx["item"])
        price_lists = {r["price_list"] for r in result["rows"]}
        self.assertIn(self.ctx["cost_floor"], price_lists)
        self.assertFalse(result.get("is_approver"))

    def test_minimum_price_hidden_when_the_setting_is_on(self) -> None:
        self._set_hide_minimum(1)
        try:
            frappe.set_user(self.ctx["viewer"])
            result = items_api.prices(item_code=self.ctx["item"])
            self.assertNotIn(self.ctx["cost_floor"], {r["price_list"] for r in result["rows"]})
        finally:
            frappe.set_user("Administrator")
            self._set_hide_minimum(0)

    def test_approver_always_sees_the_minimum_price(self) -> None:
        self._set_hide_minimum(1)
        try:
            frappe.set_user(self.ctx["approver"])
            result = items_api.prices(item_code=self.ctx["item"])
            self.assertIn(self.ctx["cost_floor"], {r["price_list"] for r in result["rows"]})
        finally:
            frappe.set_user("Administrator")
            self._set_hide_minimum(0)
