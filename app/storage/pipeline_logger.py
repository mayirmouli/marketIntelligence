from sqlalchemy import text

from app.storage.db import engine


def start_pipeline_run() -> int:
    with engine.begin() as connection:
        run_id = connection.execute(
            text("""
                INSERT INTO pipeline_runs (status)
                VALUES ('running')
                RETURNING id
            """)
        ).scalar_one()

    return run_id


def log_stage_result(
    run_id: int,
    stage_name: str,
    result: dict,
    source_name: str | None = None,
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO pipeline_stage_runs
                (
                    pipeline_run_id,
                    stage_name,
                    source_name,
                    status,
                    parsed,
                    processed,
                    inserted,
                    duplicates,
                    errors,
                    execution_time
                )
                VALUES
                (
                    :pipeline_run_id,
                    :stage_name,
                    :source_name,
                    :status,
                    :parsed,
                    :processed,
                    :inserted,
                    :duplicates,
                    :errors,
                    :execution_time
                )
            """),
            {
                "pipeline_run_id": run_id,
                "stage_name": stage_name,
                "source_name": source_name,
                "status": result.get("status", "unknown"),
                "parsed": result.get("parsed"),
                "processed": result.get("processed"),
                "inserted": result.get("inserted", 0),
                "duplicates": result.get("duplicates", 0),
                "errors": result.get("errors", 0),
                "execution_time": result.get("execution_time"),
            },
        )


def finish_pipeline_run(
    run_id: int,
    status: str,
    total_execution_time: float,
    error_message: str | None = None,
):
    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE pipeline_runs
                SET
                    finished_at = NOW(),
                    status = :status,
                    total_execution_time = :total_execution_time,
                    error_message = :error_message
                WHERE id = :run_id
            """),
            {
                "run_id": run_id,
                "status": status,
                "total_execution_time": total_execution_time,
                "error_message": error_message,
            },
        )