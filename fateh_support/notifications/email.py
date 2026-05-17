"""Email fallback for approval events. Gated by Fateh Support Settings."""

from __future__ import annotations

import frappe
from frappe.utils import cint, get_url


def _settings():
    try:
        return frappe.get_cached_doc("Fateh Support Settings")
    except Exception:
        return None


def _email_enabled(settings) -> bool:
    if not settings:
        return False
    return bool(cint(settings.get("enable_email_notifications")))


def _extra_recipients(settings) -> list[str]:
    raw = (settings.get("email_recipients_override") or "") if settings else ""
    return [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]


def _safe_send(recipients, subject, message):
    """Queue email; swallow send errors so they never block submit/decide."""
    if not recipients:
        return
    try:
        frappe.sendmail(
            recipients=list(recipients),
            subject=subject,
            message=message,
            now=False,
            delayed=True,
        )
    except Exception as exc:
        frappe.log_error(
            title="fateh_support email send failed",
            message=f"recipients={recipients!r} subject={subject!r} err={exc!r}",
        )


def notify_approvers(doc) -> None:
    settings = _settings()
    if not _email_enabled(settings):
        return
    if not cint(settings.get("email_on_request_created")):
        return

    approvers = frappe.db.sql_list(
        """
        SELECT DISTINCT u.email
        FROM `tabHas Role` hr
        JOIN `tabUser` u ON u.name = hr.parent
        WHERE hr.role IN ('Price Approver', 'System Manager')
          AND u.enabled = 1
          AND u.user_type != 'Website User'
          AND u.email IS NOT NULL
          AND u.email != ''
        """
    )
    recipients = list(dict.fromkeys(list(approvers) + _extra_recipients(settings)))
    if not recipients:
        return

    subject = frappe._("Below-cost approval request — {0}").format(doc.source_name or "")
    _safe_send(recipients, subject, _approver_body(doc))


def notify_requester(doc) -> None:
    settings = _settings()
    if not _email_enabled(settings):
        return
    if not cint(settings.get("email_on_request_decided")):
        return
    if not doc.requester:
        return

    email = frappe.db.get_value("User", doc.requester, "email")
    recipients = list(dict.fromkeys([e for e in [email] + _extra_recipients(settings) if e]))
    if not recipients:
        return

    subject = frappe._("Your below-cost request has been {0}").format(doc.status.lower())
    _safe_send(recipients, subject, _requester_body(doc))


def _approver_body(doc) -> str:
    requester = frappe.db.get_value("User", doc.requester, "full_name") or doc.requester
    url = f"{get_url()}/fateh/#/approvals/{doc.name}"
    return (
        f"<p>A new below-cost approval request is waiting.</p>"
        f"<ul>"
        f"<li><b>Requester:</b> {frappe.utils.escape_html(requester)}</li>"
        f"<li><b>Customer:</b> {frappe.utils.escape_html(doc.customer or '')}</li>"
        f"<li><b>Source:</b> {doc.source_doctype} {doc.source_name}</li>"
        f"<li><b>Variance:</b> {doc.variance_pct or 0:.2f}% ({doc.currency or ''} {doc.variance_amount or 0:.2f})</li>"
        f"</ul>"
        f"<p><a href='{url}'>Open in app</a></p>"
    )


def _requester_body(doc) -> str:
    url = f"{get_url()}/fateh/#/my-requests"
    note = (doc.decision_note or "").strip() or "(no note)"
    return (
        f"<p>Your below-cost request for {doc.source_doctype} {doc.source_name} has been "
        f"<b>{doc.status.lower()}</b>.</p>"
        f"<p>Note: {frappe.utils.escape_html(note)}</p>"
        f"<p><a href='{url}'>View in app</a></p>"
    )
