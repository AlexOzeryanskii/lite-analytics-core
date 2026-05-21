# Security Policy

## Supported Versions

Security fixes are provided for the latest stable release branch.

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| < 1.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

**Do not** open a public GitHub issue for security-sensitive reports.

Instead, use one of the following channels:

1. **GitHub Security Advisories** (preferred): use the **Report a vulnerability** button on the repository Security tab.
2. **Private contact**: email the maintainers if a security advisory workflow is not yet configured.

Include as much detail as possible:

- Affected version
- Steps to reproduce
- Impact assessment
- Suggested remediation (if available)

## Responsible Disclosure

We aim to:

1. Acknowledge receipt within **5 business days**
2. Provide an initial assessment within **14 business days**
3. Coordinate a fix and release timeline before public disclosure
4. Credit reporters in the release notes when appropriate (unless you prefer anonymity)

Please allow reasonable time for remediation before public disclosure.

## Production Security Recommendations

Lite Analytics Core is designed for **self-hosted, first-party** deployments. Operators are responsible for securing their infrastructure.

### HTTPS

- Serve the application and client sites over **HTTPS** in production.
- Terminate TLS at a reverse proxy (nginx, Caddy, Traefik) with modern cipher suites.
- Web Push requires HTTPS on client origins (browser requirement).

### Secrets

- Set `DEBUG=false` in production.
- Use long, random values for `API_KEY` and `DASHBOARD_PASSWORD`.
- Never commit `.env` files or secrets to version control.
- Rotate credentials if exposure is suspected.

### CORS

- Set `ALLOWED_ORIGINS` to an explicit comma-separated list of trusted origins.
- Do not rely on permissive defaults in production.

### Database

- Restrict filesystem and network access to the database file or server.
- Perform **regular backups** of `analytics.db` (or your configured database).
- Test restore procedures periodically.

### VAPID Keys

- Generate **unique VAPID key pairs** per environment (development, staging, production).
- Store private keys only on the server; expose only the public key to client pages.
- Rotate keys if compromise is suspected and re-subscribe clients as needed.

### Rate Limiting

- v1.1.0 includes in-process IP rate limits on public endpoints.
- For multi-worker or multi-instance deployments, add edge rate limiting (reverse proxy, WAF, or Redis-backed limiter).

### Network Exposure

- Keep private endpoints (`/api/stats`, `/api/push/send`, `/dashboard`) off the public internet where possible, or protect them with VPN, IP allowlists, or mutual TLS in addition to application auth.

## Additional Hardening

- Run the application as a non-root user.
- Keep Python dependencies updated.
- Monitor logs for repeated `429`, validation failures, and database errors.
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for secure local development practices.
