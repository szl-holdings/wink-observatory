#!/usr/bin/env python3
"""Independent, read-only public WINK browser deployment witness.

A *green observation job* is never proof that the provider application
works. This tool records the real public browser state plus exact GitHub and
HF source identities. A known broken page is OBSERVED_CLIENT_BOOT_HOLD rather
than an unreported or fabricated deployment. No tokens or provider writes.

Use only the reviewed public HTTPS origins from wink_release_probe and
wink_browser_smoke; do not invoke either owner publisher.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from runpy import run_path
from typing import Any


ROOT = Path(__file__).resolve().parent
SPACE = "SZLHOLDINGS/wink-observatory"
STATIC_URL = "https://szlholdings-wink-observatory.static.hf.space/index.html"


def _load(name: str, fn: str):
    return run_path(str(ROOT / name), run_name="_public_monitor")[fn]


def classify(browser: Any, transport: Any) -> dict:
    """No remote calls; strict separation of observed browser boot vs admission."""
    if not isinstance(browser, dict):
        browser = {}
    if not isinstance(transport, dict):
        transport = {}

    main = transport.get("github_main_sha")
    hf_sha = transport.get("hf_space_revision")
    sdk = transport.get("hf_sdk")
    static_get = transport.get("static_http_get_statuses")
    static_http = (isinstance(static_get, dict) and
                   static_get.get("/index.html") == "200" and
                   static_get.get("/style.css") == "200")
    metadata = (isinstance(main, str) and re.fullmatch(r"[0-9a-f]{40}", main)
                and isinstance(hf_sha, str) and re.fullmatch(r"[0-9a-f]{40}", hf_sha)
                and sdk in ("static", "docker"))
    same_origin = browser.get("url") == STATIC_URL
    first_draws = browser.get("webgl_draw_calls_before")
    later_draws = browser.get("webgl_draw_calls_after")
    pixel_proof = (type(first_draws) is int and first_draws >= 100 and
                   type(later_draws) is int and later_draws > first_draws and
                   browser.get("canvas_pixel_change_observed") is True and
                   browser.get("navigation_click_active") is True and
                   browser.get("protocol_panel_rendered") is True and
                   browser.get("has_webgl") is True and
                   browser.get("js_exceptions") == [] and
                   browser.get("feed_badge") in ("STALE SNAPSHOT", "PUBLIC SNAPSHOT"))
    good_browser = (browser.get("actual_browser_render_verified") is True and
                    browser.get("state") == "SOURCE_AND_3D_CLIENT_BOOT_VERIFIED" and
                    same_origin and browser.get("http") == 200 and pixel_proof and
                    browser.get("provider_writes") is False and
                    browser.get("training_started") is False and
                    browser.get("independent_scientific_validation") is False)

    reported_browser_state = browser.get("state")
    recognized_browser_states = {
        "SOURCE_AND_3D_CLIENT_BOOT_VERIFIED",
        "HOLD_CLIENT_BOOT_OR_DATA_UNAVAILABLE",
        "HTTP_NOT_200",
    }
    if not metadata or reported_browser_state not in recognized_browser_states:
        status = "INCOMPLETE_PUBLIC_OBSERVATION"
    elif sdk != "static":
        # A future Docker migration needs a separate canonical-runtime test.
        status = "STATIC_CLIENT_NOT_APPLICABLE_TO_CURRENT_SDK"
    elif not static_http:
        status = "STATIC_HTTP_UNAVAILABLE"
    elif good_browser:
        status = "PUBLIC_STATIC_CLIENT_BOOT_OBSERVED"
    else:
        status = "PUBLIC_STATIC_CLIENT_BOOT_HOLD"

    return {
        "schema": "wink.public-browser-runtime-witness/v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "source_repo": "szl-holdings/wink-observatory",
        "github_main_sha": main,
        "hf_repo": SPACE,
        "hf_revision": hf_sha,
        "hf_sdk": sdk,
        "public_origin": STATIC_URL,
        "public_static_http_reachable": bool(static_http),
        "browser_observation_state": browser.get("state", "UNAVAILABLE"),
        "browser_failure_type": browser.get("reason_type"),
        "browser_badge": browser.get("feed_badge"),
        "browser_feed_detail": browser.get("feed_detail"),
        "browser_webgl_draws_before": browser.get("webgl_draw_calls_before"),
        "browser_webgl_draws_after": browser.get("webgl_draw_calls_after"),
        "browser_canvas_pixel_change_observed": browser.get("canvas_pixel_change_observed"),
        "public_itemized_node_count": browser.get("itemized_worm_nodes")
        if browser.get("itemized_node_count_verified") is True else None,
        "public_itemized_node_count_verified": browser.get("itemized_node_count_verified") is True,
        "public_itemized_node_count_state": browser.get("itemized_node_count_state", "UNAVAILABLE"),
        "browser_js_exceptions": browser.get("js_exceptions"),
        "public_client_boot_verified": bool(status == "PUBLIC_STATIC_CLIENT_BOOT_OBSERVED"),
        "deployment_observation": status,
        "source_byte_parity_independently_verified": False,
        "verified_owner_release_approval": False,
        "independent_scientific_validation": False,
        "live_wetlab_instrument_verified": False,
        "gpu_training_active_verified": False,
        "provider_writes": False,
        "release_admission": "HOLD",
        "public_source_probe_blockers": list(transport.get("blockers", []))[:20]
        if isinstance(transport.get("blockers"), list) else [],
    }


def observe() -> dict:
    # Each target is fixed in source. The order avoids claiming a working
    # frontend based on HTTP metadata alone.
    transport = _load("wink_release_probe.py", "observe")()
    try:
        browser = _load("wink_browser_smoke.py", "observe")("public")
    except Exception as exc:
        # Playwright has its own Error/TimeoutError hierarchy. Keep the
        # already-read transport evidence and a bounded, non-sensitive
        # diagnostic rather than losing the entire receipt on browser failure.
        browser = {"state": "BROWSER_UNAVAILABLE",
                   "reason_type": type(exc).__name__[:80]}
    return classify(browser, transport)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="Archive bounded public-only readback JSON")
    args = parser.parse_args()
    try:
        record = observe()
    except (OSError, ValueError, RuntimeError, TimeoutError) as exc:
        record = classify(
            {"state": "BROWSER_UNAVAILABLE", "reason_type": type(exc).__name__},
            {},
        )
    dest = args.output
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    dest.write_text(body, encoding="utf-8", newline="\n")
    print(json.dumps(record, sort_keys=True, ensure_ascii=True))
    # A known failed public boot is a valid observed HOLD, not an exception.
    # Infrastructure/browser/metadata unavailability fails the observer.
    return 2 if record["deployment_observation"] == "INCOMPLETE_PUBLIC_OBSERVATION" else 0


if __name__ == "__main__":
    raise SystemExit(main())

