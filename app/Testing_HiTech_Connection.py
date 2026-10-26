from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    print("Opening HiTechPros...")

    page.goto(
        "https://esn.hitechpros.com/missions",
        wait_until="domcontentloaded",
        timeout=90000,
    )

    print("URL:", page.url)
    print("Title:", page.title())

    input("Press Enter to close...")
    browser.close()