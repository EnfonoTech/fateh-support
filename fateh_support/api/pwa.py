"""Dynamic PWA manifest and service-worker scaffolding.

The service worker needs the VAPID public key baked in — serving it from a
Python endpoint lets the operator update the key via the Settings DocType
without a frontend rebuild.
"""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Any

import frappe


def _set_headers(**headers: str) -> None:
    """Attach response headers, creating the dict if Frappe has not yet.

    `frappe.local.response.headers` is None on a fresh response, so assigning
    into it raises TypeError and the endpoint 500s. Both PWA routes did that
    on their last line, which is why the service worker and the manifest have
    never once been served — and therefore why web push has never worked.
    """
    if not frappe.local.response.get("headers"):
        frappe.local.response["headers"] = {}
    frappe.local.response["headers"].update(headers)


def _branding() -> dict[str, Any]:
    from fateh_support.api import branding as branding_api

    return branding_api.get()


@frappe.whitelist(allow_guest=True)
def manifest() -> None:
    """Render a dynamic webmanifest that reflects client branding."""
    brand = _branding()
    name = brand.get("brand_name") or "Fateh Trading"
    primary = brand.get("brand_primary_color") or "#1d4ed8"
    icon_192 = brand.get("brand_icon_192") or "/assets/fateh_support/frontend/icons/icon-192.png"
    icon_512 = brand.get("brand_icon_512") or "/assets/fateh_support/frontend/icons/icon-512.png"

    payload = {
        "name": name,
        "short_name": name,
        "description": name,
        "start_url": "/fateh/",
        "scope": "/fateh/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#ffffff",
        "theme_color": primary,
        "icons": [
            {"src": icon_192, "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": icon_512, "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }

    frappe.local.response["type"] = "binary"
    frappe.local.response["filename"] = "manifest.webmanifest"
    frappe.local.response["filecontent"] = json.dumps(payload).encode("utf-8")
    _set_headers(**{"Content-Type": "application/manifest+json"})


@frappe.whitelist(allow_guest=True)
def sw() -> None:
    """Service worker stub — receives push events and shows notifications."""
    brand = _branding()
    name = brand.get("brand_name") or "Fateh Trading"
    vapid = brand.get("vapid_public_key") or ""

    body = dedent(
        f"""
        self.VAPID_PUBLIC_KEY = {json.dumps(vapid)};
        self.BRAND_NAME = {json.dumps(name)};

        self.addEventListener('install', (e) => self.skipWaiting());
        self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

        self.addEventListener('push', (event) => {{
          let data = {{}};
          try {{ data = event.data ? event.data.json() : {{}}; }}
          catch (err) {{ data = {{ body: event.data ? event.data.text() : '' }}; }}
          const title = data.title || self.BRAND_NAME;
          const opts = {{
            body: data.body || '',
            icon: data.icon || '/assets/fateh_support/frontend/icons/icon-192.png',
            badge: '/assets/fateh_support/frontend/icons/icon-192.png',
            data: data.data || {{}},
            tag: data.tag || 'fateh_support',
          }};
          event.waitUntil(self.registration.showNotification(title, opts));
        }});

        self.addEventListener('notificationclick', (event) => {{
          event.notification.close();
          const target = (event.notification.data && event.notification.data.url) || '/fateh/';
          event.waitUntil(
            self.clients.matchAll({{ type: 'window', includeUncontrolled: true }}).then((clients) => {{
              for (const c of clients) {{
                if ('focus' in c) {{ c.navigate(target); return c.focus(); }}
              }}
              if (self.clients.openWindow) return self.clients.openWindow(target);
            }})
          );
        }});
        """
    ).strip()

    frappe.local.response["type"] = "binary"
    frappe.local.response["filename"] = "fateh-sw.js"
    frappe.local.response["filecontent"] = body.encode("utf-8")
    _set_headers(
        **{
            "Content-Type": "application/javascript; charset=utf-8",
            "Cache-Control": "no-store",
            # The script sits at the site root, so it may claim any scope; the
            # registration asks for /fateh/.
            "Service-Worker-Allowed": "/",
        }
    )
