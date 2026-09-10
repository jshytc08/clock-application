"""Real browser regression checks; each test gets isolated browser storage."""

import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from playwright.sync_api import expect, sync_playwright

from scripts.build_pages import build_pages

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module", params=["server", "static"])
def base_url(request, tmp_path_factory):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    if request.param == "static":
        site_root = tmp_path_factory.mktemp("pages")
        build_pages(site_root / "clock-application")
        command = [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
            "--directory",
            str(site_root),
        ]
        suffix = "/clock-application/"
    else:
        command = [sys.executable, "-m", "app.main"]
        suffix = ""
    process = subprocess.Popen(
        command,
        env={**os.environ, "PORT": str(port), "ALLOWED_HOSTS": "127.0.0.1"},
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}{suffix}"
    try:
        for _ in range(100):
            try:
                with urlopen(url if suffix else f"{url}/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except URLError:
                if process.poll() is not None:
                    pytest.fail("Test server exited before becoming healthy")
                time.sleep(0.1)
        else:
            pytest.fail("Test server did not start")
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@pytest.fixture(scope="module")
def playwright():
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="module", params=["chromium", "webkit"])
def browser(playwright, request):
    browser = getattr(playwright, request.param).launch()
    yield browser
    browser.close()


@pytest.fixture(params=["desktop", "phone"])
def page(browser, playwright, request):
    device = (
        {"viewport": {"width": 1440, "height": 1050}}
        if request.param == "desktop"
        else {**playwright.devices["iPhone 13"], "device_scale_factor": 1}
    )
    context = browser.new_context(**device, timezone_id="Asia/Manila", reduced_motion="reduce")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    yield page
    context.close()
    assert not errors, errors


def open_app(page, base_url):
    page.goto(base_url)
    expect(page.locator("#clock-grid .clock-card")).to_have_count(12)


def capture(page, base_url, state, *, full_page=True):
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    hosting = "pages" if "/clock-application/" in base_url else "server"
    engine = page.context.browser.browser_type.name
    profile = str(page.viewport_size["width"])
    page.screenshot(
        path=str(artifacts / f"{engine}-{profile}-{hosting}-{state}.png"),
        full_page=full_page,
    )


def assert_mobile_controls(page):
    small_fields = page.locator("input, select").evaluate_all("""elements => elements
      .filter(el => parseFloat(getComputedStyle(el).fontSize) < 16).map(el => el.id)""")
    assert not small_fields, f"Mobile fields need readable 16px text: {small_fields}"
    small_targets = page.locator("button, .topbar a").evaluate_all("""elements => elements
      .filter(el => el.getClientRects().length && !el.disabled)
      .filter(el => {const r = el.getBoundingClientRect(); return r.width < 44 || r.height < 44})
      .map(el => el.id || el.getAttribute('aria-label') || el.textContent)""")
    assert not small_targets, f"Touch targets must be at least 44px: {small_targets}"


def test_catalog_search_pagination_and_no_per_clock_polling(page, base_url):
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    open_app(page, base_url)
    first = page.locator("#clock-grid h3").first.inner_text()
    page.get_by_role("button", name="Next →").click()
    expect(page.locator("#page-number")).to_have_text(re.compile(r"Page 2 of \d+"))
    assert page.locator("#clock-grid h3").first.inner_text() != first
    page.locator("#searchInput").fill("Port-au-Prince")
    expect(page.locator("#clock-grid .clock-card")).to_have_count(1)
    expect(page.locator("#clock-grid h3")).to_have_text("Port-au-Prince")
    expect(page.locator("#clock-grid .clock-time")).not_to_have_text("--:--:--")
    page.locator("#searchInput").fill("new york")
    expect(page.locator("#clock-grid h3")).to_have_text("New York")
    page.locator("#searchInput").fill("zzzzzzzz")
    expect(page.locator("#no-results")).to_be_visible()
    capture(page, base_url, "empty-search")
    page.locator("#clear-search").click()
    page.locator("#page-size").select_option("48")
    expect(page.locator("#clock-grid .clock-card")).to_have_count(48)
    page.locator("#regionSelect").select_option("Asia")
    expect(page.locator("#clock-grid .clock-card").first).to_have_attribute(
        "data-zone", "Asia/Aden"
    )
    page.clock.install()
    page.clock.fast_forward(5000)
    assert not any("/api/world-clock/" in url for url in requests)
    if "/clock-application/" in base_url:
        assert not any("/api/" in url for url in requests)
        expect(page.locator("#sync-status")).to_have_text("● Device time")


