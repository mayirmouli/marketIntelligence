CREATE TABLE IF NOT EXISTS sources (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    base_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS raw_opportunities (
    id BIGSERIAL PRIMARY KEY,

    source_id BIGINT REFERENCES sources(id),
    source_name TEXT NOT NULL,

    external_id TEXT,
    title TEXT,
    raw_text TEXT,
    url TEXT,

    company_name TEXT,
    location TEXT,
    remote_policy TEXT,

    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    content_hash TEXT NOT NULL UNIQUE
);


CREATE TABLE IF NOT EXISTS clean_opportunities (
    id BIGSERIAL PRIMARY KEY,

    raw_opportunity_id BIGINT NOT NULL
        REFERENCES raw_opportunities(id)
        ON DELETE CASCADE,

    title TEXT,
    description TEXT,

    company_name TEXT,
    location TEXT,
    remote_policy TEXT,

    language TEXT,

    cleaned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_clean_raw_opportunity
        UNIQUE (raw_opportunity_id)
);


CREATE TABLE IF NOT EXISTS enriched_opportunities (
    id BIGSERIAL PRIMARY KEY,

    clean_opportunity_id BIGINT NOT NULL
        REFERENCES clean_opportunities(id)
        ON DELETE CASCADE,

    project_type TEXT,
    sector TEXT,
    seniority TEXT,

    duration TEXT,
    budget TEXT,
    urgency TEXT,

    required_profiles JSONB NOT NULL DEFAULT '[]'::jsonb,
    technologies JSONB NOT NULL DEFAULT '[]'::jsonb,

    business_need TEXT,

    market_attractiveness_score NUMERIC(5,2),
    strategic_fit_score NUMERIC(5,2),
    confidence_score NUMERIC(5,2),

    enriched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_enriched_clean_opportunity
        UNIQUE (clean_opportunity_id)
);


CREATE TABLE IF NOT EXISTS pipeline_runs (
    id BIGSERIAL PRIMARY KEY,

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,

    status VARCHAR(20) NOT NULL DEFAULT 'running',

    total_execution_time NUMERIC(10,2),
    error_message TEXT
);


CREATE TABLE IF NOT EXISTS pipeline_stage_runs (
    id BIGSERIAL PRIMARY KEY,

    pipeline_run_id BIGINT NOT NULL
        REFERENCES pipeline_runs(id)
        ON DELETE CASCADE,

    stage_name VARCHAR(100) NOT NULL,
    source_name VARCHAR(100),

    status VARCHAR(20) NOT NULL,

    parsed INTEGER,
    processed INTEGER,

    inserted INTEGER NOT NULL DEFAULT 0,
    duplicates INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,

    execution_time NUMERIC(10,2),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_raw_source_external
    ON raw_opportunities(source_name, external_id);

CREATE INDEX IF NOT EXISTS idx_raw_collected_at
    ON raw_opportunities(collected_at);

CREATE INDEX IF NOT EXISTS idx_clean_raw_id
    ON clean_opportunities(raw_opportunity_id);

CREATE INDEX IF NOT EXISTS idx_enriched_clean_id
    ON enriched_opportunities(clean_opportunity_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at
    ON pipeline_runs(started_at);

CREATE INDEX IF NOT EXISTS idx_pipeline_stage_run_id
    ON pipeline_stage_runs(pipeline_run_id);