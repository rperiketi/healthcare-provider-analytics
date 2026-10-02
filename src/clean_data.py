"""
Phase 2B - Cleaning & Validation
--------------------------------
Raw CSVs  ->  typed, filtered, analysis-ready Parquet files + validation report.

Outputs (data/processed/):
    bh_providers.parquet          behavioral-health providers, one row per NPI per year
    state_provider_totals.parquet all Medicare providers per state/year (denominator)
    bh_services_geo.parquet       behavioral-health HCPCS services by state/national
    cdc_mental_health.parquet     CDC Household Pulse demand indicators
Report:
    docs/validation_report.md

Usage:
    python src/clean_data.py
Exit code 1 if any ERROR-level validation check fails.
"""
import sys
from datetime import datetime
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
REPORT = ROOT / "docs" / "validation_report.md"

# ----------------------------------------------------------------- reference data
BH_PROVIDER_TYPES = {
    "Psychiatry": "Psychiatry",
    "Geriatric Psychiatry": "Psychiatry",
    "Neuropsychiatry": "Psychiatry",
    "Addiction Medicine": "Psychiatry",
    "Psychologist, Clinical": "Psychologist",
    "Licensed Clinical Social Worker": "Social Worker",
    "Licensed Professional Counselor": "Counselor / MFT",  # Medicare-eligible from 2024
    "Marriage and Family Therapist": "Counselor / MFT",    # Medicare-eligible from 2024
}

BH_HCPCS = {
    "90791": "Diagnostic Evaluation", "90792": "Diagnostic Evaluation",
    "90832": "Psychotherapy", "90834": "Psychotherapy", "90837": "Psychotherapy",
    "90833": "Psychotherapy Add-on (with E/M)", "90836": "Psychotherapy Add-on (with E/M)",
    "90838": "Psychotherapy Add-on (with E/M)",
    "90839": "Crisis Psychotherapy", "90840": "Crisis Psychotherapy",
    "90846": "Family / Group Therapy", "90847": "Family / Group Therapy",
    "90853": "Family / Group Therapy",
    "96130": "Psychological Testing", "96131": "Psychological Testing",
    "96136": "Psychological Testing", "96137": "Psychological Testing",
    "99484": "Collaborative / Integrated Care", "99492": "Collaborative / Integrated Care",
    "99493": "Collaborative / Integrated Care", "99494": "Collaborative / Integrated Care",
}

STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
    "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA",
    "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND",
    "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

CDC_INDICATORS = {
    "Needed Counseling or Therapy But Did Not Get It, Last 4 Weeks": "Unmet Counseling Need",
    "Received Counseling or Therapy, Last 4 Weeks": "Received Counseling",
    "Took Prescription Medication for Mental Health, Last 4 Weeks": "Took Medication",
    "Took Prescription Medication for Mental Health And/Or Received Counseling or Therapy, "
    "Last 4 Weeks": "Medication and/or Counseling",
}

# ----------------------------------------------------------------- helpers
con = duckdb.connect()
# Keep memory modest on a laptop; spill to disk instead of crashing
con.execute("SET memory_limit = '4GB'")
con.execute(f"SET temp_directory = '{(ROOT / 'data' / '.duckdb_tmp').as_posix()}'")
report: list[str] = [f"# Validation Report\n\nGenerated {datetime.now():%Y-%m-%d %H:%M}\n"]
failures = 0


def log(msg: str = "") -> None:
    print(msg)
    report.append(msg)


def check(name: str, passed: bool, detail: str, severity: str = "ERROR") -> None:
    global failures
    status = "PASS" if passed else severity
    if not passed and severity == "ERROR":
        failures += 1
    log(f"| {status} | {name} | {detail} |")


def num(col: str) -> str:
    """Text -> DOUBLE. Blanks become NULL (CMS suppresses small counts; NULL != 0)."""
    return f"TRY_CAST(NULLIF(trim(replace(\"{col}\", ',', '')), '') AS DOUBLE)"


def csvs(pattern: str) -> str:
    return (f"read_csv('{(RAW / pattern).as_posix()}', all_varchar=true, header=true, "
            f"delim=',', quote='\"', filename=true, union_by_name=true)")


def lookup_table(name: str, mapping: dict, k: str, v: str) -> None:
    rows = ", ".join(f"('{a.replace(chr(39), chr(39)*2)}', '{b}')" for a, b in mapping.items())
    con.execute(f"CREATE OR REPLACE TEMP TABLE {name} AS "
                f"SELECT * FROM (VALUES {rows}) t({k}, {v})")


def scalar(sql: str):
    return con.execute(sql).fetchone()[0]


