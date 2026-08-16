import hashlib
import time
import logging
from pathlib import Path

from playwright.sync_api import (sync_playwright,TimeoutError as PlaywrightTimeoutError,
)
from sqlalchemy import text

from app.storage.db import engine
from app.collectors.hitechpros_parser import parse_hitechpros_snapshot


AUTH_FILE = "data/hitechpros_auth.json"
SNAPSHOT_FILE = "data/hitechpros_snapshot.html"

MISSIONS_URL = "https://esn.hitechpros.com/missions"

logger = logging.getLogger("hitechpros")


def create_hash(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()

def session_is_expired(page) -> bool:
    current_url = page.url.lower()
    if "login" in current_url or "connexion" in current_url:
        return True

    try:
        password_field = page.locator(
            "input[type='password']"
        )

        if (
            password_field.count() > 0
            and password_field.first.is_visible()
        ):
            return True

    except Exception:
        pass

    return False

def fetch_hitechpros_snapshot(
    headless: bool = True
) -> bool:

    logger.info("Opening HiTechPros")

    with sync_playwright() as p:

        browser = None

        try:
            browser = p.chromium.launch(
                headless=headless
            )

            context = browser.new_context(
                storage_state=AUTH_FILE
            )

            page = context.new_page()

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
                logger.warning(
                    "Network did not become idle, "
                    "continuing anyway..."
                )

            # Give Angular time to render mission data
            page.wait_for_timeout(3000)

            current_url = page.url

            logger.info("Current URL: %s", current_url)

            # Authentication check
            if session_is_expired(page):
                logger.warning("HiTechPros session expired")
                return False

            html = page.content()

            Path(
                SNAPSHOT_FILE
            ).write_text(
                html,
                encoding="utf-8",
            )

            logger.info("Snapshot saved: %s", SNAPSHOT_FILE)

            #browser.close()

            return True

        except Exception as error:

            logger.exception( "HiTechPros snapshot ""collection failed"
            )

            #browser.close()

            return False
        
        finally:
            if browser is not None:
                browser.close()


def insert_hitechpros_missions(
    missions: list[dict]
) -> int:

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

def collect_hitechpros(headless: bool = True) -> dict:
    start_time = time.perf_counter()

    success = fetch_hitechpros_snapshot(
        headless=headless
    )

    if not success:
        return {
            "status": "failed",
            "parsed": 0,
            "inserted": 0,
            "duplicates": 0,
            "errors": 1,
            "execution_time": round(
                time.perf_counter() - start_time,
                2
            ),
        }

    missions = parse_hitechpros_snapshot(
        SNAPSHOT_FILE
    )
    parsed_count = len(missions)
    if parsed_count == 0:
        logger.error(
            "No missions were parsed from "
            "HiTechPros snapshot"
        )

        return {
            "status": "failed",
            "parsed": 0,
            "inserted": 0,
            "duplicates": 0,
            "errors": 1,
            "execution_time": round(
                time.perf_counter()
                - start_time,
                2
            ),
        }

    logger.info(
        "Missions parsed: %s",
        parsed_count
    )

    inserted_count = insert_hitechpros_missions(missions)

    duplicates_count = (
        parsed_count - inserted_count
    )

    return {
        "status": "success",
        "parsed": parsed_count,
        "inserted": inserted_count,
        "duplicates": duplicates_count,
        "errors": 0,
        "execution_time": round(
            time.perf_counter() - start_time,
            2
        ),
    }


if __name__ == "__main__":
    result = collect_hitechpros(
        headless=False
    )