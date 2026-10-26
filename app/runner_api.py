import os
import subprocess

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text


app = FastAPI(
    title="Market Intelligence Pipeline Runner"
)


POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "localhost"
)

POSTGRES_PORT = os.getenv(
    "POSTGRES_PORT",
    "5432"
)

POSTGRES_DB = os.getenv(
    "POSTGRES_DB",
    "market_intel"
)

POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
    "market_user"
)

POSTGRES_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
    ""
)


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


engine = create_engine(
    DATABASE_URL
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "market-intelligence-pipeline"
    }


def get_latest_run_id():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT MAX(id)
                FROM pipeline_runs
            """)
        ).scalar()

        return result or 0


def get_run_details(run_id: int):
    with engine.connect() as connection:

        run = connection.execute(
            text("""
                SELECT
                    id,
                    started_at,
                    finished_at,
                    status,
                    total_execution_time,
                    error_message
                FROM pipeline_runs
                WHERE id = :run_id
            """),
            {
                "run_id": run_id
            }
        ).mappings().first()

        stages = connection.execute(
            text("""
                SELECT
                    stage_name,
                    source_name,
                    status,
                    parsed,
                    processed,
                    inserted,
                    duplicates,
                    errors,
                    execution_time,
                    created_at
                FROM pipeline_stage_runs
                WHERE pipeline_run_id = :run_id
                ORDER BY id
            """),
            {
                "run_id": run_id
            }
        ).mappings().all()

    if not run:
        return None

    return {
        "status": run["status"],
        "run_id": run["id"],

        "started_at": (
            run["started_at"].isoformat()
            if run["started_at"]
            else None
        ),

        "finished_at": (
            run["finished_at"].isoformat()
            if run["finished_at"]
            else None
        ),

        "total_execution_time": (
            float(
                run["total_execution_time"]
            )
            if run["total_execution_time"] is not None
            else None
        ),

        "error_message":
            run["error_message"],

        "stages": [
            {
                "stage_name":
                    stage["stage_name"],

                "source_name":
                    stage["source_name"],

                "status":
                    stage["status"],

                "parsed":
                    stage["parsed"],

                "processed":
                    stage["processed"],

                "inserted":
                    stage["inserted"],

                "duplicates":
                    stage["duplicates"],

                "errors":
                    stage["errors"],

                "execution_time": (
                    float(
                        stage["execution_time"]
                    )
                    if stage["execution_time"] is not None
                    else None
                ),

                "created_at": (
                    stage["created_at"].isoformat()
                    if stage["created_at"]
                    else None
                ),
            }
            for stage in stages
        ],
    }


@app.post("/run")
def run_pipeline():

    previous_run_id = get_latest_run_id()

    result = subprocess.run(
        [
            "python",
            "-m",
            "app.main"
        ],
        capture_output=True,
        text=True
    )

    latest_run_id = get_latest_run_id()

    if latest_run_id <= previous_run_id:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "failed",
                "exit_code":
                    result.returncode,
                "message":
                    "Pipeline did not create "
                    "a pipeline_runs record.",
                "stderr":
                    result.stderr,
            }
        )

    run_details = get_run_details(
        latest_run_id
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                **run_details,
                "exit_code":
                    result.returncode,
            }
        )

    return {
        **run_details,
        "exit_code":
            result.returncode,
    }