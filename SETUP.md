# Setup and deployment

## Development

Python 3.14 is the tested runtime. Node.js 22+ is needed only for development checks; production serves the committed static files directly.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
npm ci
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8200
```

macOS/Linux:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm ci
python -m playwright install --with-deps chromium
python -m uvicorn app.main:app --reload --port 8200
```

Run the release gate with the virtual environment's Python:

```bash
python scripts/check.py
```

On Windows without activation, use `.venv\Scripts\python scripts/check.py`. To format changes, run `npm run format` and `python -m ruff format app tests scripts`. Keep intentional dependency pins in `requirements.txt`; do not replace them with an unrelated development environment's `pip freeze` output.

## Managed Python web service

Connect this repository to your managed host as a Python web service, using:

| Setting | Value |
| --- | --- |
| Python | 3.14, also recorded in `.python-version` |
| Build command | `python -m pip install -r requirements.txt` |
| Start command | `python -m app.main` |
| Health check path | `/health` |
| Port | Host-provided `PORT`; defaults to 8200 locally |
| Storage | No persistent server disk or database required |

`Procfile` provides the same start command for hosts that recognize it. The entry point binds to `0.0.0.0`, reads `PORT`, and runs without development reload. Begin with one process and scale using the host's service controls after measuring traffic. The API is stateless, so replicas do not share user data.

Set `ALLOWED_HOSTS` to a comma-separated list of the public hostnames and any hostnames used by the platform's health checker, for example `clock.example.com,service.provider.example,localhost,127.0.0.1`. Include hostnames only, without schemes or paths. An unset value permits arbitrary Host headers for local development. A configured unexpected host is rejected with HTTP 400.

Have the platform terminate HTTPS and redirect HTTP. Apply HSTS at the HTTPS edge once the domain is configured. The app supplies a local-assets-only content security policy, frame restrictions, no-sniff headers, and restrictive camera/microphone/geolocation permissions. Set edge request-size, connection, and rate limits using the host's controls; this app does not implement a process-local rate limiter that would fail across replicas. Static assets contain no secrets or account data.

Enable automatic service restarts, health monitoring, and log retention using your host's controls. Review access-log retention: search terms may appear in API request URLs. Build and dependency installation failures should block deployment. Keep the previous successful release available for rollback. Browser storage is tied to the site's origin, so changing domains does not transfer saved preferences.

## Before opening the production URL to users

1. Run `python scripts/check.py` and let CI pass on the exact release commit.
2. Run dependency audits against current advisories (`python -m pip install pip-audit`, then `python -m pip_audit -r requirements.txt`; `npm audit` covers development JavaScript dependencies). Fix reported findings and re-run the release gate before deploying.
3. Deploy to staging and verify `/health`, HTTPS, allowed hosts, mobile and desktop layouts, all page sizes, search, favorites after reload, invalid timer inputs, pause/resume, one timer completion, and one audible alarm. Exercise sound on the devices and browsers you support.
4. Measure response times and error rates under anticipated concurrent traffic. Choose capacity and edge limits from those measurements; local test success is not a capacity guarantee.
5. Confirm monitoring and rollback, then promote the tested release through your host's deployment controls.

No hosting account has been configured and no production deployment is performed by these files. CI results become available after you push.

## Operational limits

Alarms require the page to run and the device to be awake. Browser timer throttling and audio permissions still apply; the UI states these limits. Native/background alarm delivery would require a different delivery system and is outside this release. The app periodically estimates server time using request round-trip time; it is not a precision time synchronization service.

See the official [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/), [Uvicorn deployment documentation](https://uvicorn.dev/deployment/), and [MDN timer behavior](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout) for the underlying hosting and browser constraints.
