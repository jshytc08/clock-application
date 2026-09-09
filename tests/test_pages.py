import json

import pytz

from scripts.build_pages import build_pages


def test_static_export_contains_only_public_web_assets(tmp_path):
    output = build_pages(tmp_path / "clock-application")
    files = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
    assert files == {
        "index.html",
        ".nojekyll",
        "static/favicon.svg",
        "static/css/style.css",
        "static/js/core.mjs",
        "static/js/main.js",
        "static/js/catalog.mjs",
        "static/data/timezones.json",
    }
    html = (output / "index.html").read_text(encoding="utf-8")
    assert 'data-hosting="static"' in html
    assert "Content-Security-Policy" in html
    assert "frame-ancestors" not in html
    assert '"/static/' not in html
    assert '"./static/js/main.js"' in html
    assert json.loads((output / "static/data/timezones.json").read_text()) == sorted(
        pytz.common_timezones
    )
