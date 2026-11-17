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
from hashlib import sha256
import sys

LOCAL = "http://127.0.0.1:18760/frontend/index.html"
PUBLIC = "https://szlholdings-wink-observatory.static.hf.space/index.html"
SOURCE_STATES = {"STALE SNAPSHOT", "PUBLIC SNAPSHOT"}
NO_DATA_STATES = {"CACHED SNAPSHOT", "OFFLINE BASELINE"}
BROWSER_ARGS = ["--no-sandbox", "--disable-dev-shm-usage", "--use-gl=angle",
                "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
# Count real WebGL draw commands, not just a canvas DOM node/context.
# Bound to the single current browser page, with no effect on provider data.
GL_DRAW_WITNESS = """(() => {
  window.__wink_draw_calls=0;
  for(const klass of [window.WebGLRenderingContext,window.WebGL2RenderingContext]){
    if(!klass) continue;
    for(const name of ['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']){
      const f=klass.prototype[name];
      if(typeof f==='function'){
        klass.prototype[name]=function(...args){
          window.__wink_draw_calls++;
          return f.apply(this,args);
        };
      }
    }
  }
})();"""


def observe(target: str) -> dict:
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    url = LOCAL if target == "local" else PUBLIC
    with sync_playwright() as provider:
        browser = provider.chromium.launch(headless=True, args=BROWSER_ARGS)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.add_init_script(GL_DRAW_WITNESS)
            errors: list[str] = []
            page.on("pageerror", lambda exception: errors.append(str(exception)[:220]))
            status = page.goto(url, wait_until="domcontentloaded", timeout=25000)
            # Playwright follows redirects. Attribute evidence to the observed
            # document, never merely the requested URL.
            if page.url != url or (status is not None and status.url != url):
                return {"schema": "wink.browser-smoke/v1",
                        "state": "UNEXPECTED_BROWSER_ORIGIN",
                        "http": status.status if status else None,
                        "actual_browser_render_verified": False,
                        "url": page.url, "requested_url": url,
                        "response_url": status.url if status else None}
            if status is None or status.status != 200:
                return {"schema": "wink.browser-smoke/v1", "state": "HTTP_NOT_200",
                        "http": status.status if status else None,
                        "actual_browser_render_verified": False, "url": page.url}
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
                navCount:document.querySelectorAll('#navBtns button').length,
                drawCalls:window.__wink_draw_calls||0
              })""")
            # The tab is meaningful only if the module actually registered
            # interaction handlers; syntactic HTML without JS would fail.
            before_png = page.locator("canvas#c").screenshot(timeout=15000)
            page.locator('#navBtns button[data-v="worm"]').click(timeout=4000)
            page.wait_for_timeout(650)
            after_png = page.locator("canvas#c").screenshot(timeout=15000)
            post_draws = page.evaluate("window.__wink_draw_calls||0")
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
            rendered = (page.url == url and status.url == url and
                        source_loaded and panels_ready and
                        data.get("hasWebGL") is True and
                        isinstance(data.get("canvasWidth"), int) and
                        data["canvasWidth"] > 100 and
                        data.get("canvasHeight", 0) > 100 and
                        data.get("navCount") == 4 and
                        "active" in (nav_active or "") and
                        data.get("drawCalls",0) >= 100 and
                        post_draws > data.get("drawCalls",0) and
                        len(before_png) > 15000 and len(after_png) > 15000 and
                        sha256(before_png).digest() != sha256(after_png).digest() and
                        len(errors) == 0)
            return {
                "schema": "wink.browser-smoke/v1",
                "url": page.url,
                "requested_url": url,
                "response_url": status.url,
                "observed_utc": datetime.now(timezone.utc).isoformat(),
                "state": "SOURCE_AND_3D_CLIENT_BOOT_VERIFIED"
                         if rendered else "HOLD_CLIENT_BOOT_OR_DATA_UNAVAILABLE",
                "http": status.status,
                "feed_badge": badge,
                "feed_detail": data.get("feedTime"),
                "has_webgl": data.get("hasWebGL"),
                "webgl_draw_calls_before": data.get("drawCalls"),
                "webgl_draw_calls_after": post_draws,
                "canvas_png_size_bytes": len(before_png),
                "canvas_pixel_change_observed": (sha256(before_png).digest() != sha256(after_png).digest()),
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

