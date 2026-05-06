"""Manual visual check of the home hero animation.

Hits the local preview server, samples the inline `style.fill` of each
animated dot at multiple times, and prints whether they are changing.
Also saves two screenshots ~1.2s apart so we can compare frames.

Run with the static server already up at http://127.0.0.1:4324/.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "http://127.0.0.1:4324/"
OUT = Path(__file__).resolve().parents[1] / "_check"
OUT.mkdir(exist_ok=True)


def sample_fills(page) -> list[str]:
    return page.eval_on_selector_all(
        ".ld-mark-svg .dot", "els => els.map(e => e.style.fill || '')"
    )


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 720})
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector(".ld-mark-svg .dot", timeout=5_000)

        # Frame 1
        time.sleep(0.4)
        f1 = sample_fills(page)
        page.screenshot(path=str(OUT / "hero_t1.png"), clip={
            "x": 0, "y": 0, "width": 1280, "height": 600,
        })

        # Frame 2 (~1.2s later, mid-cycle)
        time.sleep(1.2)
        f2 = sample_fills(page)
        page.screenshot(path=str(OUT / "hero_t2.png"), clip={
            "x": 0, "y": 0, "width": 1280, "height": 600,
        })

        # Frame 3 (~2.4s later)
        time.sleep(1.2)
        f3 = sample_fills(page)

        browser.close()

    print(f"dots count: {len(f1)}")
    if not f1:
        print("FAIL: no dots found")
        return 1
    print("Sample fill values:")
    for i, (a, b, c) in enumerate(zip(f1, f2, f3)):
        print(f"  dot[{i}]  t1={a}\n         t2={b}\n         t3={c}")

    changed = sum(1 for a, b, c in zip(f1, f2, f3) if (a, b, c).count(a) != 3)
    print(f"\ndots whose fill changed across the three samples: {changed}/{len(f1)}")
    if changed == 0:
        print("FAIL: animation is not running")
        return 1
    print("OK: animation is running")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