def test_favorite_limit_persistence_and_hour_format(page, base_url):
    open_app(page, base_url)
    for _ in range(8):
        page.locator("#clock-grid .star[aria-pressed=false]").first.click()
    expect(page.locator("#favorites-grid .clock-card")).to_have_count(12)
    page.locator("#clock-grid .star[aria-pressed=false]").first.click()
    expect(page.locator("#favorite-message")).to_contain_text("12 favorites")
    page.locator("#hour-format").click()
    page.reload()
    expect(page.locator("#favorites-grid .clock-card")).to_have_count(12)
    expect(page.locator("#hour-format")).to_have_text("12-hour")
    page.locator("#favorites-grid .star").first.click()
    expect(page.locator("#favorites-grid .clock-card")).to_have_count(11)


def test_timer_validation_pause_reload_resume_and_single_completion(page, base_url):
    open_app(page, base_url)
    page.clock.install()
    page.locator("#timer-minutes").fill("0")
    page.locator("#timer-start").click()
    expect(page.locator("#timer-error")).to_contain_text("between 1 second and 24 hours")
    page.locator("#timer-error").scroll_into_view_if_needed()
    capture(page, base_url, "timer-error", full_page=False)
    page.locator("#timer-seconds").fill("2")
    page.locator("#timer-start").click()
    expect(page.locator("#timer-hours")).to_be_disabled()
    page.locator("#timer-pause").click()
    page.reload()
    expect(page.locator("#timer-start")).to_have_text("Resume timer")
    page.locator("#timer-start").click()
    page.clock.fast_forward(2500)
    expect(page.locator("#alert-dialog")).to_be_visible()
    expect(page.locator("#alert-messages")).to_contain_text("focus timer is complete")
    capture(page, base_url, "timer-alert", full_page=False)
    page.locator("#dismiss-alert").click()
    page.clock.fast_forward(5000)
    expect(page.locator("#alert-dialog")).not_to_be_visible()
    page.reload()
    expect(page.locator("#alert-dialog")).not_to_be_visible()


def test_alarms_validation_duplicate_limit_safe_labels_and_due_delivery(page, base_url):
    open_app(page, base_url)
    page.clock.install()
    page.locator("#alarm-add").click()
    expect(page.locator("#alarm-error")).to_contain_text("valid alarm time")
    page.locator("#alarm-error").scroll_into_view_if_needed()
    capture(page, base_url, "alarm-error", full_page=False)
    times = page.evaluate("""() => Array.from({length: 10}, (_, index) => {
      const date = new Date(Date.now() + (index + 2) * 60000);
      return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    })""")
    label = "<img src=x onerror=alert(1)>"
    page.locator("#alarm-time").fill(times[0])
    page.locator("#alarm-label").fill(label)
    page.locator("#alarm-add").click()
    expect(page.locator("#alarm-list strong")).to_have_text(label)
    assert page.locator("#alarm-list img").count() == 0
    page.locator("#alarm-add").click()
    expect(page.locator("#alarm-error")).to_contain_text("already scheduled")
    for alarm_time in times[1:]:
        page.locator("#alarm-time").fill(alarm_time)
        page.locator("#alarm-add").click()
    expect(page.locator("#alarm-add")).to_be_disabled()
    page.reload()
    expect(page.locator("#alarm-list li")).to_have_count(10)
    page.clock.fast_forward(120000)
    expect(page.locator("#alert-dialog")).to_be_visible()
    expect(page.locator("#alert-messages")).to_contain_text(label)
    expect(page.locator("#alarm-list li")).to_have_count(9)
    page.locator("#dismiss-alert").click()
    page.locator("#alarm-list button").first.click()
    expect(page.locator("#alarm-list li")).to_have_count(8)


def test_network_failure_retry_and_corrupt_storage(page, base_url):
    page.add_init_script("localStorage.setItem('meridian.v1', '{broken');")
    catalog_route = (
        "**/static/data/timezones.json"
        if "/clock-application/" in base_url
        else "**/api/timezones?*"
    )
    page.route(catalog_route, lambda route: route.abort())
    page.goto(base_url)
    expect(page.locator("#storage-notice")).to_be_visible()
    expect(page.locator("#catalog-error")).to_be_visible()
    expect(page.locator("#next-page")).to_be_disabled()
    page.locator("#catalog-error").scroll_into_view_if_needed()
    capture(page, base_url, "network-storage-error", full_page=False)
    page.unroute(catalog_route)
    page.locator("#retry").click()
    expect(page.locator("#clock-grid .clock-card")).to_have_count(12)


def test_blocked_storage_and_failed_sync_remain_usable(page, base_url):
    page.add_init_script(
        "Object.defineProperty(window, 'localStorage', {get() {throw new Error('blocked')}});"
    )
    page.route("**/api/time", lambda route: route.abort())
    open_app(page, base_url)
    expect(page.locator("#sync-status")).to_contain_text("Device time")
    page.locator("#hour-format").click()
    expect(page.locator("#hour-format")).to_have_text("12-hour")
    expect(page.locator("#storage-notice")).to_contain_text("unavailable")
    page.locator("#storage-notice").scroll_into_view_if_needed()
    capture(page, base_url, "storage-unavailable", full_page=False)


