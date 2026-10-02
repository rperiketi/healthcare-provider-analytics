# Validation Report

Generated 2026-10-02 18:04

## Row counts

| Table | Rows |
|---|---:|
| providers_all | 7,302,541 |
| bh_providers | 322,304 |
| state_provider_totals | 306 |
| bh_services_geo | 10,528 |
| cdc_mental_health | 10,404 |

## Behavioral-health providers by category and year

| bh_category | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|
| Counselor / MFT | 0 | 0 | 0 | 0 | 0 | 3,458 |
| Psychiatry | 22,414 | 21,595 | 21,234 | 20,840 | 20,416 | 20,362 |
| Psychologist | 16,172 | 14,485 | 13,551 | 12,924 | 12,516 | 11,961 |
| Social Worker | 21,765 | 19,324 | 18,209 | 17,451 | 17,199 | 16,428 |

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | Unique NPI per year | 0 duplicate (year, npi) pairs |
| PASS | All provider years present | years = [2019, 2020, 2021, 2022, 2023, 2024] |
| PASS | BH providers outside 50 states + DC (dropped) | 722 rows excluded (territories / foreign / military codes) |
| PASS | All 51 jurisdictions have BH providers | 51 states |
| PASS | Payment amounts parse as numbers | 0 unparseable values |
| PASS | No negative dollar amounts | 0 rows |
| PASS | Payment amount populated | 0 NULL payment rows |
| PASS | Paid <= Allowed | 0.00% of rows violate |
| PASS | Allowed <= Submitted charge | 0.02% of rows violate |
| PASS | CMS suppression rule (benes >= 11) | 0 providers below 11 beneficiaries |
| PASS | BH HCPCS codes found in geo data | 21 of 21 reference codes present |
| PASS | Geo data covers 51 jurisdictions | 51 states |
| PASS | All 4 CDC indicators mapped | 4 mapped |
| PASS | No CDC rows lost in mapping | 10,404 of 10,404 |
| PASS | CDC state names map to codes | 0 unmapped names |
| PASS | CDC percentages within 0-100 | 0 out-of-range values |
| PASS | CDC value within its confidence interval | 0 rows violate |
| PASS | CDC dates parsed | 0 unparsed dates |
| PASS | CDC suppressed estimates kept as NULL | 490 rows flagged is_suppressed |

**Result: PASSED** (0 error-level failures)