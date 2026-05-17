# Fateh Trading — ERPNext Support App

**Version:** 0.1 Design
**Date:** 2026-04-23
**Product Owner:** Sayanth (Enfono)
**Pilot Client:** RMAX
**Source PRD:** `ERPNext_Support_App_PRD_v0.1.docx` (Enfono, 2026-04-23)

## 1. Purpose

Lightweight mobile companion for ERPNext trading implementations in KSA and UAE. Serves two jobs:

1. **Read-only visibility.** Sales and showroom staff check live warehouse-wise stock balance and selling prices without loading the desktop UI.
2. **Below-cost approval workflow.** Managers review, approve, or reject sales requests where the proposed rate falls below a client-defined cost floor. Full audit trail linked back to the source Quotation or Sales Order.

Pilot at RMAX. If successful, generalised as a reusable Enfono offering. App name: **Fateh Trading**; per-client white-label via site config (brand name, logo, colors).

## 2. Scope

### In scope (v1.0)

- Email/password auth (Frappe session on web, API key/secret on native Capacitor shell).
- Item search by code / name / barcode; warehouse-wise stock view; price list rows.
- Below-cost detection in ERPNext via `before_submit` hook on Quotation and Sales Order.
- `Sales Price Approval Request` DocType with full context and audit trail.
- Approver inbox (pending, approved, rejected, mine) with real-time updates.
- Request detail with stock snapshot, valuation rate (approver-only), source doc link.
- Approve / reject with mandatory note on reject.
- Requester's "My Requests" view with push + email on decision.
- Real-time delivery via Socket.IO (in-app) + Web Push (backgrounded) + email fallback.
- Bilingual UI (English + Arabic, full RTL).
- White-label branding via `Fateh Trading Settings` Single DocType.

### Out of scope (v1.0)

- Offline mode with local writes.
- Creating or editing Quotations / Sales Orders from the app.
- General-purpose workflow engine (approval type is fixed: below-cost only).
- Customer-facing access.
- Multi-level approval escalation.
- Barcode camera scan (deferred to v1.1).
- Native app store distribution via Capacitor (deferred to v1.1).
- Multi-company tenancy in a single Settings Single (v1.2).

## 3. Architecture

### 3.1 High-level

```
┌─────────────────────────┐      HTTPS / REST       ┌──────────────────────────┐
│  PWA (Vue 3 + Pinia)    │ ──────────────────────▶ │  Frappe app              │
│  installable web app    │                         │  `fateh_support`         │
│  Capacitor v1.1 shell   │ ◀── Socket.IO / Push ── │  (alongside ERPNext)     │
└─────────────────────────┘                         └──────────────────────────┘
                                                           │
                                                           ▼
                                                    ┌──────────────┐
                                                    │   ERPNext    │
                                                    │  Item · Bin  │
                                                    │  Item Price  │
                                                    │  Quotation   │
                                                    │  Sales Order │
                                                    └──────────────┘
```

- One custom Frappe app (`fateh_support`) installed beside ERPNext. Adds DocTypes, hooks, whitelisted API.
- One Vue 3 PWA (`frontend/`) served from Frappe at `/fateh/` via `createWebHashHistory("/assets/fateh_support/frontend/")`.
- Capacitor Android shell (v1.1) symlinks `frontend/src/` and builds its own `www/` bundle.
- All persistence in ERPNext. PWA stores only session, branding cache, and recent searches in IndexedDB. No offline writes.

### 3.2 Repository layout

