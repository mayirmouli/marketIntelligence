import hashlib
from sqlalchemy import text
from app.storage.db import engine
from app.collectors.hitechpros_parser import parse_hitechpros_snapshot


def create_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def collect_hitechpros_from_snapshot() -> int:
    missions = parse_hitechpros_snapshot()
    inserted_count = 0

    with engine.begin() as connection:
        for mission in missions:
            content_hash = create_hash(
                f"HiTechPros|{mission['external_id']}|{mission['title']}|{mission['raw_text']}"
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
                    ON CONFLICT (content_hash) DO NOTHING
                """),
                {
                    "source_name": "HiTechPros",
                    "external_id": mission["external_id"],
                    "title": mission["title"],
                    "raw_text": mission["raw_text"],
                    "url": mission["url"],
                    "content_hash": content_hash,
                }
            )

            inserted_count += result.rowcount

    return inserted_count


if __name__ == "__main__":
    count = collect_hitechpros_from_snapshot()
    print(f"HiTechPros missions inserted: {count}")