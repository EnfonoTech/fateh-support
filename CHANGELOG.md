# Changelog

All notable changes to `fateh_support` are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.3] — 2026-08-16

### Fixed

- **Bulk Price disappeared from the item screen for branch users.** No code
  changed: `items.prices` has always hidden whichever list is configured as
  `cost_floor_price_list` from non-approvers, and that setting was empty
  until it was first configured — at which point the filter began firing and
  a price tier users had always seen silently vanished.

  The minimum price is a *selling* tier, not cost: a salesperson needs to
  know the floor they must not go under. It is now shown by default. Hiding
  it is opt-in via the new
  `Fateh Support Settings.hide_minimum_price_from_non_approvers`, off by
  default, and approvers always see it.

  Tests pin both directions so this cannot regress unnoticed again.

## [1.2.2] — 2026-08-16

### Fixed

- **Approve still failed from the Android app with "Request failed"**, while
  the same action worked from a desktop browser and from desk. Two bugs in
  the client's native branch, compounding:

  1. `authHeaders()` assumed "native" meant API-key auth, so it returned only
     an `Authorization` header — and `{}` when no key was stored. The APK is
     a remote-URL WebView that signs in with a session cookie like any
     browser tab, so every POST from it went out with **no CSRF header at
     all** and Frappe answered 400.
  2. The v1.1.0 refresh-and-replay fetched the new token with
     `credentials: "omit"` on native, so the server answered as Guest and
     returned a **Guest** token. The replay then failed identically — two
     400s in the same second, with no way out.

  The client no longer branches on "native" for credentials: it sends the
  CSRF header whenever it holds a token, the `Authorization` header whenever
  API keys are stored, and always includes cookies. Frappe ignores whichever
  is not relevant.

## [1.2.1] — 2026-08-16

### Fixed

- **"Could not find Source Name: RS-INV-…" when submitting a brand-new
  invoice.** Frappe's `Document.insert()` runs `before_submit` before
  `db_insert`, so the gate fires while the source row does not exist yet.
  `Sales Price Approval Request.source_name` is a Dynamic Link, so building
  the request died on link validation with a message naming an invoice the
  user had never seen. Submitting an already-saved draft was unaffected,
  which is why it looked intermittent.

  The gate now detects the unsaved case and asks for a draft instead. Nothing
  is persisted on that path — verified zero orphaned requests on production.

## [1.2.0] — 2026-08-16

### Added

- **Price lists can be exempted from the approval gate.** New
  `Fateh Support Settings.exempt_price_lists` — a sales document priced off any
  list in it skips the gate outright, whatever the rate. Inter-company
  transfers move stock between our own branches at cost, so measuring them
  against a customer-facing minimum flagged every one of them; a Sales Invoice
  on `Inter Company Price` raised an approval request for 5 of 5 lines.
  Exempting also clears a flag raised before the list was exempted, so
  documents already stuck behind a request are released on next submit.

  Matching is case-insensitive. Configured on RMAX with `Inter Company Price`.

## [1.1.2] — 2026-08-16

### Fixed

- **App failed to boot with "Unhandled promise: t is not a function".** The
  entry bundle ships under a stable `index.js` name and is cache-busted only by
  a `?v=<mtime>` query, while the chunks it imports are content-hashed — and
  `emptyOutDir: true` deleted the previous build's chunks on every rebuild. Any
  client holding a cached entry (the Capacitor WebView above all, which had held
  the May bundle for months) then requested chunk filenames that no longer
  existed, every dynamic import 404'd, and the app died on the fallback screen.
  Three rebuilds in one day is what made it bite.

  Every chunk set shipped since May is restored to `public/frontend/chunks/`, so
  cached entries resolve again with no action from the user. `emptyOutDir` is
  now `false` — do not turn it back on while the entry name is stable. A boot
  guard also catches dynamic-import failures and forces one reload, with a
  sessionStorage latch so it cannot loop.

## [1.1.1] — 2026-08-16

### Added

- Search by quotation number on **My Requests** too, not just the approvals
  list; `approvals.mine` now forwards a `search` term. Both lists share one
  `SearchBox` component.

### Security

- Both servers pulled this repo over an HTTPS remote with a **plaintext GitHub
  OAuth token** embedded in the URL — live, and scoped `repo`, `workflow`,
  `gist` on the owning account. Replaced with per-box read-only **deploy keys**
  (`~/.ssh/fateh_deploy`, generated on the box, pinned via repo-local
  `core.sshCommand`), matching how RMAX-Custom already worked. The token was
  scrubbed from both `.git/config` files and from a UAT `bench.log`, and needs
  revoking on GitHub.

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

[1.2.3]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.2.3
[1.2.2]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.2.2
[1.2.1]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.2.1
[1.2.0]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.2.0
[1.1.2]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.1.2
[1.1.1]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.1.1
[1.1.0]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.1.0
[1.0.1]: https://github.com/EnfonoTech/fateh-support/releases/tag/rmax-v1.0.1
[1.0.0]: https://github.com/EnfonoTech/fateh-support/releases/tag/v1.0.0
