from app.storage.db import test_connection
from app.processing.cleaner import clean_new_raw_opportunities
from app.enrichment.enricher import enrich_new_clean_opportunities


if __name__ == "__main__":
    test_connection()

    cleaned_count = clean_new_raw_opportunities()
    print(f"Cleaned opportunities inserted: {cleaned_count}")

    enriched_count = enrich_new_clean_opportunities()
    print(f"Enriched opportunities inserted: {enriched_count}")