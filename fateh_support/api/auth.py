"""Authentication endpoints for the Fateh Trading PWA and Capacitor shell."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.auth import LoginManager
from frappe.utils.password import get_decrypted_password

try:
    import bcrypt  # type: ignore
except ImportError:  # pragma: no cover
    bcrypt = None


def _csrf_token() -> str:
    """Current session's CSRF token, or "" if it cannot be resolved.

    The SPA needs this after every login: `post_login` rotates the session,
    so the token baked into the `/fateh` page at render time (a Guest token)
    is dead and every later POST would fail CSRF with HTTP 400.
    """
    try:
        return frappe.sessions.get_csrf_token()
    except Exception:
        return ""


def _profile_payload(user: str) -> dict[str, Any]:
    user_doc = frappe.get_doc("User", user)
    roles = set(frappe.get_roles(user))
    from fateh_support.api import branding as branding_api

    return {
        "user": user,
        "csrf_token": _csrf_token(),
        "full_name": user_doc.full_name,
        "email": user_doc.email,
        "language": user_doc.language or "en",
        "roles": sorted(roles),
        "is_approver": "Price Approver" in roles or "System Manager" in roles,
        "is_viewer": "Fateh Viewer" in roles or "Price Approver" in roles or "System Manager" in roles,
        "branding": branding_api.get(),
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def login(usr: str, pwd: str) -> dict[str, Any]:
    """Cookie-based login for the web PWA.

    Mirrors `/api/method/login` but returns a profile payload so the SPA can
    bootstrap without a second round-trip.
    """
    if not usr or not pwd:
        frappe.throw(_("Email and password are required."), frappe.AuthenticationError)

    login_manager = LoginManager()
    login_manager.authenticate(user=usr, pwd=pwd)
    login_manager.post_login()

    return _profile_payload(frappe.session.user)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def csrf() -> dict[str, str]:
    """Hand the caller a fresh CSRF token for the *current* session.

    GET-only on purpose: an unsafe method would itself be CSRF-gated, so the
    one call that heals a stale token could never get through. Guest-allowed
    because a logged-out SPA still needs a valid token to POST to `login`.
    The token is bound to the caller's own session cookie and is useless
    without it, and `allow_cors` on this site is a localhost allow-list, so
    no third-party origin can read the response.
    """
    return {"csrf_token": _csrf_token(), "user": frappe.session.user}


@frappe.whitelist()
def ping() -> dict[str, Any]:
    return {
        "user": frappe.session.user,
        "ts": str(frappe.utils.now_datetime()),
    }


@frappe.whitelist()
def me() -> dict[str, Any]:
    if (frappe.session.user or "Guest") == "Guest":
        frappe.throw(_("Not logged in"), frappe.AuthenticationError)
    return _profile_payload(frappe.session.user)


@frappe.whitelist(methods=["POST"])
def logout() -> dict[str, bool]:
    frappe.local.login_manager.logout()
    return {"ok": True}


@frappe.whitelist(allow_guest=True, methods=["POST"])
def pin_login(email: str, pin: str) -> dict[str, Any]:
    """Token-based login for the Capacitor native shell (v1.1).

    Looks up the user, verifies the bcrypt-hashed PIN stored on the User doc
    (custom field `fateh_pin_hash`), and returns an API key + secret. Reuses
    the existing `api_secret` on re-login so previously-issued tokens keep
    working.
    """
    if not email or not pin:
        frappe.throw(_("Email and PIN required"))
    if not bcrypt:
        frappe.throw(_("bcrypt is not installed on this server."))

    user_name = frappe.db.get_value("User", {"email": email}, "name") or frappe.db.get_value(
        "User", {"name": email}, "name"
    )
    if not user_name:
        frappe.throw(_("Invalid credentials"), frappe.AuthenticationError)

    if not frappe.db.has_column("User", "fateh_pin_hash"):
        frappe.throw(
            _("PIN login is not configured on this site. Use email + password instead."),
            frappe.AuthenticationError,
        )
    pin_hash = frappe.db.get_value("User", user_name, "fateh_pin_hash")
    if not pin_hash:
        frappe.throw(_("No PIN configured. Please set one up from the web app."))

    if not bcrypt.checkpw(str(pin).encode("utf-8"), pin_hash.encode("utf-8")):
        frappe.throw(_("Invalid credentials"), frappe.AuthenticationError)

    user_doc = frappe.get_doc("User", user_name)
    roles = set(frappe.get_roles(user_name))
    if not (roles & {"Fateh Viewer", "Price Approver", "System Manager"}):
        frappe.throw(_("Not authorised for this app"), frappe.PermissionError)

    existing_secret = None
    if user_doc.api_key:
        try:
            existing_secret = get_decrypted_password(
                "User", user_name, "api_secret", raise_exception=False
            )
        except Exception:
            existing_secret = None

    if existing_secret:
        api_secret = existing_secret
    else:
        api_secret = frappe.generate_hash(length=24)
        user_doc.api_key = user_doc.api_key or frappe.generate_hash(length=24)
        user_doc.api_secret = api_secret
        user_doc.flags.ignore_permissions = True
        user_doc.save(ignore_permissions=True)
        frappe.db.commit()

    return {
        "user": user_name,
        "api_key": user_doc.api_key,
        "api_secret": api_secret,
        "profile": _profile_payload(user_name),
    }
