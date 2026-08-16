import re
from sqlalchemy import text
from app.storage.db import engine


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.replace("\r", "\n")
    value = re.sub(r"\n+", "\n", value)
    value = re.sub(r"[ \t]+", " ", value)
    return value.strip()


def detect_language(text_value: str) -> str:
    text_lower = text_value.lower()

    french_markers = ["recherche", "mission", "client", "durée", "démarrage", "compétences"]
    english_markers = ["looking for", "project", "client", "duration", "start", "skills"]

    french_score = sum(marker in text_lower for marker in french_markers)
    english_score = sum(marker in text_lower for marker in english_markers)

    if french_score > english_score:
        return "fr"
    if english_score > french_score:
        return "en"
    return "unknown"


def clean_new_raw_opportunities() -> int:
    with engine.begin() as connection:
        raw_rows = connection.execute(
            text("""
                SELECT ro.id, ro.title, ro.raw_text
                FROM raw_opportunities ro
                LEFT JOIN clean_opportunities co
                    ON co.raw_opportunity_id = ro.id
                WHERE co.id IS NULL
            """)
        ).mappings().all()

        inserted_count = 0

        for row in raw_rows:
            clean_title = normalize_text(row["title"])
            clean_description = normalize_text(row["raw_text"])
            language = detect_language(clean_description)

            connection.execute(
                text("""
                    INSERT INTO clean_opportunities
                    (raw_opportunity_id, title, description, language)
                    VALUES
                    (:raw_opportunity_id, :title, :description, :language)
                """),
                {
                    "raw_opportunity_id": row["id"],
                    "title": clean_title,
                    "description": clean_description,
                    "language": language
                }
            )

            inserted_count += 1

    return inserted_count