"""Run the bounded accessibility and privacy smoke for the static explorer."""

from __future__ import annotations

import argparse
import re
from collections.abc import Sequence
from urllib.parse import urlsplit, urlunsplit

SAFETY_ZH = "本頁僅使用固定合成資料作研究展示；不提供個案風險、診斷、治療或照護決策。"
VIEWPORTS = (("desktop", 1440, 900), ("mobile", 390, 844))
PROHIBITED_VISIBLE_TERMS = (
    "score",
    "probability",
    "threshold",
    "metric",
    "model",
    "recommendation",
    "prognosis",
)
EVENT_PATH_PARTS = ("/gradio_api/call", "/gradio_api/queue", "/gradio_api/upload")


def _contrast_ratio(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(value) / 255 for value in re.findall(r"\d+", color)[:3]]
        if len(channels) != 3:
            raise ValueError("computed_color_invalid")
        linear = [
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def validate_target_url(url: str) -> str:
    """Return a normalized HTTP(S) URL with no credential/query ambiguity."""

    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("target_url_invalid")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))


def _is_matching_hf_platform_lookup(url: str, expected_origin: str) -> bool:
    requested = urlsplit(url)
    target = urlsplit(expected_origin)
    target_host = target.hostname or ""
    if target.scheme != "https" or not target_host.endswith(".hf.space"):
        return False
    subdomain = target_host.removesuffix(".hf.space")
    return (
        bool(subdomain)
        and requested.scheme == "https"
        and requested.hostname == "huggingface.co"
        and requested.port is None
        and requested.username is None
        and requested.password is None
        and requested.path == f"/api/spaces/by-subdomain/{subdomain}"
        and not requested.query
        and not requested.fragment
    )


def request_violation(method: str, url: str, expected_origin: str) -> str | None:
    """Classify browser traffic that exceeds the read-only same-origin boundary."""

    parsed = urlsplit(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if method.upper() == "POST":
        return "post_request"
    if method.upper() == "GET" and _is_matching_hf_platform_lookup(url, expected_origin):
        return None
    if origin != expected_origin:
        return "external_request"
    if any(part in parsed.path.casefold() for part in EVENT_PATH_PARTS):
        return "event_transport"
    return None


def _run_viewport(browser: object, target_url: str, name: str, width: int, height: int) -> None:
    from playwright.sync_api import Browser, ConsoleMessage, Error, Page, Request

    typed_browser = browser
    if not isinstance(typed_browser, Browser):
        raise TypeError("browser_type_invalid")
    context = typed_browser.new_context(viewport={"width": width, "height": height})
    page: Page = context.new_page()
    parsed = urlsplit(target_url)
    expected_origin = f"{parsed.scheme}://{parsed.netloc}"
    violations: list[str] = []
    console_errors: list[str] = []
    page_errors: list[str] = []

    def record_request(request: Request) -> None:
        violation = request_violation(request.method, request.url, expected_origin)
        if violation:
            violations.append(f"{violation}:{request.method}:{request.url}")

    def record_console(message: ConsoleMessage) -> None:
        if message.type == "error":
            console_errors.append(message.text)

    def record_page_error(error: Error) -> None:
        page_errors.append(str(error))

    page.on("request", record_request)
    page.on("console", record_console)
    page.on("pageerror", record_page_error)
    try:
        response = page.goto(target_url, wait_until="networkidle", timeout=45_000)
        if response is None or not response.ok:
            raise AssertionError(f"{name}:navigation_failed")
        raw_html = response.body().decode("utf-8")
        if not re.search(r'<html\b[^>]*\blang="zh-TW"', raw_html):
            raise AssertionError(f"{name}:raw_document_language_invalid")
        shell = page.locator(".cr-shell")
        shell.wait_for(state="visible", timeout=20_000)
        if page.locator(".cr-shell h1").count() != 1:
            raise AssertionError(f"{name}:h1_count_invalid")
        if page.locator("html").get_attribute("lang") != "zh-TW":
            raise AssertionError(f"{name}:language_invalid")
        if page.get_by_text(SAFETY_ZH, exact=True).count() != 1:
            raise AssertionError(f"{name}:safety_copy_missing")
        safety_first = page.evaluate(
            """() => {
              const safety = document.querySelector('.cr-boundary');
              const control = document.querySelector('.cr-picker input');
              return Boolean(safety && control &&
                (safety.compareDocumentPosition(control) & Node.DOCUMENT_POSITION_FOLLOWING));
            }"""
        )
        if not safety_first:
            raise AssertionError(f"{name}:safety_order_invalid")
        if page.locator(".cr-option input[type=radio]").count() != 4:
            raise AssertionError(f"{name}:radio_count_invalid")
        option_heights = page.locator(".cr-option").evaluate_all(
            "elements => elements.map(element => element.getBoundingClientRect().height)"
        )
        if not option_heights or min(option_heights) < 44:
            raise AssertionError(f"{name}:touch_target_too_small")
        overflow = page.evaluate(
            "document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )
        if overflow:
            raise AssertionError(f"{name}:horizontal_overflow")

        first = page.locator("#state-evidence_available")
        second = page.locator("#state-evidence_withheld")
        page.keyboard.press("Tab")
        if not first.evaluate("element => element === document.activeElement"):
            raise AssertionError(f"{name}:keyboard_focus_entry_failed")
        first.press("ArrowDown")
        if not second.is_checked():
            raise AssertionError(f"{name}:keyboard_selection_failed")
        focus_style = second.evaluate(
            "element => { const style = getComputedStyle(element.closest('label')); "
            "return [style.outlineStyle, style.outlineWidth, style.outlineColor, "
            "style.backgroundColor]; }"
        )
        if focus_style[0] == "none" or focus_style[1] == "0px":
            raise AssertionError(f"{name}:visible_focus_missing")
        if _contrast_ratio(focus_style[2], focus_style[3]) < 3:
            raise AssertionError(f"{name}:focus_contrast_too_low")
        visible_panels = page.locator(".cr-panel:visible")
        if visible_panels.count() != 1:
            raise AssertionError(f"{name}:panel_visibility_invalid")

        text = shell.inner_text().casefold()
        for term in PROHIBITED_VISIBLE_TERMS:
            if term in text:
                raise AssertionError(f"{name}:prohibited_visible_term:{term}")

        route_probes = (
            ("GET", "/openapi.json", 404),
            ("GET", "/gradio_api/openapi.json", 404),
            ("GET", "/gradio_api/file=https://example.com/", 404),
            ("GET", "/gradio_api/queue/status", 404),
            ("POST", "/gradio_api/upload", 405),
        )
        for method, path, expected_status in route_probes:
            if method == "POST":
                probe = context.request.post(expected_origin + path, data={})
            else:
                probe = context.request.get(expected_origin + path)
            if probe.status != expected_status:
                raise AssertionError(f"{name}:public_route_exposed:{method}:{path}:{probe.status}")
        page.wait_for_timeout(400)
        if violations:
            raise AssertionError(f"{name}:request_boundary:{violations}")
        if console_errors:
            raise AssertionError(f"{name}:console_errors:{console_errors}")
        if page_errors:
            raise AssertionError(f"{name}:page_errors:{page_errors}")
        print(f"{name}:PASS:{width}x{height}")
    finally:
        context.close()


def run_smoke(target_url: str) -> None:
    from playwright.sync_api import sync_playwright

    normalized_url = validate_target_url(target_url)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for name, width, height in VIEWPORTS:
                _run_viewport(browser, normalized_url, name, width, height)
        finally:
            browser.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    args = parser.parse_args(argv)
    run_smoke(args.url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
