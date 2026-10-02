-- =====================================================================
-- 03_facts.sql
-- Fact tables at a clearly stated grain.
-- NOTE: benes_served_sum adds beneficiaries across providers, so a patient
--       who sees two providers is counted twice. Use it for workload, not
--       for unique-patient counts.
-- =====================================================================

-- Grain: state x year x bh_category
CREATE OR REPLACE TABLE fct_state_supply AS
WITH base AS (
    SELECT state, year, bh_category,
           count(*)                                                AS providers,
           count(*) FILTER (WHERE rurality = 'Small Town / Rural') AS rural_providers,
           sum(tot_benes)                                          AS benes_served_sum,
           sum(tot_services)                                       AS services,
           sum(tot_submitted_charge)                               AS submitted_charge,
           sum(tot_allowed_amt)                                    AS allowed_amt,
           sum(tot_payment_amt)                                    AS payment_amt
    FROM stg_bh_providers
    GROUP BY ALL
)
SELECT b.*,
       s.state_name,
       s.census_region,
       p.population,
       b.providers * 100000.0 / p.population      AS providers_per_100k,
       b.payment_amt / NULLIF(b.services, 0)      AS payment_per_service,
       b.payment_amt / NULLIF(b.benes_served_sum, 0) AS payment_per_bene,
       b.benes_served_sum / NULLIF(b.providers, 0)   AS benes_per_provider
FROM base b
JOIN dim_state s USING (state)
LEFT JOIN stg_population p
       ON p.state_name = s.state_name AND p.year = b.year;

-- Grain: year x state ('US' = national) x hcpcs_cd x place_of_service
CREATE OR REPLACE TABLE fct_service_reimbursement AS
WITH agg AS (
    SELECT year,
           CASE WHEN geo_level = 'National' THEN 'US' ELSE state END AS state,
           hcpcs_cd, service_category, place_of_service,
           sum(tot_providers)                          AS providers,
           sum(tot_benes)                              AS benes,
           sum(tot_services)                           AS services,
           sum(avg_submitted_charge * tot_services)    AS submitted_amt,
           sum(avg_allowed_amt      * tot_services)    AS allowed_amt,
           sum(est_total_payment)                      AS payment_amt
    FROM stg_bh_services_geo
    GROUP BY ALL
),
rates AS (
    SELECT *,
           payment_amt   / NULLIF(services, 0)  AS avg_payment_per_service,
           allowed_amt   / NULLIF(services, 0)  AS avg_allowed_per_service,
           payment_amt   / NULLIF(submitted_amt, 0) AS payment_to_charge_ratio
    FROM agg
)
SELECT r.*,
       n.avg_payment_per_service AS national_avg_payment_per_service,
       r.avg_payment_per_service / NULLIF(n.avg_payment_per_service, 0)
           AS payment_index_vs_national          -- 1.10 = pays 10% above national
FROM rates r
LEFT JOIN rates n
       ON n.state = 'US'
      AND n.year = r.year
      AND n.hcpcs_cd = r.hcpcs_cd
      AND n.place_of_service = r.place_of_service;

-- Grain: state x indicator x year (CDC Household Pulse, 2020-2022)
CREATE OR REPLACE TABLE fct_demand_state AS
SELECT state, indicator, year,
       avg(value_pct)                          AS avg_pct,
       count(value_pct)                        AS periods_reported,
       count(*) FILTER (WHERE is_suppressed)   AS periods_suppressed
FROM stg_cdc_mental_health
WHERE group_name = 'State'
GROUP BY ALL;
