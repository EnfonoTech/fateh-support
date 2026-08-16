# Changelog

All notable changes to `fateh_support` are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — 2026-08-16

### Fixed

- **Approving from the PWA always failed with HTTP 400.** `/fateh` renders
  before login, so the CSRF token injected into `window.FatehBoot` belonged to
  the Guest session; `post_login` then rotated the session and nothing pushed
  the new token to the SPA. Frappe only validates CSRF on unsafe methods, so
  every GET kept working while every POST — `approvals.decide` included — was
  rejected and surfaced as a bare "Request failed". `auth.me` now carries
  `csrf_token`, the new GET-only `auth.csrf` hands out a fresh one, and the API
  client refreshes and replays once on any 400 POST, which also heals sessions
  that rotate mid-use.
- `decide_bulk` raised `TypeError` on every call: this module defines `list` as
  a REST alias, so `isinstance(names, (list, tuple))` was handed a function
  where a type belongs.
- Test sandbox looked for warehouse `Main - Fat` (company name sliced to three
  characters) while Frappe names it `Main - FTC` (company abbr), so the insert
  collided with the previous run and took 20 of 24 tests down.
- Approval requests in tests pointed `source_name` at a non-existent
  `QUO-TEST-X`; the Dynamic Link failed validation on insert and on every
  `decide()` save. The sandbox now builds a real draft Quotation, so the source
  write-back is exercised too.
- `DecisionSheet` tests queried the wrapper subtree for markup the component
  renders through `<teleport to="body">`.

### Added

- **Approve and reject from desk.** Approve/Reject buttons with a note dialog on
  the Sales Price Approval Request form (note mandatory on reject), plus
  multi-select bulk Approve/Reject in the list view backed by a new
  `approvals.decide_bulk` endpoint that decides each request independently and
  reports per-name outcomes. Both surfaces call the same server path as the
  mobile app, so they cannot drift.
- Status colours and an at-a-glance variance/impact headline on the request.
- **Search the PWA approvals list by quotation number**, debounced, with a clear
  button and a named empty state.

### Changed

- "Cost floor" is now "minimum selling price" throughout labels, the
  before-submit message and the PWA (English and Arabic). The configured floor
  list is a *selling* tier, so a line priced well above valuation could still be
  blocked and read as below cost. Fieldnames stay `cost_floor_*` — no migration.

## [1.0.1] — 2026-05-24

### Changed

- Capacitor shell retargeted at `rmaxerp.enfonoerp.com/fateh/`.
- Login accepts a plain username, not only an email address.

## [1.0.0] — 2026-05-17

- First release: stock visibility PWA, below-cost approval workflow, Android
  shell.

[1.1.0]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.1.0
[1.0.1]: https://github.com/EnfonoTech/fateh-support/releases/tag/rmax-v1.0.1
[1.0.0]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.0.0