```
fateh_support/
├── fateh_support/                   ← Frappe app
│   ├── __init__.py
│   ├── hooks.py
│   ├── install.py                   ← ensure_capacitor_cors + seed settings
│   ├── api/
│   │   ├── auth.py
│   │   ├── branding.py
│   │   ├── items.py
│   │   ├── approvals.py
│   │   ├── push.py
│   │   ├── pwa.py                   ← dynamic manifest
│   ├── approvals/
│   │   └── gate.py                  ← before_submit hook
│   ├── notifications/
│   │   ├── push.py                  ← web push fanout
│   │   ├── socket.py                ← realtime publish
│   │   └── email.py
│   ├── fateh_support/doctype/
│   │   ├── fateh_support_settings/
│   │   ├── sales_price_approval_request/
│   │   ├── sales_price_approval_line/
│   │   └── fateh_push_subscription/
│   ├── fixtures/
│   │   ├── custom_field.json        ← Quotation / SO approval flag fields
│   │   ├── role.json                ← Fateh Viewer, Price Approver
│   │   ├── property_setter.json
│   ├── public/frontend/             ← Vite output
│   ├── www/fateh/
│   │   └── index.py                 ← SPA entry
│   ├── tests/
│   ├── patches.txt
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── public/
│   │   └── icons/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/index.ts
│   │   ├── stores/
│   │   │   ├── auth.ts
│   │   │   ├── branding.ts
│   │   │   ├── approvals.ts
│   │   │   ├── items.ts
│   │   │   └── prefs.ts
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── items.ts
│   │   │   ├── approvals.ts
│   │   │   ├── branding.ts
│   │   │   ├── push.ts
│   │   ├── composables/
│   │   │   ├── useBranding.ts
│   │   │   ├── useSocket.ts
│   │   │   ├── usePush.ts
│   │   │   ├── useOnline.ts
│   │   ├── views/
│   │   │   ├── LoginView.vue
│   │   │   ├── ItemSearchView.vue
│   │   │   ├── ItemDetailView.vue
│   │   │   ├── ApprovalsView.vue
│   │   │   ├── ApprovalDetailView.vue
│   │   │   ├── MyRequestsView.vue
│   │   │   ├── SettingsView.vue
│   │   ├── components/
│   │   │   ├── AppShell.vue
│   │   │   ├── StockTable.vue
│   │   │   ├── PriceTable.vue
│   │   │   ├── RequestCard.vue
│   │   │   ├── DecisionSheet.vue
│   │   │   ├── LangToggle.vue
│   │   │   ├── BadgeCount.vue
│   │   │   ├── VarianceBanner.vue
│   │   ├── i18n/
│   │   │   ├── index.ts
│   │   │   ├── en.json
│   │   │   ├── ar.json
│   │   ├── utils/
│   │   │   ├── platform.ts
│   │   │   ├── db.ts                ← IndexedDB recent searches
│   │   │   ├── format.ts
│   │   ├── service-worker/
│   │   │   └── sw.ts
│   │   ├── styles/
│   │   │   ├── tokens.css
│   │   │   └── main.css
│   └── tests/
├── android-capacitor/               ← v1.1
├── docs/superpowers/specs/
├── docs/superpowers/plans/
├── pyproject.toml
├── README.md
├── license.txt
```

### 3.3 Backend — DocTypes

**Sales Price Approval Request** (submittable)

| Field | Type | Notes |
|---|---|---|
| `naming_series` | Select | `SPAR-.YYYY.-` |
| `status` | Select | Pending / Approved / Rejected (default Pending) |
| `requester` | Link User | Auto from `frappe.session.user` |
| `customer` | Link Customer | |
| `source_doctype` | Select | Quotation / Sales Order |
| `source_name` | Dynamic Link | |
| `currency` | Link Currency | From source doc |
| `total_proposed` | Currency | Sum of line_total on lines |
| `total_cost_floor` | Currency | Sum of cost_floor_total |
| `variance_amount` | Currency | proposed − floor |
| `variance_pct` | Percent | absolute pct |
| `line_total_impact` | Currency | same as variance_amount |
| `justification` | Small Text | Requester optional |
| `approver` | Link User | Set on decide |
| `decision_note` | Small Text | Mandatory if rejected |
| `decided_at` | Datetime | |
| `lines` | Table: Sales Price Approval Line | One row per below-cost line |

**Sales Price Approval Line** (child)

| Field | Type | Notes |
|---|---|---|
| `item_code` | Link Item | |
| `item_name` | Data | Fetched |
| `qty` | Float | |
| `uom` | Link UOM | |
| `proposed_rate` | Currency | |
| `cost_floor_rate` | Currency | From cost-floor Price List |
| `valuation_rate` | Currency | Approver-only (API filters for viewers) |
| `last_purchase_rate` | Currency | Approver-only |
| `variance_amount` | Currency | |
| `variance_pct` | Percent | |
| `line_total` | Currency | |

**Fateh Trading Settings** (Single)

