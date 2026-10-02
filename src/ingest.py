"""
Phase 1 - Data Ingestion
------------------------
Discovers CMS "Medicare Physician & Other Practitioners" datasets from the
official CMS data catalog (data.json) and downloads yearly CSVs to data/raw/.

Usage:
    python src/ingest.py --dry-run      # list available files, download nothing
    python src/ingest.py                # download all configured years
    python src/ingest.py --years 2023 2024
    python src/ingest.py --list-titles  # debug: show matching catalog titles
"""
import argparse
import html
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from tqdm import tqdm

CATALOG_URL = "https://data.cms.gov/data.json"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_YEARS = list(range(2019, 2025))  # 2019 = pre-COVID baseline, 2024 = latest

# Matched by keywords (robust to dashes, &amp;, spacing differences in the catalog)
DATASETS = {
    "geo_service": {"include": ["physician", "practitioners", "geography and service"],
                    "exclude": []},
    "provider": {"include": ["physician", "practitioners", "by provider"],
                 "exclude": ["service", "geography"]},
}

# Direct-download sources. Demand side: CDC/NCHS Household Pulse Survey (Aug 2020 - May 2022, state-level)
DIRECT_SOURCES = {
    "cdc_mental_health_care": "https://data.cdc.gov/api/views/yni7-er2q/rows.csv?accessType=DOWNLOAD",
    # Census state population estimates (for per-capita supply metrics)
    "census_pop_2020s": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/state/totals/NST-EST2025-ALLDATA.csv",
    "census_pop_2010s": "https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/national/totals/nst-est2019-alldata.csv",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("ingest")


def load_catalog() -> list[dict]:
    log.info("Fetching CMS catalog...")
    resp = requests.get(CATALOG_URL, timeout=120)
    resp.raise_for_status()
    return resp.json()["dataset"]


def normalize(text: str) -> str:
    """Lowercase, unescape HTML, unify dashes, collapse whitespace."""
    text = html.unescape(text or "").lower()
    text = re.sub(r"[\u2010-\u2015\-]+", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def find_datasets(catalog: list[dict], rule: dict) -> list[dict]:
    """CMS publishes one catalog entry per year, e.g. '... - by Provider : 2024-12-01'."""
    return [
        d for d in catalog
        if "medicare" in normalize(d.get("title"))
        and all(k in normalize(d.get("title")) for k in rule["include"])
        and not any(k in normalize(d.get("title")) for k in rule["exclude"])
    ]


def find_csv_links(catalog: list[dict], rule: dict) -> dict[int, str]:
    """Return {year: csv_url}, reading the year from each yearly entry's title."""
    matches = find_datasets(catalog, rule)
    if not matches:
        raise ValueError(f"No dataset matched {rule}. Run with --list-titles to inspect.")

    links = {}
    for ds in matches:
        year_match = re.search(r"(\d{4})-\d{2}-\d{2}", ds.get("title", ""))
        if not year_match:
            continue  # skip any un-dated parent entry
        year = int(year_match.group(1))

        csv_url = None
        for dist in ds.get("distribution", []):
            url = dist.get("downloadURL") or dist.get("accessURL") or ""
            if dist.get("mediaType") == "text/csv" or url.lower().endswith(".csv"):
                csv_url = url
                break
        if csv_url:
            links[year] = csv_url
        else:
            types = [d.get("mediaType") for d in ds.get("distribution", [])]
            log.warning("No CSV distribution in %r (media types: %s)", ds["title"], types)
    return links


def download(url: str, dest: Path) -> int:
    """Stream a file to disk; skip if it already exists. Returns size in bytes."""
    if dest.exists() and dest.stat().st_size > 0:
        log.info("Skip (already exists): %s", dest.name)
        return dest.stat().st_size

    tmp = dest.with_suffix(".part")
    with requests.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        with open(tmp, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=dest.name
        ) as bar:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                bar.update(len(chunk))
    tmp.rename(dest)  # only rename once the download fully succeeded
    return dest.stat().st_size


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-titles", action="store_true",
                        help="print catalog titles containing 'physician' and exit")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()

    if args.list_titles:
        for d in catalog:
            if "physician" in normalize(d.get("title")):
                print(repr(d["title"]))
        return
    manifest = {"retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "files": []}

    for key, rule in DATASETS.items():
        links = find_csv_links(catalog, rule)
        title = re.split(r"\s*:\s*\d{4}", find_datasets(catalog, rule)[0]["title"])[0]
        log.info("%s -> years available: %s", key, sorted(links))

        for year in args.years:
            if year not in links:
                log.warning("%s: no CSV found for %s", key, year)
                continue
            dest = RAW_DIR / f"{key}_{year}.csv"
            if args.dry_run:
                log.info("[dry-run] %s %s -> %s", key, year, links[year])
                continue
            size = download(links[year], dest)
            manifest["files"].append(
                {"dataset": title, "year": year, "file": dest.name,
                 "url": links[year], "bytes": size}
            )

    for key, url in DIRECT_SOURCES.items():
        dest = RAW_DIR / f"{key}.csv"
        if args.dry_run:
            log.info("[dry-run] %s -> %s", key, url)
            continue
        size = download(url, dest)
        manifest["files"].append({"dataset": key, "year": None, "file": dest.name,
                                  "url": url, "bytes": size})

    if not args.dry_run:
        (RAW_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
        log.info("Done. Manifest written to %s", RAW_DIR / "manifest.json")


if __name__ == "__main__":
    main()