OUT.mkdir(parents=True, exist_ok=True)
lookup_table("ref_bh_types", BH_PROVIDER_TYPES, "provider_type", "bh_category")
lookup_table("ref_hcpcs", BH_HCPCS, "ref_code", "service_category")
lookup_table("ref_states", STATES, "state_name", "state")
lookup_table("ref_cdc", CDC_INDICATORS, "indicator_raw", "indicator")

# ================================================================ 1. providers
print("Building bh_providers ...")
con.execute(f"""
CREATE OR REPLACE TABLE providers_all AS
SELECT
    CAST(regexp_extract(filename, 'provider_(\\d{{4}})', 1) AS INTEGER) AS year,
    trim(Rndrng_NPI)                         AS npi,
    trim(Rndrng_Prvdr_Type)                  AS provider_type,
    trim(Rndrng_Prvdr_Crdntls)               AS credentials,
    trim(Rndrng_Prvdr_Ent_Cd)                AS entity_code,
    trim(Rndrng_Prvdr_Last_Org_Name)         AS last_or_org_name,
    trim(Rndrng_Prvdr_First_Name)            AS first_name,
    trim(Rndrng_Prvdr_City)                  AS city,
    upper(trim(Rndrng_Prvdr_State_Abrvtn))   AS state,
    lpad(trim(Rndrng_Prvdr_Zip5), 5, '0')    AS zip5,
    trim(Rndrng_Prvdr_Cntry)                 AS country,
    {num('Rndrng_Prvdr_RUCA')}               AS ruca,
    trim(Rndrng_Prvdr_RUCA_Desc)             AS ruca_desc,
    trim(Rndrng_Prvdr_Mdcr_Prtcptg_Ind)      AS medicare_participating,
    {num('Tot_HCPCS_Cds')}                   AS tot_hcpcs_codes,
    {num('Tot_Benes')}                       AS tot_benes,
    {num('Tot_Srvcs')}                       AS tot_services,
    {num('Tot_Sbmtd_Chrg')}                  AS tot_submitted_charge,
    {num('Tot_Mdcr_Alowd_Amt')}              AS tot_allowed_amt,
    {num('Tot_Mdcr_Pymt_Amt')}               AS tot_payment_amt,
    {num('Tot_Mdcr_Stdzd_Amt')}              AS tot_standardized_amt,
    {num('Bene_Avg_Age')}                    AS bene_avg_age,
    {num('Bene_Avg_Risk_Scre')}              AS bene_avg_risk_score,
    {num('Bene_Dual_Cnt')}                   AS bene_dual_cnt,
    {num('Bene_Feml_Cnt')}                   AS bene_female_cnt,
    {num('Bene_Male_Cnt')}                   AS bene_male_cnt,
    {num('Bene_CC_BH_Depress_V1_Pct')}       AS bene_pct_depression,
    {num('Bene_CC_BH_Anxiety_V1_Pct')}       AS bene_pct_anxiety,
    {num('Bene_CC_BH_Bipolar_V1_Pct')}       AS bene_pct_bipolar,
    {num('Bene_CC_BH_PTSD_V1_Pct')}          AS bene_pct_ptsd,
    {num('Bene_CC_BH_Schizo_OthPsy_V1_Pct')} AS bene_pct_schizophrenia,
    {num('Bene_CC_BH_Alcohol_Drug_V1_Pct')}  AS bene_pct_substance_use
FROM {csvs('provider_*.csv')}
""")

con.execute("""
CREATE OR REPLACE TABLE bh_providers AS
SELECT p.*,
       r.bh_category,
       CASE WHEN p.ruca IS NULL OR p.ruca >= 99 THEN 'Unknown'
            WHEN p.ruca < 4 THEN 'Metropolitan'
            WHEN p.ruca < 7 THEN 'Micropolitan'
            ELSE 'Small Town / Rural' END                     AS rurality,
       p.tot_payment_amt / NULLIF(p.tot_benes, 0)             AS payment_per_bene,
       p.tot_payment_amt / NULLIF(p.tot_services, 0)          AS payment_per_service,
       p.tot_payment_amt / NULLIF(p.tot_submitted_charge, 0)  AS payment_to_charge_ratio
FROM providers_all p
JOIN ref_bh_types r USING (provider_type)
WHERE p.state IN (SELECT state FROM ref_states)
""")

con.execute("""
CREATE OR REPLACE TABLE state_provider_totals AS
SELECT year, state,
       count(*)                        AS all_providers,
       count(*) FILTER (WHERE r.provider_type IS NOT NULL) AS bh_providers,
       sum(tot_benes)                  AS all_benes,
       sum(tot_payment_amt)            AS all_payment_amt
FROM providers_all p
LEFT JOIN ref_bh_types r USING (provider_type)
WHERE state IN (SELECT state FROM ref_states)
GROUP BY ALL
""")

