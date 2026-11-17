#!/usr/bin/env python3
"""Manual real-Chromium WINK static 3D boot witness (never deployment authority).

Tests actual JavaScript execution, public pinned-data readback, populated
panels, WebGL canvas and navigation—not merely an HTTP 200. No tokens,
provider writes, lab private records, GPU jobs, mail or browser mutations
outside the current public/localhost page.

Usage:
  python scripts/wink_browser_smoke.py --target local
  python scripts/wink_browser_smoke.py --target public

Playwright/Chromium is a test-only dependency on the operator host.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys

LOCAL = "http://127.0.0.1:18760/frontend/index.html"
PUBLIC = "https://szlholdings-wink-observatory.static.hf.space/index.html"
SOURCE_STATES = {"STALE SNAPSHOT", "PUBLIC SNAPSHOT"}
NO_DATA_STATES = {"CACHED SNAPSHOT", "OFFLINE BASELINE"}
BROWSER_ARGS = ["--no-sandbox", "--disable-dev-shm-usage", "--use-gl=angle",
                "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]


def observe(target: str) -> dict:
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    url = LOCAL if target == "local" else PUBLIC
    with sync_playwright() as provider:
        browser = provider.chromium.launch(headless=True, args=BROWSER_ARGS)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            errors: list[str] = []
            page.on("pageerror", lambda exception: errors.append(str(exception)[:220]))
            status = page.goto(url, wait_until="domcontentloaded", timeout=25000)
            if status is None or status.status != 200:
                return {"schema": "wink.browser-smoke/v1", "state": "HTTP_NOT_200",
                        "http": status.status if status else None,
                        "actual_browser_render_verified": False, "url": url}
            try:
                page.wait_for_function(
                    """() => {
                      let v=document.getElementById('feedBadge')?.textContent;
                      return ['PUBLIC SNAPSHOT','STALE SNAPSHOT',
                              'CACHED SNAPSHOT','OFFLINE BASELINE'].includes(v);
                    }""",
                    timeout=18000,
                )
            except PlaywrightTimeout:
                pass
            data = page.evaluate("""() => ({
                badge:document.getElementById('feedBadge')?.textContent,
                feedTime:document.getElementById('feedTime')?.textContent,
                protocol:document.getElementById('protoBody')?.innerText,
                battery:document.getElementById('batteryBody')?.innerText,
                note:document.getElementById('note')?.innerText,
                canvasWidth:document.querySelector('#c')?.width,
                canvasHeight:document.querySelector('#c')?.height,
                hasWebGL:!!(document.querySelector('#c')?.getContext('webgl2') ||
                          document.querySelector('#c')?.getContext('webgl')),
                navCount:document.querySelectorAll('#navBtns button').length
              })""")
            # The tab is meaningful only if the module actually registered
            # interaction handlers; syntactic HTML without JS would fail.
            page.locator('#navBtns button[data-v="worm"]').click(timeout=4000)
            nav_active = page.locator('#navBtns button[data-v="worm"]').get_attribute("class")
            badge = data.get("badge") or "UNKNOWN"
            source_loaded = (badge in SOURCE_STATES and
                             isinstance(data.get("feedTime"), str) and
                             "Dataset " in data["feedTime"] and
                             "producer " in data["feedTime"])
            panels_ready = (
                isinstance(data.get("protocol"), str) and
                "NOT FROZEN" in data["protocol"] and
                isinstance(data.get("battery"), str) and
                "C4 NEUTRAL" in data["battery"] and
                "UNINTERPRETABLE" in data["battery"]
            )
            rendered = (source_loaded and panels_ready and
                        data.get("hasWebGL") is True and
                        isinstance(data.get("canvasWidth"), int) and
                        data["canvasWidth"] > 100 and
                        data.get("canvasHeight", 0) > 100 and
                        data.get("navCount") == 4 and
                        "active" in (nav_active or "") and
                        len(errors) == 0)
            return {
                "schema": "wink.browser-smoke/v1",
                "url": url,
                "observed_utc": datetime.now(timezone.utc).isoformat(),
                "state": "SOURCE_AND_3D_CLIENT_BOOT_VERIFIED"
                         if rendered else "HOLD_CLIENT_BOOT_OR_DATA_UNAVAILABLE",
                "http": status.status,
                "feed_badge": badge,
                "feed_detail": data.get("feedTime"),
                "has_webgl": data.get("hasWebGL"),
                "protocol_panel_rendered": panels_ready,
                "navigation_click_active": "active" in (nav_active or ""),
                "js_exceptions": errors[:4],
                "actual_browser_render_verified": rendered,
                "hf_source_byte_parity_verified": False,
                "independent_scientific_validation": False,
                "training_started": False,
                "provider_writes": False,
                "lab_instrument_connected": False,
            }
        finally:
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("local", "public"), required=True)
    args = parser.parse_args()
    try:
        result = observe(args.target)
    except Exception as exc:
        result = {"schema": "wink.browser-smoke/v1", "state": "BROWSER_UNAVAILABLE",
                  "target": args.target, "reason_type": type(exc).__name__,
                  "actual_browser_render_verified": False,
                  "independent_scientific_validation": False}
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0 if result["actual_browser_render_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
