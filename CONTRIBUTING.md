# Contributing to Lite Analytics Core

Thank you for your interest in contributing. This project welcomes bug reports, documentation improvements, and focused feature proposals.

## Code of Conduct

Be respectful and constructive. Assume good intent. Keep discussions technical and actionable.

## Local Development Setup

### Requirements

- Python 3.10 or newer
- Git

### Setup

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

Edit `.env` for local development. A minimal configuration:

```env
DEBUG=true
API_KEY=dev-api-key-change-me
DASHBOARD_PASSWORD=dev-dashboard-password
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Run the application

```bash
uvicorn main:app --reload
```

Verify the health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

### Create a test project

```bash
python create_project.py --name "Demo" --domain "localhost" --key "demo"
```

## Running Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

All tests should pass before opening a pull request.

## Coding Style Expectations

- Match existing project structure and naming conventions.
- Keep changes focused; avoid unrelated refactors in the same PR.
- Prefer clear, self-explanatory code over excessive comments.
- Use the centralized logger (`app.logger`) instead of `print()` in application code.
- Do not commit secrets, database files, or local environment files.
- Preserve existing API routes and response contracts unless the issue explicitly requires a breaking change (breaking changes require discussion first).

## Project Structure

```
app/
  config.py           # Environment settings
  db.py               # SQLAlchemy engine and sessions
  models.py           # Database models
  schemas.py          # Pydantic API models
  deps.py             # Auth and request helpers
  logger.py           # Logging configuration
  version.py          # Application version
  routes/             # HTTP endpoints
  services/           # Business logic
  security/           # Rate limiting and related controls
  templates/          # Dashboard HTML (Jinja2)
  static/             # tracker.js, service worker, CSS
main.py               # FastAPI entrypoint
create_project.py     # CLI project initializer
tests/                # Pytest suite
```

## Contribution Workflow

1. **Search existing issues** to avoid duplicate work.
2. **Open an issue** for significant changes before implementing large features.
3. **Fork** the repository and create a feature branch from `main`.
4. **Implement** your change with tests where applicable.
5. **Run pytest** and verify the app starts locally.
6. **Open a pull request** using the PR template.

## Pull Request Process

- Fill in the pull request template completely.
- Link related issues (`Fixes #123` when applicable).
- Ensure CI/tests pass (or document why they cannot).
- Be responsive to review feedback.

Small documentation-only PRs are welcome and appreciated.

## Commit Message Recommendations

Use clear, imperative subject lines:

```
Add PostgreSQL connection pooling option
Fix dashboard escaping for referrer field
Document rate limit headers in README
```

Optional body: explain **why** the change is needed, not only **what** changed.

## Questions

Open a GitHub Discussion or issue for questions that are not security-sensitive. For vulnerabilities, see [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions will be licensed under the [GNU Affero General Public License v3.0 or later](LICENSE).
