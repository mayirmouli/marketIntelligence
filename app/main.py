import time
import logging
from app.logging_config import setup_logging
from app.storage.db import test_connection
from app.storage.pipeline_logger import (start_pipeline_run,log_stage_result,finish_pipeline_run,)
from app.collectors.hitechpros_collector import collect_hitechpros
from app.processing.cleaner import clean_new_raw_opportunities
from app.enrichment.enricher import enrich_new_clean_opportunities

logger = logging.getLogger("pipeline")

def print_stage_result(
    name: str,
    result: dict
):
    print(f"\n{name}")
    print("-" * len(name))

    for key, value in result.items():
        print(f"{key:15}: {value}")


def run_pipeline():
    setup_logging()
    pipeline_start = time.perf_counter()
    logger.info(
        "Market Intelligence Pipeline started"
    )
    print("=" * 50)
    print("MARKET INTELLIGENCE PIPELINE")
    print("=" * 50)

    test_connection()

    run_id = start_pipeline_run()
    print(f"Pipeline run ID: {run_id}")

    try: 
        collector_result = collect_hitechpros(headless=True)
        print_stage_result("HiTechPros Collector", collector_result)
        log_stage_result(
            run_id=run_id,
            stage_name="collection",
            source_name="HiTechPros",
            result=collector_result,
        )
        if collector_result["status"] != "success":
            raise RuntimeError(
                "HiTechPros collection failed."
            )
        logger.info(
            "HiTechPros collection completed: "
            "parsed=%s inserted=%s duplicates=%s",
            collector_result["parsed"],
            collector_result["inserted"],
            collector_result["duplicates"],
        )

        cleaner_result = clean_new_raw_opportunities()
        print_stage_result("Cleaning",cleaner_result)
        log_stage_result(
            run_id=run_id,
            stage_name="cleaning",
            result=cleaner_result,
        )
        logger.info(
            "Cleaning completed: processed=%s inserted=%s",
            cleaner_result["processed"],
            cleaner_result["inserted"],
        )

        enricher_result = enrich_new_clean_opportunities()
        print_stage_result("Enrichment", enricher_result)
        log_stage_result(
            run_id=run_id,
            stage_name="enrichment",
            result=enricher_result,
        )
        logger.info(
            "Enrichment completed: processed=%s inserted=%s",
            enricher_result["processed"],
            enricher_result["inserted"],
        )

        total_time = round(
            time.perf_counter() - pipeline_start,
            2
        )

        finish_pipeline_run(
            run_id=run_id,
            status="success",
            total_execution_time=total_time,
        )

        print("\n" + "=" * 50)
        print("PIPELINE COMPLETED")
        print(f"Run ID: {run_id}")
        print(f"Total execution time: {total_time}s")
        print("=" * 50)
        logger.info(
            "Pipeline completed successfully "
            "run_id=%s execution_time=%ss",
            run_id,
            total_time,
        )

    except Exception as error:
        total_time = round(
            time.perf_counter() - pipeline_start,
            2
        )

        finish_pipeline_run(
            run_id=run_id,
            status="failed",
            total_execution_time=total_time,
            error_message=str(error),
        )

        print("\n" + "=" * 50)
        print("PIPELINE FAILED")
        print(f"Run ID: {run_id}")
        print(f"Error: {error}")
        print("=" * 50)
        logger.exception(
            "Pipeline failed run_id=%s",
            run_id,
        )

        raise

if __name__ == "__main__":
    run_pipeline()