# Deployment & RMAX Onboarding Checklist

## Bench install

```bash
cd ~/frappe-bench
bench get-app fateh_support /path/to/fateh_support
bench --site <site> install-app fateh_support
bench --site <site> migrate
```

## Pre-flight checks

- [ ] `bench version` ≥ 15.0
- [ ] `pip show pywebpush` present; `pip show bcrypt` present
- [ ] `site_config.json::allow_cors` contains `https://localhost`, `capacitor://localhost`, `http://localhost` (or `*`)
- [ ] Nginx / Traefik terminates TLS (PWA refuses to install over HTTP)
- [ ] Socket.IO is reachable: `curl -i https://<site>/socketio/` returns 200
- [ ] `System Manager → Role` has `Fateh Viewer` and `Price Approver` (loaded by fixture)
- [ ] Custom fields on Quotation / Sales Order exist (load fixtures: `bench --site <site> migrate` runs them automatically)

## RMAX configuration sheet

Capture these values before kickoff so the first bench install is one-and-done.

| Key | Value |
|---|---|
| `brand_name` | RMAX |
| `brand_logo` | `<upload>` |
| `brand_icon_192` | `<upload>` |
| `brand_icon_512` | `<upload>` |
| `brand_primary_color` | `<hex>` |
| `brand_secondary_color` | `<hex>` |
| `cost_floor_price_list` | `RMAX Cost Floor` |
| `show_valuation_to_approvers` | ON |
| `notification_timeout_mins` | 30 |
| `vapid_public_key` | generated |
| `vapid_private_key` | generated |
| `vapid_subject` | `mailto:ops@rmax.com` |
| `sentry_dsn` | optional |

## User mapping (RMAX pilot)

- `Fateh Viewer` → every sales, showroom, branch-manager user.
- `Price Approver` → Sales Managers only.
- Exclusions: users in the `Inter-Company` business unit → restrict via `User Permission` on Warehouse + Company so the `items.stock` API returns nothing. No app-side blocklist is required.

## Cost-floor Price List maintenance

Static per-item rates. Maintain via desk or bulk import:

```csv
Item Code,Price List,Rate,Currency
ITM-001,RMAX Cost Floor,120,SAR
ITM-002,RMAX Cost Floor,95,SAR
```

Missing rows = item not gated. Review monthly with the RMAX ops team.

## Rollout plan

- **Day -7**: Enfono deploys app to RMAX staging bench. Smoke-test login, search, a mock Quotation below cost.
- **Day -3**: Client super-user runs through 10 UAT scenarios (Section 6 of the spec).
- **Day 0**: Production install. Small pilot group (3 approvers, 10 sales users).
- **Day +14**: Review analytics — weekly active users, median decision time, % of below-cost SOs routed through the app.
- **Day +30**: Full RMAX rollout.

## Health monitoring

- Frappe Error Log filtered by `method LIKE '%fateh_support%'` reviewed daily for 14 days.
- Sentry (if DSN configured) dashboards: session crash-free rate, unhandled promise rejections in the PWA.
- Push-send failures: inspect `Fateh Push Subscription` list for stale entries (auto-pruned on 404/410).

## Rollback

- `bench --site <site> uninstall-app fateh_support` leaves custom fields in place with no data loss on source docs; `custom_approval_status` remains read-only. Re-install reinstates behaviour.
- PWA is served from Frappe — no CDN invalidation required on rollback.