# ================================================================ 2. geo services
print("Building bh_services_geo ...")
con.execute(f"""
CREATE OR REPLACE TABLE bh_services_geo AS
SELECT
    CAST(regexp_extract(filename, 'geo_service_(\\d{{4}})', 1) AS INTEGER) AS year,
    trim(Rndrng_Prvdr_Geo_Lvl)               AS geo_level,
    trim(Rndrng_Prvdr_Geo_Desc)              AS geo_desc,
    s.state                                  AS state,
    trim(HCPCS_Cd)                           AS hcpcs_cd,
    trim(HCPCS_Desc)                         AS hcpcs_desc,
    h.service_category,
    trim(Place_Of_Srvc)                      AS place_of_service,
    {num('Tot_Rndrng_Prvdrs')}               AS tot_providers,
    {num('Tot_Benes')}                       AS tot_benes,
    {num('Tot_Srvcs')}                       AS tot_services,
    {num('Avg_Sbmtd_Chrg')}                  AS avg_submitted_charge,
    {num('Avg_Mdcr_Alowd_Amt')}              AS avg_allowed_amt,
    {num('Avg_Mdcr_Pymt_Amt')}               AS avg_payment_amt,
    {num('Avg_Mdcr_Stdzd_Amt')}              AS avg_standardized_amt,
    {num('Avg_Mdcr_Pymt_Amt')} * {num('Tot_Srvcs')} AS est_total_payment
FROM {csvs('geo_service_*.csv')} g
JOIN ref_hcpcs h ON trim(g.HCPCS_Cd) = h.ref_code
LEFT JOIN ref_states s ON trim(g.Rndrng_Prvdr_Geo_Desc) = s.state_name
WHERE trim(Rndrng_Prvdr_Geo_Lvl) = 'National' OR s.state IS NOT NULL
""")

# ================================================================ 3. CDC demand
print("Building cdc_mental_health ...")
fmts = "['%m/%d/%Y', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S.%f']"
con.execute(f"""
CREATE OR REPLACE TABLE cdc_mental_health AS
SELECT
    i.indicator,
    regexp_replace(trim("Group"), '^By ', '')           AS group_name,
    trim(c.State)                                        AS state_name,
    s.state                                              AS state,
    trim(Subgroup)                                       AS subgroup,
    trim(Phase)                                          AS phase,
    TRY_CAST(trim("Time Period") AS INTEGER)             AS time_period,
    trim("Time Period Label")                            AS time_period_label,
    CAST(try_strptime("Time Period Start Date", {fmts}) AS DATE) AS start_date,
    CAST(try_strptime("Time Period End Date", {fmts}) AS DATE)   AS end_date,
    year(try_strptime("Time Period Start Date", {fmts}))         AS year,
    {num('Value')}                                       AS value_pct,
    {num('LowCI')}                                       AS low_ci,
    {num('HighCI')}                                      AS high_ci,
    {num('Value')} IS NULL                               AS is_suppressed
FROM {csvs('cdc_mental_health_care.csv')} c
JOIN ref_cdc i ON trim(c.Indicator) = i.indicator_raw
LEFT JOIN ref_states s ON trim(c.State) = s.state_name
""")

# ================================================================ 4. validation
log("## Row counts\n")
log("| Table | Rows |")
log("|---|---:|")
for t in ["providers_all", "bh_providers", "state_provider_totals",
          "bh_services_geo", "cdc_mental_health"]:
    log(f"| {t} | {scalar(f'SELECT count(*) FROM {t}'):,} |")

log("\n## Behavioral-health providers by category and year\n")
rows = con.execute("""PIVOT (SELECT bh_category, year FROM bh_providers)
                      ON year USING count(*) GROUP BY bh_category ORDER BY 1""")
cols = [d[0] for d in rows.description]
log("| " + " | ".join(cols) + " |")
log("|---|" + "---:|" * (len(cols) - 1))
for r in rows.fetchall():
    log(f"| {r[0]} | " + " | ".join(f"{(v or 0):,}" for v in r[1:]) + " |")

log("\n## Checks\n")
log("| Status | Check | Detail |")
log("|---|---|---|")

# -- completeness / keys
dup = scalar("SELECT count(*) - count(DISTINCT (year, npi)) FROM bh_providers")
check("Unique NPI per year", dup == 0, f"{dup:,} duplicate (year, npi) pairs")

years = [r[0] for r in con.execute("SELECT DISTINCT year FROM bh_providers ORDER BY 1").fetchall()]
check("All provider years present", years == list(range(2019, 2025)), f"years = {years}")

dropped = scalar("""SELECT count(*) FROM providers_all p JOIN ref_bh_types USING (provider_type)
                    WHERE p.state NOT IN (SELECT state FROM ref_states) OR p.state IS NULL""")
check("BH providers outside 50 states + DC (dropped)", True,
      f"{dropped:,} rows excluded (territories / foreign / military codes)", "INFO")

