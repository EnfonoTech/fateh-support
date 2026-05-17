"""Web Push fanout (VAPID) with dead-subscription cleanup."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, now_datetime

try:
    from pywebpush import WebPushException, webpush  # type: ignore
except ImportError:  # pragma: no cover
    webpush = None  # type: ignore[assignment]
    WebPushException = Exception  # type: ignore[misc,assignment]


def _settings() -> Any:
    return frappe.get_cached_doc("Fateh Support Settings")


def _vapid_claims(settings) -> dict[str, Any]:
    subject = settings.get("vapid_subject") or "mailto:hello@enfono.com"
    return {"sub": subject}


def _vapid_private_key(settings) -> str | None:
    return settings.get_password("vapid_private_key", raise_exception=False)


def _can_send(settings) -> bool:
    if not cint(settings.get("enable_push")):
        return False
    if webpush is None:
        return False
    if not settings.get("vapid_public_key"):
        return False
    if not _vapid_private_key(settings):
        return False
    return True


def fanout_to_approvers(doc) -> None:
    settings = _settings()
    if not _can_send(settings):
        return

    title = _(title_for_new_request(doc))
    body = _format_request_body(doc)
    payload = {
        "title": title,
        "body": body,
        "data": {"url": f"/fateh/#/approvals/{doc.name}", "request": doc.name},
        "tag": f"approval:{doc.name}",
    }

    approver_users = frappe.db.sql_list(
        """
        SELECT DISTINCT `tabHas Role`.parent
        FROM `tabHas Role`
        JOIN `tabUser` u ON u.name = `tabHas Role`.parent
        WHERE `tabHas Role`.role IN ('Price Approver', 'System Manager')
          AND u.enabled = 1
          AND u.user_type != 'Website User'
        """
    )
    if not approver_users:
        return
    _send_to_users(approver_users, payload, settings)


def notify_requester(doc) -> None:
    if not doc.requester:
        return
    settings = _settings()
    if not _can_send(settings):
        return

    title = _("Below-cost request {0}").format(doc.status.lower())
    body = _format_decision_body(doc)
    payload = {
        "title": title,
        "body": body,
        "data": {"url": f"/fateh/#/my-requests", "request": doc.name},
        "tag": f"approval-decision:{doc.name}",
    }
    _send_to_users([doc.requester], payload, settings)


def _send_to_users(users: list[str], payload: dict[str, Any], settings) -> None:
    subs = frappe.get_all(
        "Fateh Push Subscription",
        filters={"user": ["in", users], "type": "web"},
        fields=["name", "endpoint", "p256dh", "auth"],
    )
    if not subs:
        return

    vapid_private = _vapid_private_key(settings)
    vapid_claims = _vapid_claims(settings)
    body = json.dumps(payload)

    for sub in subs:
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
        }
        try:
            webpush(  # type: ignore[misc]
                subscription_info=subscription_info,
                data=body,
                vapid_private_key=vapid_private,
                vapid_claims=vapid_claims,
            )
            frappe.db.set_value("Fateh Push Subscription", sub.name, "last_seen", now_datetime())
        except WebPushException as exc:  # type: ignore[misc]
            code = getattr(exc.response, "status_code", 0) if getattr(exc, "response", None) else 0
            if code in (404, 410):
                frappe.delete_doc("Fateh Push Subscription", sub.name, ignore_permissions=True)
            else:
                frappe.log_error(message=str(exc), title="fateh_support push send failed")
        except Exception as exc:  # pragma: no cover
            frappe.log_error(message=str(exc), title="fateh_support push send failed")


def title_for_new_request(doc) -> str:
    try:
        pct = abs(float(doc.variance_pct or 0))
    except Exception:
        pct = 0.0
    return f"Below-cost request ({pct:.1f}%)"


def _format_request_body(doc) -> str:
    requester_name = (
        frappe.db.get_value("User", doc.requester, "full_name") or doc.requester or ""
    )
    customer = doc.customer or ""
    return f"{requester_name} — {customer} — {doc.source_doctype} {doc.source_name}"


def _format_decision_body(doc) -> str:
    note = doc.decision_note or ""
    base = f"{doc.source_doctype} {doc.source_name}"
    if note:
        return f"{base} — {note}"
    return base


def cleanup_dead_subscriptions() -> None:
    """Scheduled hourly — no-op placeholder; dead endpoints are deleted inline on 404/410."""
    return


# frappe.translate shim so this module stays import-safe in tests that stub frappe.
def _(value: str) -> str:  # pragma: no cover
    try:
        return frappe._(value)
    except Exception:
        return value
