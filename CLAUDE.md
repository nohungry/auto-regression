# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

End-to-end regression test suite for a gaming platform (T9 Platform) using Python + pytest-playwright. Tests run against a live site via a Chrome browser, either locally or via CDP (Chrome DevTools Protocol) when running from WSL.

## Setup

```bash
cp .env.example .env   # Fill in credentials and CDP_URL
pip install -r requirements.txt
playwright install chromium
```

Key `.env` variables:
- `DEFAULT_SITE` — which site config to use (e.g. `drc`)
- `CDP_URL` — Chrome remote debug URL (WSL/Linux only; e.g. `http://<WINDOWS_IP>:9223`)
- `SITE_<NAME>_URL/USERNAME/PASSWORD` — per-site credentials

## Running Tests

```bash
pytest                                                        # all tests
pytest --site=drc                                             # specific site
pytest -m p0                                                  # by marker
pytest -m login                                               # by marker
pytest tests/test_p0_smoke.py::TestLogin::test_login_success  # single test
```

Reports are written to `reports/report.html` (self-contained HTML).

## Architecture

```
conftest.py          — browser setup, environment detection (Windows/WSL/Linux), global fixtures
config/settings.py   — multi-site SiteConfig dataclass loaded from .env
pages/               — Page Object Model: LoginPage, HomePage
tests/               — test classes (TC-001 to TC-022 in test_p0_smoke.py)
utils/dialog_helper.py — shared helper for dismissing server error popups
```

**Environment detection** in `conftest.py`: detects WSL vs Windows vs Linux, auto-starts Windows Chrome over CDP if needed, injects a MutationObserver to auto-close server error popups.

**Fixtures** (conftest.py):
- `site_config` (session-scoped) — loads credentials for the selected site
- `page` (function-scoped) — fresh browser context per test, window maximized
- `logged_in_page` — pre-authenticated page for tests that require login
- `auto_logout_after_test` — cleanup after each test

**Markers** (pytest.ini): `p0`, `p1`, `p2`, `login`, `home`

## Adding Tests / Sites

- New page objects go in `pages/`, following the existing POM pattern.
- New sites: add `SITE_XXX_URL`, `SITE_XXX_USERNAME`, `SITE_XXX_PASSWORD` to `.env`.
- New test markers must be declared in `pytest.ini` under `markers`.