def test_responsive_layout_labels_keyboard_and_screenshots(page, base_url):
    open_app(page, base_url)
    capture(page, base_url, "initial")
    assert page.locator("input, select").evaluate_all(
        "(elements) => elements.every(el => el.labels.length > 0)"
    )
    initial_width = page.viewport_size["width"]
    if initial_width > 700:
        page.locator("body").click(position={"x": 2, "y": 2})
        page.keyboard.press("Tab")
        expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
        page.keyboard.press("Enter")
        expect(page.locator("#main")).to_be_focused()
    page.locator("#hero-title").click()
    for width, height in ((320, 844), (390, 844), (430, 932), (844, 390), (768, 1024)):
        page.set_viewport_size({"width": width, "height": height})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        capture(page, base_url, f"from-{initial_width}-layout-{width}")
        if width <= 700:
            assert_mobile_controls(page)


def test_narrow_long_content_and_short_viewport_alert(page, base_url):
    page.set_viewport_size({"width": 320, "height": 640})
    open_app(page, base_url)
    page.locator("#hour-format").click()
    page.locator("#searchInput").fill("Argentina")
    expect(page.locator("#clock-grid h3").first).to_be_visible()
    assert page.locator(".clock-card, .local-clock").evaluate_all(
        "elements => elements.every(el => el.scrollWidth <= el.clientWidth)"
    )
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    capture(page, base_url, "long-cities-12-hour")
    page.locator("#alarm-time").fill("23:59")
    page.locator("#alarm-label").fill("A" * 40)
    page.locator("#alarm-add").click()
    expect(page.locator("#alarm-list strong")).to_have_text("A" * 40)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.clock.install()
    page.locator("#timer-minutes").fill("0")
    page.locator("#timer-seconds").fill("1")
    page.locator("#timer-start").click()
    page.clock.fast_forward(1500)
    page.set_viewport_size({"width": 390, "height": 320})
    expect(page.locator("#alert-dialog")).to_be_visible()
    page.locator("#dismiss-alert").scroll_into_view_if_needed()
    expect(page.locator("#dismiss-alert")).to_be_in_viewport()
    capture(page, base_url, "short-viewport-alert", full_page=False)
    page.locator("#dismiss-alert").click()
    expect(page.locator("#alert-dialog")).not_to_be_visible()


def test_catalog_loading_and_navigation(page, base_url):
    pending = []
    catalog_route = (
        "**/static/data/timezones.json"
        if "/clock-application/" in base_url
        else "**/api/timezones?*"
    )
    page.route(catalog_route, lambda route: pending.append(route))
    page.goto(base_url, wait_until="domcontentloaded")
    expect(page.locator("#clock-grid")).to_have_attribute("aria-busy", "true")
    expect(page.locator("#catalog-status")).to_contain_text("Loading")
    page.locator("#catalog-status").scroll_into_view_if_needed()
    capture(page, base_url, "loading", full_page=False)
    assert pending
    for route in pending:
        route.continue_()
    page.unroute(catalog_route)
    expect(page.locator("#clock-grid .clock-card")).to_have_count(12)
    page.get_by_role("link", name="Meridian home").scroll_into_view_if_needed()
    navigation = page.get_by_role("link", name="Timer & alarms", exact=True)
    if page.viewport_size["width"] <= 700:
        navigation.tap()
    else:
        navigation.click()
    expect(page.locator("#tools-title")).to_be_in_viewport()


def test_configured_host_restrictions_reject_untrusted_requests(base_url):
    from urllib.error import HTTPError
    from urllib.request import Request

    if "/clock-application/" in base_url:
        pytest.skip("Host restrictions belong to FastAPI; Pages supplies its own hosting layer.")
    request = Request(f"{base_url}/health", headers={"Host": "untrusted.example"})
    with pytest.raises(HTTPError) as error:
        urlopen(request, timeout=2)
    assert error.value.code == 400


def test_sound_opt_in_and_timer_reset(page, base_url):
    open_app(page, base_url)
    sound = page.locator("#enable-sound")
    if page.viewport_size["width"] <= 700:
        sound.tap()
    else:
        sound.click()
    if sys.platform == "win32" and page.context.browser.browser_type.name == "webkit":
        # Windows Playwright WebKit has no Web Audio implementation. Assert the
        # actual capability and the app's fallback; other platforms must enable it.
        assert page.evaluate("typeof AudioContext") == "undefined"
        expect(page.locator("#sound-status")).to_contain_text("Sound is unavailable")
    else:
        expect(page.locator("#sound-status")).to_contain_text("Sound enabled")
    capture(page, base_url, "sound-status", full_page=False)
    page.locator("#timer-start").click()
    page.locator("#timer-reset").click()
    expect(page.locator("#timer-hours")).to_be_enabled()
    expect(page.locator("#timer-display")).to_have_text("00:25:00")
    assert page.evaluate("JSON.parse(localStorage.getItem('meridian.v1')).timer") is None
