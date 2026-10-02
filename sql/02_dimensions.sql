-- =====================================================================
-- 02_dimensions.sql
-- Conformed dimensions shared by every fact table and dashboard sheet.
-- =====================================================================

CREATE OR REPLACE TABLE dim_state AS
SELECT DISTINCT
    c.state,
    c.state_name,
    CASE p.region_code
        WHEN 1 THEN 'Northeast' WHEN 2 THEN 'Midwest'
        WHEN 3 THEN 'South'     WHEN 4 THEN 'West'
    END AS census_region
FROM stg_cdc_mental_health c
JOIN (SELECT state_name, arg_max(region_code, year) AS region_code   -- latest vintage wins
      FROM stg_population GROUP BY state_name) p
  ON p.state_name = c.state_name
WHERE c.group_name = 'State'
  AND c.state IS NOT NULL;

CREATE OR REPLACE TABLE dim_provider_type AS
SELECT DISTINCT
    provider_type,
    bh_category,
    CASE WHEN bh_category = 'Counselor / MFT' THEN 2024 ELSE NULL END
        AS medicare_eligible_from      -- Consolidated Appropriations Act, 2023
FROM stg_bh_providers;

CREATE OR REPLACE TABLE dim_service AS
SELECT hcpcs_cd,
       service_category,
       arg_max(hcpcs_desc, year) AS hcpcs_desc   -- most recent description wins
FROM stg_bh_services_geo
GROUP BY ALL;
