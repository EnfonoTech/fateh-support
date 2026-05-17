"""Tests for push subscription endpoints."""

from __future__ import annotations

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from fateh_support.api import push as push_api
from fateh_support.tests.setup_fixtures import reset_test_sandbox


class TestPushApi(FrappeTestCase):
    def setUp(self) -> None:
        self.ctx = reset_test_sandbox()
        self._orig_user = frappe.session.user
        frappe.set_user(self.ctx["approver"])

    def tearDown(self) -> None:
        frappe.set_user(self._orig_user)

    def test_subscribe_creates_record(self) -> None:
        sub = {
            "endpoint": "https://push.example.com/abc123",
            "keys": {"p256dh": "p256", "auth": "auth"},
        }
        result = push_api.subscribe(subscription=json.dumps(sub), type="web")
        self.assertTrue(result.get("ok"))
        exists = frappe.db.exists(
            "Fateh Push Subscription",
            {"user": self.ctx["approver"], "endpoint": sub["endpoint"]},
        )
        self.assertTrue(exists)

    def test_resubscribe_updates_existing(self) -> None:
        sub = {"endpoint": "https://push.example.com/reuse", "keys": {"p256dh": "a", "auth": "b"}}
        push_api.subscribe(subscription=json.dumps(sub), type="web")
        sub["keys"]["p256dh"] = "new"
        push_api.subscribe(subscription=json.dumps(sub), type="web")
        count = frappe.db.count(
            "Fateh Push Subscription",
            filters={"user": self.ctx["approver"], "endpoint": sub["endpoint"]},
        )
        self.assertEqual(count, 1)
        name = frappe.db.get_value(
            "Fateh Push Subscription",
            {"user": self.ctx["approver"], "endpoint": sub["endpoint"]},
            "p256dh",
        )
        self.assertEqual(name, "new")

    def test_unsubscribe_removes_record(self) -> None:
        sub = {"endpoint": "https://push.example.com/byebye", "keys": {"p256dh": "a", "auth": "b"}}
        push_api.subscribe(subscription=json.dumps(sub), type="web")
        push_api.unsubscribe(endpoint=sub["endpoint"])
        exists = frappe.db.exists(
            "Fateh Push Subscription",
            {"user": self.ctx["approver"], "endpoint": sub["endpoint"]},
        )
        self.assertFalse(exists)
