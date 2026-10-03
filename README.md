# Healthcare Analytics & Provider Trends Dashboard

**[View Live Dashboard on Tableau Public →] https://public.tableau.com/app/profile/renusri.periketi4831/viz/Book1_17909944772050/MedicareMentalHealthAccess2019-2024**

## Overview
An interactive Tableau dashboard analyzing Medicare behavioral health provider
trends, geographic access gaps, and reimbursement patterns from 2019–2024.
Built on official CMS and CDC federal datasets.

**Key finding:** The Medicare behavioral health workforce shrank ~19% (like-for-like)
from 2019–2024, with the steepest declines among psychologists and social workers.
States with the lowest provider density also report the highest unmet counseling need.

## Tech Stack
- **Python** (pandas, DuckDB) — data ingestion, cleaning, validation
- **SQL** — layered warehouse (staging → dimensions → facts → marts), 8 automated data tests
- **Tableau** — interactive dashboard with map, trend lines, scatter plots, and heatmap

## Data Sources
- [CMS Medicare Physician & Other Practitioners](https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners) (by Provider, and by Geography and Service), 2019–2024
- [CDC Household Pulse Survey — Mental Health Care in the Last 4 Weeks](https://data.cdc.gov/National-Center-for-Health-Statistics/Mental-Health-Care-in-the-Last-4-Weeks/yni7-er2q), 2020–2022
- [U.S. Census Bureau state population estimates](https://www.census.gov/programs-surveys/popest.html)

## Pipeline

data/raw (CSV) → src/clean_data.py → data/processed (Parquet)
→ src/build_warehouse.py (DuckDB + SQL) → tableau/data (CSV)
→ src/analyze.py (statistical findings, figures)
→ Tableau Public dashboard


## Project Structure

├── src/ Python ETL and analysis scripts
├── sql/ Layered SQL models + automated data tests
├── data/raw/ Raw CMS/CDC downloads (not tracked in git)
├── data/processed/ Cleaned Parquet files (not tracked in git)
├── tableau/data/ CSV exports feeding the dashboard
├── docs/ Data profile, validation report, analysis findings
└── docs/figures/ Supporting charts (PNG)


## Key Findings
See [`docs/analysis_findings.md`](docs/analysis_findings.md) for the full statistical
write-up, including sensitivity analysis on the Access Gap Score and provider
billing outlier detection.

## Reproducing This Project
```bash
pip install -r requirements.txt
python src/ingest.py        # download CMS/CDC/Census data
python src/clean_data.py    # clean + validate
python src/build_warehouse.py  # build SQL warehouse, run tests, export
python src/analyze.py       # statistical analysis + figures
```