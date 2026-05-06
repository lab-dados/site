"""Screenshot the footer of the home so we can eyeball it."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "_check"
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_context(viewport={"width": 1280, "height": 800}).new_page()
    page.goto("http://127.0.0.1:4324/", wait_until="networkidle")
    foot = page.locator("footer.footer")
    foot.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    foot.screenshot(path=str(OUT / "footer.png"))
    b.close()
print("saved")
