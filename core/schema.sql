CREATE TABLE IF NOT EXISTS securities (
    ticker TEXT PRIMARY KEY,
    cik TEXT,
    wikidata_id TEXT,
    name TEXT,
    exchange TEXT,
    sector TEXT,
    industry TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS facts (
    ticker TEXT NOT NULL,
    metric TEXT NOT NULL,
    period DATE NOT NULL,
    period_type TEXT NOT NULL,
    value DOUBLE,
    unit TEXT,
    source TEXT,
    ingested_at TIMESTAMP,
    PRIMARY KEY (ticker, metric, period, period_type)
);
CREATE TABLE IF NOT EXISTS prices (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE,
    volume BIGINT,
    PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS macro (
    series_id TEXT NOT NULL,
    date DATE NOT NULL,
    value DOUBLE,
    PRIMARY KEY (series_id, date)
);
CREATE TABLE IF NOT EXISTS metric_catalog (
    metric TEXT PRIMARY KEY,
    label TEXT,
    category TEXT,
    unit TEXT,
    description TEXT,
    higher_is_better BOOLEAN
);
CREATE INDEX IF NOT EXISTS idx_facts_metric ON facts(metric, period_type);
CREATE INDEX IF NOT EXISTS idx_facts_ticker ON facts(ticker);
CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices(ticker, date);
