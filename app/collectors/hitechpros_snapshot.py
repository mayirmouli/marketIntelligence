from pathlib import Path
from playwright.sync_api import sync_playwright

AUTH_FILE = "data/hitechpros_auth.json"
OUTPUT_FILE = "data/hitechpros_snapshot2.html"


def save_authenticated_snapshot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()

        page.goto("https://esn.hitechpros.com/missions", wait_until="networkidle")

        print("Navigate manually to the missions/offers search results page.")
        input("Press ENTER once the offers list is visible...")

        html = page.content()
        Path(OUTPUT_FILE).write_text(html, encoding="utf-8")

        print(f"Snapshot saved to {OUTPUT_FILE}")
        browser.close()


if __name__ == "__main__":
    save_authenticated_snapshot()