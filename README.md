# Fateh Trading — ERPNext Support App

Mobile PWA companion for ERPNext trading implementations in KSA and UAE.

Two jobs in one app:

- **Stock & price visibility.** Sales and showroom staff look up live warehouse-wise stock and selling prices without loading the desktop UI.
- **Below-cost approval workflow.** Managers review, approve, or reject Quotations and Sales Orders whose rates fall below a client-defined cost floor. Full audit trail linked to the source document.

Shipped as a Frappe custom app (backend) + Vue 3 Progressive Web App (frontend). White-label branding per client via `Fateh Trading Settings`.

## Prerequisites

- Frappe v15 / ERPNext v15 bench.
- Python 3.10+ on the bench.
- Node 20+ and pnpm 8+ (or npm / yarn) for frontend builds.
- `pywebpush` and `bcrypt` (pip-installable, wired into `pyproject.toml`).

## Install the Frappe app

From a Frappe bench root:

```bash
bench get-app fateh_trading /path/to/fateh_trading
bench --site <your-site> install-app fateh_trading
bench --site <your-site> migrate
```

`after_migrate` automatically merges the Capacitor CORS origins into `site_config.json::allow_cors` and seeds `Fateh Trading Settings` with defaults.

## Configure the pilot (RMAX)

1. Desk → **Fateh Trading Settings**:
   - `brand_name` = "RMAX"
   - Upload `brand_logo`, `brand_icon_192`, `brand_icon_512` (PNG, transparent background recommended).
   - `brand_primary_color` + `brand_secondary_color` to match RMAX brand guide.
   - `cost_floor_price_list` = the Price List holding per-item cost-floor rates (create one if missing: "RMAX Cost Floor", Currency = site default, Selling = 1).
   - `show_valuation_to_approvers` = ON if approvers should see valuation + last purchase rate.
   - `enable_push` = ON.
   - Generate VAPID keys (see below) and paste `vapid_public_key` + `vapid_private_key`.
   - `vapid_subject` = `mailto:<ops-contact>@rmax-client-domain.com`.
2. Maintain `Item Price` rows for every SKU on the cost-floor Price List. Missing rows = that item is not gated.
3. User Management:
   - Assign `Fateh Viewer` to every sales / showroom / manager who should use the app.
   - Assign `Price Approver` to managers who may approve below-cost requests (you can assign both).
   - Restrict stock and price visibility for excluded users via standard **User Permission** (Warehouse, Company, Price List).
4. Put the cost-floor Price List under a User Permission scoped to the `Price Approver` role so regular viewers cannot read it.

### Generate VAPID keys

```bash
pip install py-vapid
python -m py_vapid.main --gen
# writes public_key.pem and private_key.pem
python - <<'PY'
from py_vapid import Vapid
v = Vapid.from_file("./private_key.pem")
print("public", v.public_key_bytes_b64())
print("private", v.private_pem().decode())
PY
```

Paste the base64url public key into `vapid_public_key`, the PEM into `vapid_private_key`.

## Build the frontend

```bash
cd apps/fateh_trading/frontend
pnpm install          # or npm install
pnpm build            # writes to ../fateh_trading/public/frontend/
```

Then on the bench:

```bash
bench build --app fateh_trading
bench --site <your-site> clear-cache
```

The PWA is served at `https://<your-site>/fateh/`.

## Local development

```bash
# Terminal 1 — Frappe bench
bench start

# Terminal 2 — frontend dev server (proxies /api to bench on :8000)
cd apps/fateh_trading/frontend
pnpm dev
```

Open `http://localhost:8082/`. Login uses the Frappe session cookie proxied through.

## Tests

```bash
# Backend
bench --site <test-site> run-tests --app fateh_trading

# Frontend
cd apps/fateh_trading/frontend
pnpm test
```

## How the workflow fires

1. Sales user creates a Quotation or Sales Order in ERPNext with an item rate below the cost-floor Price List rate.
2. `before_submit` hook creates a `Sales Price Approval Request`, flags the source doc as `Pending Approval`, and throws with a link to the request.
3. Approver receives three signals:
   - **Socket.IO** update if they have the app open (instant).
   - **Web Push** OS notification (backgrounded).
   - **Email** fallback if no active push subscription.
4. Approver opens the app, reviews the request detail (stock snapshot, valuation rate, justification, source doc link), and taps Approve or Reject.
5. Approval flips the source doc's `custom_approval_status = Approved`; rejection keeps it locked at `Rejected`. Requester is notified via the same three channels.
6. On Approve, the requester re-submits the source doc in ERPNext; the gate now lets it through.

## White-labelling another client

1. Install the same app on the client's bench.
2. Edit `Fateh Trading Settings` with their brand values.
3. No rebuild needed — the PWA pulls branding from the server on load.

## Capacitor native shell (v1.1, post-pilot)

See `android-capacitor/` scaffold (not yet wired). Token auth via `auth.pin_login`, same APIs, Firebase Cloud Messaging push.

## Troubleshooting

| Symptom | Check |
|---|---|
| PWA shows "Sign-in failed" on a known-good password | Site's `ignore_csrf` or CSRF token missing — confirm `csrf_token` cookie is set and `X-Frappe-CSRF-Token` is echoed in the request |
| Submit on Quotation silently succeeds with a below-cost rate | `cost_floor_price_list` not set in Settings OR that Price List has no `Item Price` row for the SKU |
| Approvers not notified | `enable_push` off, or VAPID keys missing, or the approver has not tapped "Enable notifications" in Settings |
| Inbox stuck | Check Frappe Error Log for `fateh_trading` entries; Socket.IO handshake failure falls back to a 30s poll on reconnect |
| App opens to a blank screen | Browser refused to register the service worker over HTTP — PWA requires HTTPS except on `localhost` |

## License

Proprietary — Enfono Technologies. Internal use and commercially-licensed deployments only.
