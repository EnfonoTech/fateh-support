"""Tests for the branding endpoint."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from fateh_support.api import branding as branding_api
from fateh_support.tests.setup_fixtures import reset_test_sandbox


class TestBrandingApi(FrappeTestCase):
    def setUp(self) -> None:
        self.ctx = reset_test_sandbox()

    def test_default_brand_name(self) -> None:
        payload = branding_api.get()
        self.assertTrue(payload.get("brand_name"))
        self.assertTrue(payload.get("brand_primary_color").startswith("#"))

    def test_brand_override_reflected(self) -> None:
        settings = frappe.get_single("Fateh Support Settings")
        settings.brand_name = "RMAX Trading"
        settings.brand_primary_color = "#ff0000"
        settings.flags.ignore_permissions = True
        settings.save(ignore_permissions=True)
        frappe.clear_document_cache("Fateh Support Settings", "Fateh Support Settings")
        payload = branding_api.get()
        self.assertEqual(payload["brand_name"], "RMAX Trading")
        self.assertEqual(payload["brand_primary_color"].lower(), "#ff0000")
