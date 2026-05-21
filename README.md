# Lite Analytics Core

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

**Lite Analytics Core** is a lightweight, self-hosted analytics and web push subscription backend for first-party PWA projects.

Collect page views, custom events, device context, and web push subscriptions on infrastructure you control — without relying on third-party analytics or push platforms.

---

## Features

| Area | Capabilities |
|------|----------------|
| **Analytics** | Pageviews, custom events, paths, referrers, visitors and sessions |
| **Storage** | SQLite with WAL mode (PostgreSQL planned) |
| **API** | Public event ingestion and push subscribe; private stats and push send |
| **Dashboard** | Per-project stats UI with authentication |
| **Tracker** | Vanilla `tracker.js` with `sendBeacon` / `fetch` fallback |
| **Web Push** | Subscription storage and VAPID-based delivery |
| **Hardening (v1.1)** | IP rate limiting, bot filtering, input validation, structured logging |

---

## Why Self-Hosted

- **Data ownership** — events and subscriptions remain in your database
- **First-party deployment** — the tracker talks directly to your backend
- **Minimal footprint** — small Python service and a single JavaScript embed
- **No vendor lock-in** — standard HTTP APIs and SQLite storage
- **Transparent operation** — you control configuration, retention, and access

---

## Architecture

```
┌─────────────┐     POST /api/track          ┌──────────────────────┐
│  Your PWA   │ ───────────────────────────► │  Lite Analytics Core │
│ tracker.js  │     POST /api/push/subscribe │  (FastAPI + SQLite)  │
└─────────────┘                              └──────────┬───────────┘
                                                        │
                        GET /api/stats (API key)        │
                        GET /dashboard (auth)           ▼
                                               ┌────────────────┐
                                               │ analytics.db   │
                                               └────────────────┘
```

**Components:**

- `tracker.js` — client-side event collection
- `app/routes/` — HTTP endpoints
- `app/services/` — analytics and push business logic
- `app/security/` — rate limiting
- `app/templates/` — Jinja2 dashboard

---

## Installation

**Requirements:** Python 3.10+

```bash
git clone https://github.com/YOUR_ORG/LiteAnalytics.git
cd LiteAnalytics
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` before running. See [Configuration](#configuration) and [Environment Variables](#environment-variables).

---

## Configuration

For local development:

```env
DEBUG=true
API_KEY=dev-api-key-change-me
DASHBOARD_PASSWORD=dev-dashboard-password
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

For production, set `DEBUG=false` and provide strong secrets. The application refuses to start in production mode without `API_KEY` and `DASHBOARD_PASSWORD`.

---

## Quick Start

```bash
uvicorn main:app --reload
```

Verify the service:

```bash
curl http://127.0.0.1:8000/health
```

Example response:

```json
{
  "status": "ok",
  "database": "ok",
  "version": "1.1.0",
  "time": "2026-05-21T12:00:00+00:00"
}
```

---

## Creating a Project

Register a project key used by the tracker and APIs:

```bash
python create_project.py --name "My Site" --domain "example.com" --key "my-site"
```

---

## Tracker Integration

Add the tracker script to your site HTML. Use the same origin or configure CORS via `ALLOWED_ORIGINS`:

```html
<script
  src="https://analytics.example.com/static/tracker.js"
  data-project-key="my-site"
  data-backend-url="https://analytics.example.com"
></script>
```

The tracker automatically records a `pageview` when the page loads. If the backend is unavailable, the host page continues to work — requests fail silently.

---

## Tracking Custom Events

```javascript
window.LiteAnalytics.track("cta_click", { button: "pricing", plan: "pro" });
```

**Fields sent by default:**

| Field | Source |
|-------|--------|
| `path`, `title`, `referrer` | Page context |
| `visitor_id` | `localStorage` |
| `session_id` | `sessionStorage` |
| `screen_width`, `screen_height` | Screen API |
| `language`, `timezone` | Browser |

---

## Push Subscription Support

### 1. Configure VAPID keys

Generate a VAPID key pair and add to `.env`:

```env
VAPID_PUBLIC_KEY=your-public-key
VAPID_PRIVATE_KEY=your-private-key
VAPID_CLAIMS_SUB=mailto:admin@yourdomain.com
```

### 2. Expose the public key on your page

```html
<script
  src="https://analytics.example.com/static/tracker.js"
  data-project-key="my-site"
  data-backend-url="https://analytics.example.com"
  data-vapid-public-key="YOUR_VAPID_PUBLIC_KEY"
  data-sw-path="/sw.js"
></script>
```

### 3. Subscribe from your UI

```javascript
window.LiteAnalytics.subscribePush()
  .then(() => { /* subscription saved */ })
  .catch(() => { /* handle permission or network errors in your UI */ });
```

### 4. Service worker

Lite Analytics serves an example worker at `/sw.js` (`app/static/sw.js`).

If your PWA already registers a service worker for the same scope, merge push handlers from `app/static/sw.js` into your existing worker instead of registering a second worker.

**HTTPS** is required for Web Push in production (localhost is exempt in browsers).

---

## Dashboard

Open in a browser:

```
https://analytics.example.com/dashboard/my-site
```

**Authentication:**

- **HTTP Basic Auth** — `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD`
- **API key header** — `X-API-Key: <API_KEY>`

The dashboard requires credentials in production. In development (`DEBUG=true`), access may be open when secrets are not configured.

---

## API Reference

### Public endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service and database health |
| `POST` | `/api/track` | Record an analytics event |
| `POST` | `/api/push/subscribe` | Store a web push subscription |

**Rate limits (v1.1):**

| Endpoint | Limit |
|----------|-------|
| `POST /api/track` | 120 requests / minute / IP |
| `POST /api/push/subscribe` | 20 requests / hour / IP |

Exceeded limits return `429` with `{"detail": "Rate limit exceeded"}`.

**Bot filtering:** known crawler user agents receive `{"ok": true, "ignored": "bot"}` without storing an event.

### Private endpoints (require `X-API-Key`)

| Method | Path | Auth errors |
|--------|------|-------------|
| `GET` | `/api/stats/{project_key}` | `401` missing key, `403` invalid key |
| `POST` | `/api/push/send/{project_key}` | `401` missing key, `403` invalid key |

### Example: track an event

```bash
curl -X POST http://127.0.0.1:8000/api/track \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "my-site",
    "event_type": "pageview",
    "path": "/docs",
    "title": "Documentation",
    "visitor_id": "vis_abc",
    "session_id": "sess_xyz"
  }'