| Field | Type | Notes |
|---|---|---|
| `cost_floor_price_list` | Link Price List | |
| `brand_name` | Data | Default "Fateh Trading" |
| `brand_logo` | Attach | Public file |
| `brand_icon_192` | Attach | PWA icon 192 |
| `brand_icon_512` | Attach | PWA icon 512 |
| `brand_primary_color` | Color | Default `#1d4ed8` |
| `brand_secondary_color` | Color | |
| `login_tagline` | Data | |
| `vapid_public_key` | Data | |
| `vapid_private_key` | Password | |
| `vapid_subject` | Data | `mailto:` |
| `enable_push` | Check | Default 1 |
| `notification_timeout_mins` | Int | Default 30 |
| `show_valuation_to_approvers` | Check | Default 1 |
| `sentry_dsn` | Data | Optional |

**Fateh Push Subscription**

| Field | Type | Notes |
|---|---|---|
| `user` | Link User | |
| `endpoint` | Small Text | Unique with `user` |
| `type` | Select | web / fcm / apns |
| `p256dh` | Data | Web only |
| `auth` | Data | Web only |
| `user_agent` | Small Text | |

**Custom fields on Quotation and Sales Order (fixture):**

- `custom_approval_status` — Select (blank / Pending Approval / Approved / Rejected).
- `custom_approval_request` — Link: `Sales Price Approval Request`.

### 3.4 Backend — approval gate

Hook `fateh_support.approvals.gate.check_cost_floor` runs on `before_submit` of Quotation and Sales Order:

