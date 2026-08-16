CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_opportunities (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    source_name TEXT,
    external_id TEXT,
    title TEXT,
    raw_text TEXT,
    url TEXT,
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),
    content_hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS clean_opportunities (
    id SERIAL PRIMARY KEY,
    raw_opportunity_id INTEGER REFERENCES raw_opportunities(id),
    title TEXT,
    description TEXT,
    company_name TEXT,
    location TEXT,
    remote_policy TEXT,
    language TEXT,
    cleaned_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS enriched_opportunities (
    id SERIAL PRIMARY KEY,
    clean_opportunity_id INTEGER REFERENCES clean_opportunities(id),
    project_type TEXT,
    sector TEXT,
    seniority TEXT,
    duration TEXT,
    budget TEXT,
    urgency TEXT,
    required_profiles JSONB,
    technologies JSONB,
    business_need TEXT,
    market_attractiveness_score NUMERIC,
    strategic_fit_score NUMERIC,
    confidence_score NUMERIC,
    enriched_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_date TIMESTAMP DEFAULT NOW(),
    status TEXT,
    collected_count INTEGER DEFAULT 0,
    cleaned_count INTEGER DEFAULT 0,
    enriched_count INTEGER DEFAULT 0,
    error_message TEXT
);