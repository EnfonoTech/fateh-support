"""Serve the compiled PWA shell at /fateh/.

Frappe serves this page's HTML template (`index.html`) and injects branding
+ VAPID public key into the context so the SPA can bootstrap synchronously.

We also append a cache-busting `?v=<mtime>` query string to the bundle URLs
so mobile browsers don't keep serving a stale JS bundle after we ship a
fix.
"""

from __future__ import annotations

import os
from typing import Any

import frappe

no_cache = 1


def _safe_csrf() -> str:
    try:
        return frappe.sessions.get_csrf_token()
    except Exception:
        return ""


def _bundle_version() -> str:
    """Return the mtime of the JS bundle so the URL changes on each deploy."""
    try:
        path = frappe.get_app_path("fateh_support", "public", "frontend", "index.js")
        if os.path.exists(path):
            return str(int(os.path.getmtime(path)))
    except Exception:
        pass
    return "0"


def get_context(context):
    from fateh_support.api import branding as branding_api

    brand = branding_api.get()
    context.brand_name = brand.get("brand_name") or "Fateh Trading"
    context.brand_primary_color = brand.get("brand_primary_color") or "#2563EB"
    context.vapid_public_key = brand.get("vapid_public_key") or ""
    context.csrf_token = _safe_csrf()
    context.asset_base = "/assets/fateh_support/frontend"
    context.bundle_version = _bundle_version()
    context.no_cache = 1
    return context
