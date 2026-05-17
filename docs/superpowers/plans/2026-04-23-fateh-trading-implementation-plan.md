# Fateh Trading — Implementation Plan

**Spec:** `docs/superpowers/specs/2026-04-23-fateh-trading-support-app-design.md`
**Starting state:** empty repo at `/Users/sayanthns/ERP - PWAs/fateh_support/`
**Target:** v1.0 feature-complete skeleton ready for `bench get-app` install + RMAX UAT.

## Phase order

Files are produced in this order so downstream phases can import from earlier ones. Each phase is self-contained and testable.

### Phase 1 — Repo scaffold

- `pyproject.toml`, `license.txt`, `README.md`, `.gitignore`.
- `fateh_support/__init__.py` with `__version__`.
- `fateh_support/modules.txt`, `patches.txt` (empty).
- `requirements.txt` (pywebpush, bcrypt).

### Phase 2 — DocTypes + fixtures

Create DocType JSON schemas:

- `fateh_support/fateh_support/doctype/fateh_support_settings/*` (Single).
- `fateh_support/fateh_support/doctype/sales_price_approval_request/*` (Submittable).
- `fateh_support/fateh_support/doctype/sales_price_approval_line/*` (Child).
- `fateh_support/fateh_support/doctype/fateh_push_subscription/*`.

Fixtures:

- `role.json` — `Fateh Viewer`, `Price Approver`.
- `custom_field.json` — Quotation + Sales Order: `custom_approval_status`, `custom_approval_request`, `custom_approval_approver`, `custom_approval_decision_note`. Item: `item_name_ar`.
- `property_setter.json` — placeholder for per-site tweaks.

### Phase 3 — Install + hooks

- `install.py` — `ensure_capacitor_cors`, `seed_settings`, `generate_vapid_if_missing` (deferred to helper — requires py-vapid).
- `hooks.py` — `doc_events` (Quotation/SO `before_submit`), `after_migrate`, `website_route_rules` (`/fateh` → SPA), `website_redirects` (`/fateh` → `/assets/fateh_support/frontend/index.html`), `app_include_js`, notifications config, fixtures list.

### Phase 4 — Approval gate

- `approvals/__init__.py`.
- `approvals/gate.py`:
  - `check_cost_floor(doc, method)` — loads settings, scans items, creates approval request on violation, throws.
  - `resolve_cost_floor_rate(item_code, cost_floor_price_list, currency)`.
  - `build_approval_request(doc, violations)`.
  - `guard_approved_submit(doc, method)` — clears approval lock on submit.

### Phase 5 — Backend API

- `api/__init__.py`.
- `api/auth.py` — `login`, `ping`, `logout`, `pin_login` (v1.1 stub wired but unused v1.0).
- `api/branding.py` — `get` returns config; `set` for admin (wraps `save`).
- `api/items.py` — `search`, `stock`, `prices`.
- `api/approvals.py` — `list`, `get`, `decide`, `mine`.
- `api/push.py` — `subscribe`, `unsubscribe`.
- `api/pwa.py` — `manifest`, `sw` (returns templated service worker with VAPID pub key inline).

### Phase 6 — Notifications

- `notifications/__init__.py`.
- `notifications/realtime.py` — `publish_approval_created`, `publish_approval_decided`.
- `notifications/push.py` — `fanout(users, payload)`, `send_one(subscription, payload)`, dead-endpoint cleanup.
- `notifications/email.py` — `fallback_email(user, subject, body)`.

### Phase 7 — Backend tests

- `tests/__init__.py`, `tests/setup_fixtures.py` (seed helpers).
- `tests/test_approval_gate.py`.
- `tests/test_approvals_api.py`.
- `tests/test_items_api.py`.
- `tests/test_branding_api.py`.
- `tests/test_push.py`.

### Phase 8 — Frontend scaffold

- `frontend/package.json`, `frontend/pnpm-lock.yaml` (empty for now).
- `frontend/tsconfig.json`, `tsconfig.node.json`.
- `frontend/vite.config.ts` — base depends on command (`/` dev, `/assets/fateh_support/frontend/` prod).
- `frontend/index.html`.
- `frontend/.gitignore`.

### Phase 9 — Frontend core

- `src/main.ts`, `src/App.vue`, `src/router/index.ts`.
- `src/utils/platform.ts`, `src/utils/db.ts`, `src/utils/format.ts`.
- `src/api/client.ts`, `src/api/auth.ts`, `src/api/items.ts`, `src/api/approvals.ts`, `src/api/branding.ts`, `src/api/push.ts`.
- `src/stores/auth.ts`, `src/stores/branding.ts`, `src/stores/approvals.ts`, `src/stores/items.ts`, `src/stores/prefs.ts`.
- `src/composables/useBranding.ts`, `useSocket.ts`, `usePush.ts`, `useOnline.ts`.
- `src/i18n/index.ts`, `en.json`, `ar.json`.

### Phase 10 — Frontend views + components

- All views listed in spec §3.7.
- All components listed in spec §3.7.
- Styles: `styles/tokens.css`, `styles/main.css`.

### Phase 11 — Service worker + PWA

- `src/service-worker/sw.ts` — compiled to `public/frontend/sw.js`.
- `public/icons/*.png` — placeholder icons.
- `public/manifest.webmanifest` — static shell (dynamic version served by backend).

### Phase 12 — Frontend tests

- `tests/stores/auth.test.ts`, `approvals.test.ts`, `branding.test.ts`.
- `tests/components/StockTable.test.ts`, `PriceTable.test.ts`, `DecisionSheet.test.ts`, `LangToggle.test.ts`.

### Phase 13 — Deployment + onboarding README

- Top-level `README.md` with install steps.
- `docs/deployment.md` — bench install, site config, VAPID key generation, RMAX onboarding checklist.

## Test strategy

- Backend: Frappe runs `bench --site <site> run-tests --app fateh_support`.
- Frontend: `pnpm test` via Vitest.
- Integration: manual smoke per UAT checklist.

## Definition of done for tonight

- Spec written + auto-approved.
- Implementation plan written (this doc).
- Full Frappe app tree committed, syntactically valid, importable.
- Frappe tests defined — pass against seeded fixtures.
- Full Vue 3 PWA tree committed, `pnpm build` produces a bundle.
- README documents install + RMAX onboarding.
- No install executed on user's bench (user runs it).

What is NOT done tonight:

- Running `bench get-app` / `bench install-app` on the user's machine.
- Capacitor Android shell (v1.1).
- VAPID keypair generation (user seeds at install).
- RMAX production secrets.
- Real SPA icons (placeholder PNGs).
