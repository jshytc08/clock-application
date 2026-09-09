"""Export only public web assets for static hosting, including project subpaths."""

import json
import shutil
from pathlib import Path

import pytz

ROOT = Path(__file__).resolve().parents[1]


def build_pages(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    source = ROOT / "app"
    html = (source / "templates/index.html").read_text(encoding="utf-8-sig")
    assert 'data-hosting="server"' in html, "Missing hosting mode marker"
    html = html.replace('data-hosting="server"', 'data-hosting="static"', 1)
    policy = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self'; connect-src 'self'; font-src 'self'; "
        "object-src 'none'; base-uri 'none'; form-action 'self'"
    )
    html = html.replace(
        "<head>",
        "<head>\n"
        f'    <meta http-equiv="Content-Security-Policy" content="{policy}" />\n'
        '    <meta name="referrer" content="strict-origin-when-cross-origin" />',
        1,
    )
    (destination / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(source / "static", destination / "static", dirs_exist_ok=True)
    data = destination / "static/data"
    data.mkdir(exist_ok=True)
    (data / "timezones.json").write_text(
        json.dumps(sorted(pytz.common_timezones)), encoding="utf-8"
    )
    (destination / ".nojekyll").write_text("", encoding="utf-8")
    return destination


if __name__ == "__main__":
    # Require a fresh output folder so stale or unrelated files cannot be published.
    output = ROOT / "dist"
    if output.exists():
        raise SystemExit(
            "dist/ already exists. Use a fresh checkout or move that folder before rebuilding."
        )
    build_pages(output)
    print(f"Static site built in {output}")
