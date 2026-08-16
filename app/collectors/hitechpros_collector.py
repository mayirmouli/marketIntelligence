import hashlib
from pathlib import Path

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
from sqlalchemy import text

from app.storage.db import engine
from app.collectors.hitechpros_parser import parse_hitechpros_snapshot


AUTH_FILE = "data/hitechpros_auth.json"
SNAPSHOT_FILE = "data/hitechpros_snapshot.html"

MISSIONS_URL = "https://esn.hitechpros.com/missions"


def create_hash(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def fetch_hitechpros_snapshot(
    headless: bool = True
) -> bool:

    print("Opening HiTechPros...")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=headless
        )

        context = browser.new_context(
            storage_state=AUTH_FILE
        )

        page = context.new_page()

        try:
            page.goto(
                MISSIONS_URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            try:
                page.wait_for_load_state(
                    "networkidle",
                    timeout=15000,
                )
            except PlaywrightTimeoutError:
                print(
                    "Network did not become idle, "
                    "continuing anyway..."
                )

            # Give Angular time to render mission data
            page.wait_for_timeout(3000)

            current_url = page.url

            print(
                f"Current URL: {current_url}"
            )

            # Authentication check
            if (
                "login" in current_url.lower()
                or "connexion" in current_url.lower()
            ):
                print(
                    "HiTechPros authentication "
                    "session appears to be expired."
                )

                browser.close()

                return False

            html = page.content()

            Path(
                SNAPSHOT_FILE
            ).write_text(
                html,
                encoding="utf-8",
            )

            print(
                f"Snapshot saved: "
                f"{SNAPSHOT_FILE}"
            )

            browser.close()

            return True

        except Exception as error:

            print(
                f"HiTechPros collection error: "
                f"{error}"
            )

            browser.close()

            return False


def insert_hitechpros_missions() -> int:

    missions = parse_hitechpros_snapshot(
        SNAPSHOT_FILE
    )

    print(
        f"Missions parsed: {len(missions)}"
    )

    inserted_count = 0

    with engine.begin() as connection:

        for mission in missions:

            content_hash = create_hash(
                f"HiTechPros|"
                f"{mission['external_id']}|"
                f"{mission['title']}|"
                f"{mission['raw_text']}"
            )

            result = connection.execute(
                text("""
                    INSERT INTO raw_opportunities
                    (
                        source_name,
                        external_id,
                        title,
                        raw_text,
                        url,
                        content_hash
                    )
                    VALUES
                    (
                        :source_name,
                        :external_id,
                        :title,
                        :raw_text,
                        :url,
                        :content_hash
                    )
                    ON CONFLICT (content_hash)
                    DO NOTHING
                """),
                {
                    "source_name": "HiTechPros",

                    "external_id":
                        mission["external_id"],

                    "title":
                        mission["title"],

                    "raw_text":
                        mission["raw_text"],

                    "url":
                        mission["url"],

                    "content_hash":
                        content_hash,
                },
            )

            inserted_count += result.rowcount

    return inserted_count


def collect_hitechpros(
    headless: bool = True
) -> int:

    success = fetch_hitechpros_snapshot(
        headless=headless
    )

    if not success:
        print(
            "HiTechPros collection aborted."
        )

        return 0

    count = insert_hitechpros_missions()

    print(
        f"New HiTechPros missions "
        f"inserted: {count}"
    )

    return count


if __name__ == "__main__":

    collect_hitechpros(
        headless=False
    )