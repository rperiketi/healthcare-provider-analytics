-- =====================================================================
-- 04_marts.sql
-- Dashboard-ready marts. Each one feeds a specific Tableau sheet.
-- =====================================================================

-- KPI cards + national trend line (grain: year)
CREATE OR REPLACE TABLE mart_national_kpis AS
WITH y AS (
    SELECT year,
           sum(providers)        AS bh_providers,
           sum(services)         AS services,
           sum(payment_amt)      AS payment_amt,
           sum(benes_served_sum) AS benes_served_sum
    FROM fct_state_supply
    GROUP BY year
),
pop AS (
    SELECT p.year, sum(p.population) AS population
    FROM stg_population p
    JOIN dim_state s USING (state_name)
    GROUP BY p.year
)
SELECT y.*,
       pop.population,
       y.bh_providers * 100000.0 / pop.population                    AS providers_per_100k,
       y.payment_amt / NULLIF(y.services, 0)                         AS payment_per_service,
       y.bh_providers - lag(y.bh_providers) OVER w_kpi                   AS providers_yoy_change,
       round(100.0 * (y.bh_providers / lag(y.bh_providers) OVER w_kpi - 1), 2) AS providers_yoy_pct,
       round(100.0 * (y.payment_amt  / lag(y.payment_amt)  OVER w_kpi - 1), 2) AS payment_yoy_pct,
       round(100.0 * y.bh_providers / first_value(y.bh_providers) OVER w_kpi, 1) AS providers_index_2019
FROM y
LEFT JOIN pop USING (year)
WINDOW w_kpi AS (ORDER BY y.year);

-- Workforce trend by category (grain: bh_category x year)
CREATE OR REPLACE TABLE mart_category_trend AS
WITH c AS (
    SELECT bh_category, year,
           sum(providers)   AS providers,
           sum(services)    AS services,
           sum(payment_amt) AS payment_amt
    FROM fct_state_supply
    GROUP BY ALL
)
SELECT *,
       payment_amt / NULLIF(services, 0)                               AS payment_per_service,
       round(100.0 * (providers / lag(providers) OVER w_cat - 1), 2)       AS providers_yoy_pct,
       round(100.0 * providers / first_value(providers) OVER w_cat, 1)     AS providers_index_first_year,
       round(100.0 * providers / sum(providers) OVER (PARTITION BY year), 2) AS share_of_bh_workforce_pct
FROM c
WINDOW w_cat AS (PARTITION BY bh_category ORDER BY year);

