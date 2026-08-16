"""Web Push subscription management."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist(methods=["POST"])
def subscribe(subscription: str | dict[str, Any], type: str = "web") -> dict[str, Any]:
    """Save a Web Push / FCM / APNs subscription for the current user.

    `subscription` is either a JSON string or a dict with fields depending on
    channel:
      - web: `{endpoint, keys: {p256dh, auth}}`
      - fcm / apns: `{endpoint}` (endpoint = device token)
    """
    if isinstance(subscription, str):
        try:
            subscription = json.loads(subscription)
        except json.JSONDecodeError:
            frappe.throw(_("subscription must be a JSON object"))

    if not isinstance(subscription, dict):
        frappe.throw(_("subscription must be an object"))

    endpoint = subscription.get("endpoint")
    if not endpoint:
        frappe.throw(_("subscription.endpoint is required"))

    keys = subscription.get("keys") or {}
    user = frappe.session.user
    # `frappe.get_request_header` dereferences frappe.request, which raises
    # "object is not bound" when there is no HTTP request — a background job,
    # a bench console call, or a test. The user agent is a nicety; never let
    # it take the subscription down with it.
    user_agent = (frappe.get_request_header("User-Agent") or "") if frappe.request else ""

    existing = frappe.db.get_value(
        "Fateh Push Subscription",
        {"user": user, "endpoint": endpoint},
        "name",
    )
    if existing:
        doc = frappe.get_doc("Fateh Push Subscription", existing)
        doc.type = type
        doc.p256dh = keys.get("p256dh")
        doc.auth = keys.get("auth")
        doc.user_agent = user_agent
        doc.last_seen = now_datetime()
        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Fateh Push Subscription",
                "user": user,
                "type": type,
                "endpoint": endpoint,
                "p256dh": keys.get("p256dh"),
                "auth": keys.get("auth"),
                "user_agent": user_agent,
                "last_seen": now_datetime(),
            }
        )
        doc.insert(ignore_permissions=True)
    return {"ok": True, "name": doc.name}


@frappe.whitelist(methods=["POST"])
def unsubscribe(endpoint: str) -> dict[str, bool]:
    if not endpoint:
        frappe.throw(_("endpoint is required"))
    name = frappe.db.get_value(
        "Fateh Push Subscription",
        {"user": frappe.session.user, "endpoint": endpoint},
        "name",
    )
    if name:
        frappe.delete_doc("Fateh Push Subscription", name, ignore_permissions=True)
    return {"ok": True}
