from playwright.sync_api import sync_playwright

AUTH_FILE = "data/hitechpros_auth.json"


def save_hitechpros_session():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://esn.hitechpros.com", wait_until="domcontentloaded")

        print("Log in manually in the opened browser.")
        print("Go to the page where you can see missions/offers.")
        input("Press ENTER here after login...")

        context.storage_state(path=AUTH_FILE)
        print(f"Session saved to {AUTH_FILE}")

        browser.close()


if __name__ == "__main__":
    save_hitechpros_session()