n_states = scalar("SELECT count(DISTINCT state) FROM bh_providers")
check("All 51 jurisdictions have BH providers", n_states == 51, f"{n_states} states")

# -- type parsing: values present in text but failed numeric conversion
bad_num = scalar(f"""
    SELECT count(*) FROM {csvs('provider_*.csv')}
    WHERE NULLIF(trim(Tot_Mdcr_Pymt_Amt), '') IS NOT NULL AND {num('Tot_Mdcr_Pymt_Amt')} IS NULL""")
check("Payment amounts parse as numbers", bad_num == 0, f"{bad_num:,} unparseable values")

# -- business rules
neg = scalar("""SELECT count(*) FROM bh_providers
                WHERE tot_payment_amt < 0 OR tot_allowed_amt < 0 OR tot_submitted_charge < 0""")
check("No negative dollar amounts", neg == 0, f"{neg:,} rows")

null_pay = scalar("SELECT count(*) FROM bh_providers WHERE tot_payment_amt IS NULL")
check("Payment amount populated", null_pay == 0, f"{null_pay:,} NULL payment rows")

over = scalar("SELECT avg((tot_payment_amt > tot_allowed_amt * 1.001)::INT) * 100 FROM bh_providers")
check("Paid <= Allowed", over < 1, f"{over:.2f}% of rows violate", "WARN")

over2 = scalar("""SELECT avg((tot_allowed_amt > tot_submitted_charge * 1.001)::INT) * 100
                  FROM bh_providers""")
check("Allowed <= Submitted charge", over2 < 5, f"{over2:.2f}% of rows violate", "WARN")

low_benes = scalar("SELECT count(*) FROM bh_providers WHERE tot_benes < 11")
check("CMS suppression rule (benes >= 11)", low_benes == 0,
      f"{low_benes:,} providers below 11 beneficiaries", "WARN")

geo_codes = scalar("SELECT count(DISTINCT hcpcs_cd) FROM bh_services_geo")
check("BH HCPCS codes found in geo data", geo_codes >= 15,
      f"{geo_codes} of {len(BH_HCPCS)} reference codes present", "WARN")

geo_states = scalar("SELECT count(DISTINCT state) FROM bh_services_geo WHERE geo_level = 'State'")
check("Geo data covers 51 jurisdictions", geo_states == 51, f"{geo_states} states")

# -- CDC
cdc_ind = scalar("SELECT count(DISTINCT indicator) FROM cdc_mental_health")
check("All 4 CDC indicators mapped", cdc_ind == 4, f"{cdc_ind} mapped")

cdc_rows_raw = scalar(f"SELECT count(*) FROM {csvs('cdc_mental_health_care.csv')}")
cdc_rows = scalar("SELECT count(*) FROM cdc_mental_health")
check("No CDC rows lost in mapping", cdc_rows == cdc_rows_raw, f"{cdc_rows:,} of {cdc_rows_raw:,}")

unmapped = scalar("""SELECT count(DISTINCT state_name) FROM cdc_mental_health
                     WHERE group_name = 'State' AND state IS NULL""")
check("CDC state names map to codes", unmapped == 0, f"{unmapped} unmapped names")

rng = scalar("SELECT count(*) FROM cdc_mental_health WHERE value_pct < 0 OR value_pct > 100")
check("CDC percentages within 0-100", rng == 0, f"{rng:,} out-of-range values")

ci = scalar("""SELECT count(*) FROM cdc_mental_health
               WHERE NOT is_suppressed AND (value_pct < low_ci OR value_pct > high_ci)""")
check("CDC value within its confidence interval", ci == 0, f"{ci:,} rows violate")

bad_dates = scalar("SELECT count(*) FROM cdc_mental_health WHERE start_date IS NULL")
check("CDC dates parsed", bad_dates == 0, f"{bad_dates:,} unparsed dates")

sup = scalar("SELECT count(*) FROM cdc_mental_health WHERE is_suppressed")
check("CDC suppressed estimates kept as NULL", True, f"{sup:,} rows flagged is_suppressed", "INFO")

# ================================================================ 5. write parquet
print("\nWriting Parquet ...")
for t in ["bh_providers", "state_provider_totals", "bh_services_geo", "cdc_mental_health"]:
    path = (OUT / f"{t}.parquet").as_posix()
    con.execute(f"COPY {t} TO '{path}' (FORMAT parquet, COMPRESSION zstd)")
    print(f"  {path}")

log(f"\n**Result: {'FAILED' if failures else 'PASSED'}** ({failures} error-level failures)")
REPORT.parent.mkdir(exist_ok=True)
REPORT.write_text("\n".join(report))
print(f"\nReport written to {REPORT}")
sys.exit(1 if failures else 0)