1. If `doc.custom_approval_status == "Approved"`, return — approved requests proceed.
2. Load `cost_floor_price_list` from settings. If not set, return (misconfigured sites don't block sales).
3. For each item in `doc.items`, look up cost-floor rate. Collect lines where `item.rate < cost_floor_rate`.
4. If no violations, return.
5. If violations and `doc.custom_approval_request` exists with status Pending, `frappe.throw("Approval already in flight")`.
6. Otherwise create `Sales Price Approval Request` with one child line per violation. Set `doc.custom_approval_status = "Pending Approval"` and `doc.custom_approval_request = req.name`. Save source as draft. `frappe.throw(_("Price below cost floor — approval requested"))` to block submit.

On `approvals.decide`:

- Approve: load source doc, set `custom_approval_status = "Approved"`, `custom_approval_decision_note`, `custom_approval_approver`, save. Requester re-submits.
- Reject: set `custom_approval_status = "Rejected"`. Source remains draft.

### 3.5 Backend — API surface

All under `/api/method/fateh_support.api.*`.

| Endpoint | Method | Guard | Returns |
|---|---|---|---|
| `auth.login` | POST | allow_guest | user, full_name, roles, is_approver, branding |
| `auth.ping` | GET | logged-in | timestamp, user |
| `auth.logout` | POST | logged-in | ok |
| `auth.pin_login` | POST | allow_guest | api_key/secret (v1.1) |
| `branding.get` | GET | allow_guest | brand config |
| `items.search` | GET | Fateh Viewer | list of {code, name, name_ar, uom, image} |
| `items.stock` | GET | Fateh Viewer | bins {warehouse, actual, reserved, projected, ordered} with totals |
| `items.prices` | GET | Fateh Viewer | rows filtered by role (cost-floor hidden for viewers) |
| `approvals.list` | GET | Fateh Viewer | pending / approved / rejected / mine with pagination |
| `approvals.get` | GET | Fateh Viewer | full detail incl. source link + stock snapshot; valuation only if approver |
| `approvals.decide` | POST | Price Approver | updates status, source doc, triggers notification |
| `approvals.mine` | GET | Fateh Viewer | requester history |
| `push.subscribe` | POST | logged-in | ok |
| `push.unsubscribe` | POST | logged-in | ok |
| `pwa.manifest` | GET | allow_guest | dynamic webmanifest with branding |
| `pwa.sw` | GET | allow_guest | service worker bootstrap |

### 3.6 Notifications

Three layers, all fire for the same event:

1. **Socket.IO** (`frappe.publish_realtime`, `user=target`) — instant update when app open. Event name `fateh_approval_update`.
2. **Web Push** (VAPID, `pywebpush`) — OS notification when backgrounded. Stored subscriptions per user. Dead endpoints (410/404) deleted on send.
3. **Email** (`frappe.sendmail`) — fallback when user has no active subscription.

Events fired:

- Approval Request inserted → all users with `Price Approver` role.
- Approval decided → requester.

Reconnect path: on Socket.IO reconnect, PWA calls `approvals.list` to catch any events missed offline.

### 3.7 Frontend

**Stack:** Vite + Vue 3 + TypeScript, Pinia, Vue Router (hash history), vue-i18n, idb.

**Routes:**

| Path | Role | View |
|---|---|---|
| `/login` | guest | LoginView |
| `/items` | viewer | ItemSearchView |
| `/items/:code` | viewer | ItemDetailView |
| `/approvals` | approver | ApprovalsView |
| `/approvals/:name` | approver | ApprovalDetailView |
| `/my-requests` | viewer | MyRequestsView |
| `/settings` | self | SettingsView |

Router guards redirect to login on 401 and hide approver routes for non-approvers.

**Stores:**

- `auth` — session state, roles, current user. Handles login, logout, refresh.
- `branding` — brand config from server. Applies CSS vars on `:root`.
- `approvals` — inbox cache, filters, pagination, socket event handler.
- `items` — item detail cache (short-lived), recent searches (IDB).
- `prefs` — locale, RTL flag, push permission state.

**Key components:**

- `AppShell` — top app bar with brand logo + title, bottom nav (Items / Approvals / Mine / Settings). Approvals tab badge = unread pending count.
- `StockTable` — warehouse rows grouped by company, sticky totals row.
- `PriceTable` — price list rows, cost-floor row hidden unless approver.
- `RequestCard` — inbox card: requester + customer + variance + age.
- `DecisionSheet` — modal bottom sheet; note required on reject, optional on approve.
- `VarianceBanner` — colour scale (amber < 5%, orange 5–15%, red ≥ 15%).
- `LangToggle` — en/ar switch, flips `<html dir>` and `lang`.

**I18n:** all strings in `en.json` / `ar.json`. Lazy-loaded. Currency and date via `Intl` with site locale.

**Service worker:** vanilla (no PWA plugin lock-in). Handles install + `push` + `notificationclick`. Fetched from `/api/method/fateh_support.api.pwa.sw` so Frappe can inject VAPID public key and app version.

### 3.8 Auth

- **Web (v1.0):** Frappe session cookie. `POST /api/method/login` with `usr` + `pwd`. CSRF token included on mutating calls.
- **Native (v1.1):** PIN or password → `auth.pin_login` returns API key + secret. Stored via `@capacitor/preferences`. Token header on every request. Re-login reuses existing `api_secret`.
- Biometric (v1.1) unlocks stored credentials only — not a second factor.
- Session timeout respects site default; `auth.ping` on app resume detects expiry.

### 3.9 Permissions

- All data access through whitelisted endpoints running under session user.
- Frappe DocPerm + User Permission enforce warehouse, company, and price list visibility.
- `items.prices` filters cost-floor Price List rows for users without `Price Approver` role.
- `approvals.decide` requires `Price Approver`; `approvals.get` allows `requester == session.user` even without approver role.
- Roles (fixtures): `Fateh Viewer` (Item, Bin, Item Price read), `Price Approver` (Viewer + Sales Price Approval Request read/write).
- Access exclusion is pure ERPNext User Permission — no app-side blocklist.

### 3.10 Localisation + branding

- `vue-i18n` with en/ar, lazy loaded. RTL flips `<html dir>` and uses logical CSS.
- Item name bilingual via custom field `item_name_ar` (fixture-added).
- Branding from `Fateh Trading Settings` applied as CSS vars + runtime `document.title` + dynamic `manifest.webmanifest`.
- Per-client deployment = install app, edit Settings, upload logo, done. No rebuild.

## 4. User flows

### 4.1 Stock + price lookup (viewer)

1. Open app → already signed in.
2. Tap search, type item code.
3. Select item → detail view shows warehouse-wise stock + price rows.
4. Relay to customer. Done.

### 4.2 Raise below-cost request (in ERPNext)

1. Sales user creates Quotation or SO in ERPNext with rate below cost floor.
2. On submit, `before_submit` hook blocks and creates `Sales Price Approval Request`.
3. User prompted for justification (re-submit with justification field populated on the Approval Request after creation — entered on a second dialog, or stored via separate API call immediately after the throw).
4. User opens app → My Requests → sees status Pending.

### 4.3 Approve or reject (approver)

1. Socket / push notification arrives.
2. Tap → request detail opens.
3. Review context (requester, customer, item, variance, stock snapshot, valuation rate, justification).
4. Optionally open source Quotation / SO in ERPNext mobile browser.
5. Tap Approve (optional note) or Reject (mandatory note).
6. Server updates request + source doc, fans out notification + email to requester.
7. Requester re-submits source doc (approve path) or revises (reject path).

## 5. Non-functional

| Dim | Target |
|---|---|
| Item search p95 | ≤ 1.5s on 4G |
| Item detail render | ≤ 2s |
| Inbox first page (20) | ≤ 2s |
| Decision round-trip | ≤ 3s |
| Socket reconnect | ≤ 3s after flap |
| Crash-free sessions | ≥ 99.5% |
| TLS | 1.2+ |
| Session storage | Keychain / Keystore (native), HTTPOnly cookies (web) |
| Text contrast | WCAG AA |
| Tap target | 44pt / 48dp min |

## 6. Testing

**Backend (Python, FrappeTestCase):**

- `test_approval_gate.py` — hook behaviour: pass/block, multiple items, missing floor, double-submit, approved path.
- `test_approvals_api.py` — decide, permission errors, mandatory reject note, status transitions.
- `test_items_api.py` — search, stock filtering, price filtering by role.
- `test_branding_api.py` — settings round-trip, dynamic manifest.
- `test_push.py` — subscribe/unsubscribe, dead endpoint cleanup.

**Frontend (Vitest):**

- Store tests — auth, approvals (socket events, optimistic + rollback), branding CSS var apply.
- Component tests — StockTable grouping, PriceTable role filtering, DecisionSheet reject validation, LangToggle RTL class flip.
- `fake-indexeddb` for recent-search cache.
- `msw` for API mocks.

**Performance + security:**

- Smoke test with seeded 100-request inbox.
- Contract test — cost-floor row absent in viewer prices response.
- `api_secret` never echoed beyond initial login response.

**UAT:**

- RMAX UAT checklist per §4 flows × en/ar × Android + iOS PWA install.

## 7. Milestones

| Milestone | Duration | Exit criteria |
|---|---|---|
| M0 — Design + schema | 1 wk | Spec signed, DocType JSONs drafted, RMAX config sheet collected |
| M1 — Auth + items | 2 wks | Login; search + detail render with stock + prices; bilingual + RTL; branding live |
| M2 — Approval workflow | 2 wks | Gate, inbox, detail, decide, socket + push + email, requester view |
| M3 — Hardening + UAT | 1 wk | Tests green, perf budget met, UAT sign-off, rollback rehearsed |
| M4 — Pilot rollout | 1 wk | Users onboarded, analytics + crash reporting live, support channel open |
| **M5 — Capacitor shell** | 1 wk | v1.1 after pilot stabilises |

**Total to pilot: 7 weeks.**

## 8. Risks

- **iOS Web Push < 16.4** — silently absent. Mitigation: email fallback + install-to-home-screen onboarding.
- **Socket.IO token auth on native** — Frappe v15 feature. Verify in M1; fallback to 30s poll if handshake fails.
- **Multi-company mid-pilot** — Settings is a Single DocType; multi-company cost-floor mapping deferred to v1.2.
- **Cost-floor Price List maintenance** — manual rate upkeep per item. Dynamic (valuation × margin) deferred to v1.1 if RMAX finds manual load painful.

## 9. Open questions (closed at sign-off)

| # | Question | Resolution |
|---|---|---|
| 1 | Cost-floor source | Static Price List |
| 2 | Approver routing | All users with `Price Approver` role |
| 3 | Cost price visibility | Valuation + last purchase visible to approver only |
| 4 | Access exclusion mechanism | Pure ERPNext User Permission |
| 5 | Platform | PWA v1.0, Capacitor v1.1 |
| 6 | App name | `fateh_support`; per-client white-label via Settings |
| 7 | Offline writes | None |
| 8 | Real-time | Socket.IO added to v1.0 (approval latency is load-bearing) |
| 9 | Sales-side entry | Raised from ERPNext only; app is approver + status view |

## 10. References

- Source PRD: `ERPNext_Support_App_PRD_v0.1.docx`
- Fateh HR template: `/Users/sayanthns/Documents/fatehhr`
- Frappe-Vue-PWA skill: `/Users/sayanthns/.claude/skills/frappe-vue-pwa/SKILL.md`
