"""Install hooks for Fateh Trading.

- `after_install` runs once on `bench install-app fateh_support`.
- `after_migrate` runs on every `bench migrate` — idempotent.
"""

import json
import os
from typing import Any

import frappe

CAPACITOR_ORIGINS = [
    "https://localhost",
    "capacitor://localhost",
    "http://localhost",
]

DEFAULT_SETTINGS: dict[str, Any] = {
    "brand_name": "Fateh Trading",
    "brand_primary_color": "#1d4ed8",
    "brand_secondary_color": "#334155",
    "login_tagline": "Stock visibility and approvals, simplified.",
    "enable_push": 1,
    "notification_timeout_mins": 30,
    "show_valuation_to_approvers": 1,
}


def after_install() -> None:
    """First-time install tasks."""
    ensure_capacitor_cors()
    seed_settings()


def ensure_capacitor_cors() -> None:
    """Merge Capacitor origins into `site_config.json::allow_cors`.

    Idempotent. Does nothing if `allow_cors == "*"`.
    """
    site_config_path = frappe.get_site_path("site_config.json")
    if not os.path.exists(site_config_path):
        return

    with open(site_config_path) as f:
        cfg = json.load(f)

    current = cfg.get("allow_cors")
    if current == "*":
        return

    origins: list[str] = list(current) if isinstance(current, list) else []
    changed = False
    for origin in CAPACITOR_ORIGINS:
        if origin not in origins:
            origins.append(origin)
            changed = True

    if not changed:
        return

    cfg["allow_cors"] = origins
    with open(site_config_path, "w") as f:
        json.dump(cfg, f, indent=1)


def seed_settings() -> None:
    """Seed `Fateh Trading Settings` with defaults on first run."""
    if not frappe.db.exists("DocType", "Fateh Support Settings"):
        return

    settings = frappe.get_single("Fateh Support Settings")
    changed = False
    for field, value in DEFAULT_SETTINGS.items():
        if not settings.get(field):
            settings.set(field, value)
            changed = True

    if changed:
        settings.flags.ignore_permissions = True
        settings.save(ignore_permissions=True)
        frappe.db.commit()
