-- =====================================================================
-- 01_staging.sql
-- Staging layer: thin views over the validated Parquet files, plus
-- Census population reshaped from wide (one column per year) to long.
-- {{PROCESSED}} and {{RAW}} are substituted by src/build_warehouse.py
-- =====================================================================

CREATE OR REPLACE VIEW stg_bh_providers AS
SELECT * FROM read_parquet('{{PROCESSED}}/bh_providers.parquet');

CREATE OR REPLACE VIEW stg_state_provider_totals AS
SELECT * FROM read_parquet('{{PROCESSED}}/state_provider_totals.parquet');

CREATE OR REPLACE VIEW stg_bh_services_geo AS
SELECT * FROM read_parquet('{{PROCESSED}}/bh_services_geo.parquet');

CREATE OR REPLACE VIEW stg_cdc_mental_health AS
SELECT * FROM read_parquet('{{PROCESSED}}/cdc_mental_health.parquet');

-- Census: 2020-2025 vintage (UNPIVOT wide year columns) + 2019 from the 2010s vintage
CREATE OR REPLACE TABLE stg_population AS
WITH v2020s AS (
    SELECT NAME, REGION, COLUMNS('^POPESTIMATE20[0-9]{2}$')
    FROM read_csv('{{RAW}}/census_pop_2020s.csv', all_varchar = true, header = true,
                  encoding = 'latin-1')
    WHERE TRY_CAST(SUMLEV AS INTEGER) = 40
),
long_2020s AS (
    UNPIVOT v2020s ON COLUMNS('^POPESTIMATE') INTO NAME col VALUE pop
)
SELECT trim(NAME)                          AS state_name,
       TRY_CAST(REGION AS INTEGER)         AS region_code,
       CAST(substr(col, 12) AS INTEGER)    AS year,
       CAST(pop AS BIGINT)                 AS population,
       'Vintage 2025'                      AS source_vintage
FROM long_2020s
UNION ALL
SELECT trim(NAME), TRY_CAST(REGION AS INTEGER), 2019,
       CAST(POPESTIMATE2019 AS BIGINT), 'Vintage 2019'
FROM read_csv('{{RAW}}/census_pop_2010s.csv', all_varchar = true, header = true,
              encoding = 'latin-1')
WHERE TRY_CAST(SUMLEV AS INTEGER) = 40;
