# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-21

### Added

- IP-based rate limiting for `POST /api/track` (120 req/min) and `POST /api/push/subscribe` (20 req/hour)
- Bot filtering for common crawlers and SEO bots
- Pydantic field length validation and 20 KB payload size limit
- Database indexes on `events.path` and `push_subscriptions.is_active`
- Extended `/health` endpoint with database check, version, and timestamp
- Centralized logging subsystem (`app/logger.py`)
- Tracker SDK hardening (silent failures, fetch fallback)
- API key distinction: `401` for missing key, `403` for invalid key
- Test suite for v1.1 hardening features

### Security

- Dashboard template audit (Jinja2 auto-escaping confirmed)
- Input validation to prevent oversized database records

## [0.1.0] - Initial MVP

### Added

- FastAPI application with SQLite storage
- Event ingestion (`POST /api/track`)
- Web push subscription storage and send API
- Protected stats API and dashboard
- Vanilla `tracker.js` embed
- Project CLI (`create_project.py`)

[1.1.0]: https://github.com/YOUR_ORG/LiteAnalytics/releases/tag/v1.1.0
[0.1.0]: https://github.com/YOUR_ORG/LiteAnalytics/releases/tag/v0.1.0
