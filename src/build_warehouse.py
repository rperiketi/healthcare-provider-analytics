"""
Phase 3 - Build the DuckDB warehouse
------------------------------------
1. Runs sql/01_staging.sql ... sql/04_marts.sql in order
2. Runs every sql/tests/*.sql data test (a test passes when it returns 0 rows)
3. Exports dashboard tables to tableau/data/*.csv for Tableau Public

Usage:
    python src/build_warehouse.py
Exit code 1 if any SQL test fails (nothing is exported).
"""
import sys
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
DB_PATH = ROOT / "data" / "warehouse.duckdb"
EXPORT_DIR = ROOT / "tableau" / "data"

EXPORT_TABLES = [
    "dim_state", "dim_provider_type", "dim_service",
    "fct_state_supply", "fct_service_reimbursement", "fct_demand_state",
    "mart_national_kpis", "mart_category_trend", "mart_state_gap",
    "mart_service_mix", "mart_rural_access", "mart_demand_by_group",
    "mart_demand_trend", "mart_provider_detail",
]


def render(sql: str) -> str:
    return (sql.replace("{{PROCESSED}}", (ROOT / "data" / "processed").as_posix())
               .replace("{{RAW}}", (ROOT / "data" / "raw").as_posix()))


def main() -> int:
    con = duckdb.connect(str(DB_PATH))
    con.execute("SET memory_limit = '4GB'")

    # ---------------------------------------------------------------- models
    print("== Building models ==")
    for path in sorted(SQL_DIR.glob("[0-9][0-9]_*.sql")):
        start = time.time()
        con.execute(render(path.read_text()))
        print(f"  OK  {path.name:<20} {time.time() - start:5.1f}s")

    print("\n== Row counts ==")
    for t in EXPORT_TABLES:
        n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t:<28} {n:>10,}")

    # ---------------------------------------------------------------- tests
    print("\n== Data tests ==")
    failed = 0
    for path in sorted((SQL_DIR / "tests").glob("*.sql")):
        rows = con.execute(render(path.read_text())).fetchall()
        if rows:
            failed += 1
            print(f"  FAIL {path.stem}  ({len(rows)} rows), e.g. {rows[:3]}")
        else:
            print(f"  PASS {path.stem}")

    if failed:
        print(f"\n{failed} test(s) failed - nothing exported.")
        return 1

    # ---------------------------------------------------------------- export
    print("\n== Exporting for Tableau ==")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    for t in EXPORT_TABLES:
        out = (EXPORT_DIR / f"{t}.csv").as_posix()
        con.execute(f"COPY {t} TO '{out}' (HEADER, DELIMITER ',')")
    print(f"  {len(EXPORT_TABLES)} CSVs written to {EXPORT_DIR}")

    # ---------------------------------------------------------------- preview
    print("\n== Preview: top 10 access-gap states ==")
    print(con.sql("""
        SELECT access_gap_rank AS rank, state,
               round(unmet_need_pct, 1)             AS unmet_need_pct,
               round(providers_per_100k_2020_22, 1) AS providers_per_100k,
               providers_change_pct_2019_24         AS provider_chg_pct,
               access_gap_score, gap_quadrant
        FROM mart_state_gap ORDER BY access_gap_rank LIMIT 10"""))

    print("== Preview: national KPIs ==")
    print(con.sql("""
        SELECT year, bh_providers, round(providers_per_100k, 1) AS per_100k,
               providers_yoy_pct, round(payment_amt / 1e6, 1) AS payment_musd,
               round(payment_per_service, 2) AS pay_per_svc, providers_index_2019
        FROM mart_national_kpis ORDER BY year"""))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())