\set ON_ERROR_STOP on
\timing on
SET statement_timeout = '60s';
SET lock_timeout = '2s';

CREATE TEMP TABLE lifecycle_benchmark (
    id bigint GENERATED ALWAYS AS IDENTITY,
    created_at timestamptz NOT NULL,
    payload text NOT NULL
);

INSERT INTO lifecycle_benchmark (created_at, payload)
SELECT
    timestamptz '2024-01-01 00:00:00+00' + (value * interval '5 minutes'),
    repeat('x', 64)
FROM generate_series(0, 249999) AS value;

CREATE INDEX lifecycle_benchmark_created_at_idx
ON lifecycle_benchmark (created_at);
ANALYZE lifecycle_benchmark;

EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, SUMMARY ON)
SELECT count(*)
FROM lifecycle_benchmark
WHERE created_at < timestamptz '2025-01-01 00:00:00+00';

BEGIN;
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, SUMMARY ON)
DELETE FROM lifecycle_benchmark
WHERE created_at < timestamptz '2025-01-01 00:00:00+00';
ROLLBACK;

CREATE TEMP TABLE candle_partition_benchmark (
    observed_at timestamptz NOT NULL,
    close numeric(18, 4) NOT NULL
) PARTITION BY RANGE (observed_at);

DO $block$
DECLARE
    month_start date := date '2024-01-01';
    next_month date;
    partition_index integer;
BEGIN
    FOR partition_index IN 0..23 LOOP
        next_month := (month_start + interval '1 month')::date;
        EXECUTE format(
            'CREATE TEMP TABLE candle_partition_benchmark_%s '
            'PARTITION OF candle_partition_benchmark '
            'FOR VALUES FROM (%L) TO (%L)',
            to_char(month_start, 'YYYY_MM'),
            month_start,
            next_month
        );
        month_start := next_month;
    END LOOP;
END
$block$;

INSERT INTO candle_partition_benchmark (observed_at, close)
SELECT
    timestamptz '2024-01-01 00:00:00+00' + (value * interval '4 minutes'),
    100 + (value % 1000) / 10.0
FROM generate_series(0, 239999) AS value;

ANALYZE candle_partition_benchmark;

EXPLAIN (ANALYZE, BUFFERS, COSTS OFF, SUMMARY ON)
SELECT count(*)
FROM candle_partition_benchmark
WHERE observed_at >= timestamptz '2025-10-01 00:00:00+00'
  AND observed_at < timestamptz '2025-11-01 00:00:00+00';

SELECT
    250000 AS lifecycle_rows,
    240000 AS partitioned_rows,
    24 AS monthly_partitions,
    'temporary_only' AS persistence;
