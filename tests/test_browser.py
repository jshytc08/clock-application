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

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def base_url():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        env={**os.environ, "PORT": str(port), "ALLOWED_HOSTS": "127.0.0.1"},
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                with urlopen(f"{url}/health", timeout=1) as response:
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
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(
        viewport={"width": 1440, "height": 1050}, timezone_id="Asia/Manila"
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    yield page
    context.close()
    assert not errors, errors


def open_app(page, base_url):
    page.goto(base_url)
    expect(page.locator("#clock-grid .clock-card")).to_have_count(12)


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
    page.route("**/api/timezones?*", lambda route: route.abort())
    page.goto(base_url)
    expect(page.locator("#storage-notice")).to_be_visible()
    expect(page.locator("#catalog-error")).to_be_visible()
    expect(page.locator("#next-page")).to_be_disabled()
    page.unroute("**/api/timezones?*")
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


def test_responsive_layout_labels_keyboard_and_screenshots(page, base_url):
    open_app(page, base_url)
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    page.screenshot(path=str(artifacts / "desktop.png"), full_page=True)
    assert page.locator("input, select").evaluate_all(
        "(elements) => elements.every(el => el.labels.length > 0)"
    )
    page.keyboard.press("Control+Home")
    page.locator("body").click(position={"x": 2, "y": 2})
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
    page.locator("#hero-title").click()
    for width in (390, 320):
        page.set_viewport_size({"width": width, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(artifacts / f"mobile-{width}.png"), full_page=True)


def test_configured_host_restrictions_reject_untrusted_requests(base_url):
    from urllib.error import HTTPError
    from urllib.request import Request

    request = Request(f"{base_url}/health", headers={"Host": "untrusted.example"})
    with pytest.raises(HTTPError) as error:
        urlopen(request, timeout=2)
    assert error.value.code == 400


def test_sound_opt_in_and_timer_reset(page, base_url):
    open_app(page, base_url)
    page.locator("#enable-sound").click()
    expect(page.locator("#sound-status")).to_contain_text("Sound enabled")
    page.locator("#timer-start").click()
    page.locator("#timer-reset").click()
    expect(page.locator("#timer-hours")).to_be_enabled()
    expect(page.locator("#timer-display")).to_have_text("00:25:00")
    assert page.evaluate("JSON.parse(localStorage.getItem('meridian.v1')).timer") is None
