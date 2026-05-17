"""Branding settings endpoints."""

from __future__ import annotations

from typing import Any

import frappe


_BRAND_FIELDS = (
    "brand_name",
    "brand_logo",
    "brand_icon_192",
    "brand_icon_512",
    "brand_primary_color",
    "brand_secondary_color",
    "login_tagline",
)


def _site_default_currency() -> str:
    # Prefer the default Company's currency, then the site default, then SAR.
    try:
        default_company = frappe.defaults.get_global_default("company")
        if default_company:
            cur = frappe.db.get_value("Company", default_company, "default_currency")
            if cur:
                return cur
    except Exception:
        pass
    try:
        return frappe.db.get_default("currency") or "SAR"
    except Exception:
        return "SAR"


@frappe.whitelist(allow_guest=True)
def get() -> dict[str, Any]:
    """Return public branding config. Safe to expose pre-login."""
    settings = frappe.get_cached_doc("Fateh Support Settings")
    payload: dict[str, Any] = {field: settings.get(field) for field in _BRAND_FIELDS}
    payload["brand_name"] = payload.get("brand_name") or "Fateh Trading"
    payload["brand_primary_color"] = payload.get("brand_primary_color") or "#2563EB"
    payload["brand_secondary_color"] = payload.get("brand_secondary_color") or "#334155"
    payload["vapid_public_key"] = settings.get("vapid_public_key") or ""
    payload["default_currency"] = _site_default_currency()
    return payload
