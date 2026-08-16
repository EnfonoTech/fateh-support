"""Tests for the auth endpoints — specifically CSRF token delivery.

The SPA cannot POST without the token for the session the server currently
sees. `login` rotates that session, so the token baked into the `/fateh`
page at render time is dead by the time the user acts. These tests pin the
two ways the client can get a live one.
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from fateh_support.api import auth as auth_api
from fateh_support.tests.setup_fixtures import reset_test_sandbox


class TestAuthApi(FrappeTestCase):
    def setUp(self) -> None:
        self.ctx = reset_test_sandbox()
        self._orig_user = frappe.session.user

    def tearDown(self) -> None:
        frappe.set_user(self._orig_user)

    def test_csrf_returns_session_token(self) -> None:
        frappe.set_user(self.ctx["approver"])
        payload = auth_api.csrf()
        self.assertTrue(payload["csrf_token"])
        self.assertEqual(payload["csrf_token"], frappe.sessions.get_csrf_token())

    def test_profile_carries_csrf_token(self) -> None:
        frappe.set_user(self.ctx["approver"])
        profile = auth_api.me()
        self.assertEqual(profile["csrf_token"], frappe.sessions.get_csrf_token())

    def test_csrf_is_get_only(self) -> None:
        """GET-only, or the CSRF gate would block the call that heals CSRF."""
        self.assertEqual(
            frappe.allowed_http_methods_for_whitelisted_func[auth_api.csrf],
            ["GET"],
        )
