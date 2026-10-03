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