```

### Example: fetch project stats

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://127.0.0.1:8000/api/stats/my-site
```

### Example: send a push notification

```bash
curl -X POST http://127.0.0.1:8000/api/push/send/my-site \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "Update available", "body": "A new version is live.", "url": "/"}'
```

---

## Environment Variables

| Variable | Required (prod) | Description |
|----------|-----------------|-------------|
| `DEBUG` | — | `true` for development; `false` for production |
| `DATABASE_URL` | — | SQLAlchemy URL (default: `sqlite:///./analytics.db`) |
| `API_KEY` | Yes | Secret for private API routes and dashboard API-key auth |
| `ALLOWED_ORIGINS` | Recommended | Comma-separated CORS origins (no wildcard in production) |
| `DASHBOARD_USERNAME` | — | Basic Auth username (default: `admin`) |
| `DASHBOARD_PASSWORD` | Yes | Basic Auth password for dashboard |
| `VAPID_PUBLIC_KEY` | For push | Web Push public key |
| `VAPID_PRIVATE_KEY` | For push | Web Push private key |
| `VAPID_CLAIMS_SUB` | For push | VAPID subject (e.g. `mailto:admin@domain.com`) |
| `PUSH_MAX_FAIL_COUNT` | — | Deactivate subscription after N failures (default: `5`) |

See `.env.example` for a starter template.

---

## Security Notes

| Topic | Behavior |
|-------|----------|
| Production secrets | `API_KEY` and `DASHBOARD_PASSWORD` required when `DEBUG=false` |
| API authentication | Missing key → `401`; invalid key → `403` |
| CORS | Explicit `ALLOWED_ORIGINS`; no permissive wildcard in production |
| IP storage | Stored as SHA-256 hash only |
| Input validation | Field length limits and 20 KB payload cap |
| Dashboard | Jinja2 auto-escaping; no unsafe HTML output |
| Private routes | Stats, push send, and dashboard require authentication |

See [SECURITY.md](SECURITY.md) for the vulnerability reporting process and production hardening guidance.

---

## Performance Notes

- SQLite WAL mode is enabled for better concurrent read performance.
- Indexes are defined on common query columns (`project_id`, `created_at`, `event_type`, `path`, `visitor_id`).
- In-memory rate limiting applies per process; use edge rate limiting for multi-worker deployments.
- For higher traffic, plan a move to PostgreSQL (see Roadmap).

---

## Limitations

- SQLite only in v1.1 (PostgreSQL support planned)
- No multi-user admin UI for project management
- No built-in chart export or real-time streaming dashboard
- Push delivery requires `pywebpush`, valid VAPID keys, and HTTPS on client sites
- Project provisioning is CLI-based (`create_project.py`)
- In-memory rate limits do not synchronize across multiple worker processes

---

## Ethical Use

Lite Analytics Core is intended for **first-party analytics** on websites and applications you operate or administer.

- **Site owners** are responsible for compliance with applicable privacy laws and regulations (for example GDPR, CCPA, or local equivalents).
- **Consent requirements** vary by jurisdiction, use case, and data collected — consult qualified legal counsel when needed.
- **Disclosure** — inform visitors about analytics and push notifications where your policies or local law require it.
- **Transparent deployment** — the tracker is loaded explicitly by the site owner; there is no obfuscated or third-party relay layer in the default setup.

This software provides infrastructure; it does not replace legal review, privacy policies, or consent management platforms.

---

## Roadmap

- [ ] PostgreSQL support
- [ ] Admin UI for projects
- [x] Rate limiting and bot filtering (v1.1.0)
- [ ] Redis-backed rate limiting for multi-instance deployments
- [ ] Scheduled reports and webhooks
- [ ] Segment filters and funnels
- [ ] Per-project API tokens
- [ ] Docker Compose and Helm chart

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding expectations, and the pull request process.

Report security issues privately via [SECURITY.md](SECURITY.md).

---

## License

This project is licensed under the [GNU Affero General Public License v3.0 or later](LICENSE) (AGPL-3.0-or-later).

If you run a modified version as a network service, AGPL obligations may require you to provide corresponding source to users interacting with that service. Review the license text and consult legal counsel for your deployment model.
