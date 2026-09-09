# Meridian — Time, thoughtfully.

A responsive, privacy-friendly clock dashboard built with FastAPI and plain JavaScript. No account, database, frontend build, or third-party assets are required.

## What it does

- World clocks with dates, UTC offsets, 12/24-hour display, and up to 12 favorites.
- Search by city or timezone, filter by region, and browse 12, 24, or 48 clocks per page.
- One countdown timer from 1 second to 24 hours, with pause, resume, and reset.
- Up to 10 labeled, one-time alarms in the device's local timezone. Duplicate scheduled times and labels over 40 characters are rejected.
- Browser-local persistence, storage recovery, loading/error/empty states, keyboard focus indicators, and layouts down to 320px.

The directory uses the maintained `pytz.common_timezones` catalog. Exact timezone identifiers are preserved, including hyphens and nested city names. Clocks render with `Intl.DateTimeFormat` and synchronize to the server on load, every five minutes, and when returning to the tab; there is no per-clock polling. A failed sync falls back to visibly labeled device time.

## Run locally

Use Python 3.14 (the tested runtime):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8200
```

Open <http://127.0.0.1:8200>. See [SETUP.md](SETUP.md) for macOS/Linux, verification, and managed hosting.

## Verify before committing

Install development dependencies and Chromium once, with Node.js 22+ available:

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
npm ci
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python scripts/check.py
```

The release gate checks dependency consistency, Python lint/formatting, JavaScript syntax/formatting, logic tests, API tests, real Chromium flows, and Git whitespace. Browser tests start an isolated local server and use separate browser storage. Screenshots are saved in ignored `artifacts/`. GitHub Actions runs the same gate on pushes and pull requests. `AGENTS.md` instructs coding agents to commit completed, verified work locally; it is not a background watcher that commits every file save. Pushing remains manual.

## Alert behavior and privacy

Keep the page open and the device awake. Browser suspension, sleep, or closing the page prevents timely alerts; overdue alerts appear when the page runs again. Enable sound with the **Enable & test sound** button after opening or reloading the page. Visual alerts remain available without sound. These are convenience reminders, not a guaranteed delivery service.

Timers use stored device-clock deadlines, so delayed callbacks do not accumulate drift. Changing the device's clock can change their remaining time. Alarm times are resolved using the device's timezone when created and stored as fixed instants; a later timezone change does not reschedule them. Past times schedule tomorrow. A local time skipped by daylight saving is rejected; a repeated local time uses JavaScript's first occurrence.

Favorites, display preferences, timer state, and alarm labels stay in local storage on this browser and origin. Clearing site data removes them. Storage-disabled browsers can use the current tab but cannot persist changes. Same-origin tabs synchronize saved state; simultaneous edits use the most recent write, and multiple open tabs can each show an alert. Use one tab if you want a single sound alert. No cross-device sync or background notification service is provided.

The app requires a current browser with JavaScript, Intl timezone data, Web Audio (for sound), and AbortSignal timeout/any support. Automated browser coverage currently uses Chromium. Verify any other target browsers on staging before launch.

## Read-only API

| Endpoint | Behavior |
| --- | --- |
| `GET /health` | Liveness response: `{"status":"ok"}` |
| `GET /api/time` | UTC epoch milliseconds; never cached |
| `GET /api/timezones` | `zones`, `regions`, `total`, `page`, `page_size`, `pages` |
| `GET /api/world-clock/{timezone}` | Time, date, and ISO timestamp with UTC offset; unknown identifiers return 404 |

Catalog parameters: `q` (maximum 80 characters), `region` (one of the returned regions), `page` (1–10000), and `page_size` (12, 24, or 48). Invalid parameters return 422; nonexistent pages return 404. Empty searches return an empty first page. The old unbounded timezone response has intentionally changed to pagination. Catalog responses can be cached for five minutes. The OpenAPI schema remains at `/openapi.json`; interactive API documentation is disabled to keep the site's content security policy restricted to local assets.

## Release status

This repository includes a tested first-release implementation and managed-host instructions. It has not been deployed or load-tested against a live host. HTTPS, health monitoring, edge rate limits, host configuration, and a staging smoke test are deployment responsibilities described in [SETUP.md](SETUP.md).