-- The hero table: demand vs supply vs reimbursement (grain: state)
CREATE OR REPLACE TABLE mart_state_gap AS
WITH demand AS (
    SELECT state,
           avg(value_pct) FILTER (WHERE indicator = 'Unmet Counseling Need')        AS unmet_need_pct,
           avg(value_pct) FILTER (WHERE indicator = 'Received Counseling')          AS received_counseling_pct,
           avg(value_pct) FILTER (WHERE indicator = 'Took Medication')              AS took_medication_pct,
           avg(value_pct) FILTER (WHERE indicator = 'Medication and/or Counseling') AS any_treatment_pct
    FROM stg_cdc_mental_health
    WHERE group_name = 'State'
    GROUP BY state
),
supply_year AS (
    SELECT state, year,
           sum(providers)   AS providers,
           max(population)  AS population
    FROM fct_state_supply
    GROUP BY ALL
),
supply AS (
    SELECT state,
           avg(providers * 100000.0 / population) FILTER (WHERE year BETWEEN 2020 AND 2022)
                                                   AS providers_per_100k_2020_22,
           max(providers * 100000.0 / population) FILTER (WHERE year = 2024)
                                                   AS providers_per_100k_2024,
           max(providers) FILTER (WHERE year = 2019) AS providers_2019,
           max(providers) FILTER (WHERE year = 2024) AS providers_2024
    FROM supply_year
    GROUP BY state
),
reimb AS (   -- 60-min psychotherapy in an office setting: the most common BH service
    SELECT state,
           avg_payment_per_service   AS psychotherapy_60min_payment_2024,
           payment_index_vs_national AS psychotherapy_payment_index
    FROM fct_service_reimbursement
    WHERE hcpcs_cd = '90837' AND place_of_service = 'O' AND year = 2024 AND state <> 'US'
),
joined AS (
    SELECT s.state, s.state_name, s.census_region,
           d.unmet_need_pct, d.received_counseling_pct, d.took_medication_pct, d.any_treatment_pct,
           sp.providers_per_100k_2020_22, sp.providers_per_100k_2024,
           sp.providers_2019, sp.providers_2024,
           round(100.0 * (sp.providers_2024 / sp.providers_2019 - 1), 1) AS providers_change_pct_2019_24,
           r.psychotherapy_60min_payment_2024, r.psychotherapy_payment_index
    FROM dim_state s
    LEFT JOIN demand d USING (state)
    LEFT JOIN supply sp USING (state)
    LEFT JOIN reimb r USING (state)
),
ranked AS (
    SELECT *,
           percent_rank() OVER (ORDER BY unmet_need_pct)                  AS demand_pctile,
           percent_rank() OVER (ORDER BY providers_per_100k_2020_22 DESC) AS scarcity_pctile
    FROM joined
)
SELECT *,
       round(100 * (0.5 * demand_pctile + 0.5 * scarcity_pctile), 1) AS access_gap_score,
       rank() OVER (ORDER BY 0.5 * demand_pctile + 0.5 * scarcity_pctile DESC) AS access_gap_rank,
       CASE
           WHEN demand_pctile >= 0.5 AND scarcity_pctile >= 0.5 THEN 'High need / Low supply'
           WHEN demand_pctile >= 0.5                            THEN 'High need / High supply'
           WHEN scarcity_pctile >= 0.5                          THEN 'Low need / Low supply'
           ELSE                                                      'Low need / High supply'
       END AS gap_quadrant
FROM ranked;

-- National service mix (grain: service_category x year)
CREATE OR REPLACE TABLE mart_service_mix AS
WITH m AS (
    SELECT service_category, year,
           sum(services)    AS services,
           sum(payment_amt) AS payment_amt
    FROM fct_service_reimbursement
    WHERE state = 'US'
    GROUP BY ALL
)
SELECT *,
       payment_amt / NULLIF(services, 0)                                     AS avg_payment_per_service,
       round(100.0 * payment_amt / sum(payment_amt) OVER (PARTITION BY year), 2) AS share_of_bh_payment_pct,
       round(100.0 * (services / lag(services) OVER w_mix - 1), 2)              AS services_yoy_pct
FROM m
WINDOW w_mix AS (PARTITION BY service_category ORDER BY year);

-- Rural vs urban access (grain: rurality x bh_category x year)
CREATE OR REPLACE TABLE mart_rural_access AS
SELECT rurality, bh_category, year,
       count(*)                                        AS providers,
       median(tot_benes)                               AS median_benes_per_provider,
       sum(tot_payment_amt) / NULLIF(sum(tot_services), 0) AS payment_per_service,
       avg(bene_avg_risk_score)                        AS avg_patient_risk_score
FROM stg_bh_providers
GROUP BY ALL;

-- Reference-style demand breakdowns: age, sex, symptoms, race, etc.
CREATE OR REPLACE TABLE mart_demand_by_group AS
SELECT group_name, subgroup, indicator,
       avg(value_pct)  AS avg_pct,
       min(start_date) AS period_start,
       max(end_date)   AS period_end
FROM stg_cdc_mental_health
WHERE group_name NOT IN ('State')
GROUP BY ALL;

-- National demand time series with confidence bands
CREATE OR REPLACE TABLE mart_demand_trend AS
SELECT indicator, time_period, time_period_label, start_date, end_date,
       value_pct, low_ci, high_ci
FROM stg_cdc_mental_health
WHERE group_name = 'National Estimate';

-- Provider-level detail for Tableau drill-down (names excluded by design)
CREATE OR REPLACE TABLE mart_provider_detail AS
SELECT year, npi, provider_type, bh_category, city, state, zip5, rurality,
       tot_benes, tot_services, tot_payment_amt, payment_per_service,
       bene_avg_risk_score, bene_pct_depression, bene_pct_anxiety
FROM stg_bh_providers;
