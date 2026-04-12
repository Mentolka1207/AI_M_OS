-- AI_M_OS metrics schema
-- PostgreSQL 15+

CREATE TABLE IF NOT EXISTS metrics_cpu (
    id         BIGSERIAL PRIMARY KEY,
    ts         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_pct  REAL NOT NULL,
    cores_pct  REAL[] NOT NULL,
    load_avg   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics_memory (
    id             BIGSERIAL PRIMARY KEY,
    ts             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_kb       BIGINT NOT NULL,
    used_kb        BIGINT NOT NULL,
    swap_total_kb  BIGINT NOT NULL,
    swap_used_kb   BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics_network (
    id         BIGSERIAL PRIMARY KEY,
    ts         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    iface      TEXT NOT NULL,
    rx_bps     REAL NOT NULL,
    tx_bps     REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduler_events (
    id         BIGSERIAL PRIMARY KEY,
    ts         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    pid        INT NOT NULL,
    action     TEXT NOT NULL,  -- 'renice', 'kill_suggestion'
    old_nice   INT,
    new_nice   INT,
    reason     TEXT NOT NULL
);

-- Индекс для быстрых запросов за последние N минут
CREATE INDEX IF NOT EXISTS idx_cpu_ts  ON metrics_cpu(ts DESC);
CREATE INDEX IF NOT EXISTS idx_mem_ts  ON metrics_memory(ts DESC);
CREATE INDEX IF NOT EXISTS idx_net_ts  ON metrics_network(ts DESC);
