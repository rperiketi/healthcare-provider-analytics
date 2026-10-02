"""
Phase 2A - Data Profiling
-------------------------
Profiles every raw file (row counts, schema drift across years, null rates,
duplicate keys, behavioral-health coverage) and writes a Markdown report to
docs/data_profile.md.

Usage:
    python src/profile_data.py
"""
import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DOCS = ROOT / "docs"
REPORT = DOCS / "data_profile.md"

# Keywords used to spot behavioral-health provider types
BH_PATTERN = r"(?i)psych|social work|counsel|marriage|mental|behavior|addiction"
# Common psychotherapy / psychiatric evaluation HCPCS codes
BH_HCPCS = ["90791", "90792", "90832", "90834", "90837", "90846", "90847", "90853"]

con = duckdb.connect()
lines: list[str] = []


def out(text: str = "") -> None:
    print(text)
    lines.append(text)


def src(path: Path) -> tuple[str, str, int]:
    """Return (sql_source, encoding, row_count). Tries UTF-8 on the full file,
    falls back to latin-1 if any invalid bytes are found."""
    base = f"read_csv('{path.as_posix()}', all_varchar=true, header=true, delim=',', quote='\"'"
    for enc, source in [("utf-8", base + ")"), ("latin-1", base + ", encoding='latin-1')")]:
        try:
            n = con.execute(f"SELECT count(*) FROM {source}").fetchone()[0]
            return source, enc, n
        except duckdb.Error:
            try:
                con.execute("ROLLBACK")
            except duckdb.Error:
                pass
    raise RuntimeError(f"Could not read {path.name} as UTF-8 or latin-1")


def columns(source: str) -> list[str]:
    return [r[0] for r in con.sql(f"DESCRIBE SELECT * FROM {source}").fetchall()]


def find_col(cols: list[str], pattern: str) -> str | None:
    return next((c for c in cols if re.search(pattern, c, re.I)), None)


def year_of(path: Path) -> int:
    return int(re.search(r"(\d{4})", path.stem).group(1))


# ---------------------------------------------------------------- 1. inventory
out("# Data Profile Report\n")
out("## 1. File inventory\n")
out("| File | Rows | Columns | Encoding |")
out("|---|---:|---:|---|")
schemas: dict[str, dict[int, list[str]]] = {"provider": {}, "geo_service": {}}
sources: dict[Path, str] = {}

for f in sorted(RAW.glob("*.csv")):
    s, enc, n = src(f)
    sources[f] = s
    cols = columns(s)
    out(f"| {f.name} | {n:,} | {len(cols)} | {enc} |")
    for fam in schemas:
        if f.stem.startswith(fam + "_"):
            schemas[fam][year_of(f)] = cols

# ---------------------------------------------------------- 2. schema drift
out("\n## 2. Schema drift across years\n")
for fam, by_year in schemas.items():
    if not by_year:
        continue
    all_cols = sorted(set().union(*by_year.values()))
    drift = {c: [y for y in by_year if c not in by_year[y]] for c in all_cols}
    drift = {c: ys for c, ys in drift.items() if ys}
    out(f"**{fam}**: {len(all_cols)} distinct columns across {sorted(by_year)}")
    if drift:
        for c, ys in drift.items():
            out(f"- `{c}` missing in {ys}")
    else:
        out("- No drift: identical columns every year")
    latest = max(by_year)
    out(f"\nColumns ({fam} {latest}): `" + "`, `".join(by_year[latest]) + "`\n")

# ------------------------------------------------- 3. provider deep dive
prov_files = sorted(RAW.glob("provider_*.csv"))
if prov_files:
    latest = prov_files[-1]
    s = sources[latest]
    cols = columns(s)
    out(f"\n## 3. Provider file checks ({latest.name})\n")

    npi = find_col(cols, r"npi$")
    if npi:
        total, distinct = con.sql(f'SELECT count(*), count(DISTINCT "{npi}") FROM {s}').fetchone()
        out(f"- Key `{npi}`: {total:,} rows, {distinct:,} distinct, "
            f"{total - distinct:,} duplicates")

    null_exprs = ", ".join(
        f"""round(100.0 * count(*) FILTER (WHERE "{c}" IS NULL OR trim("{c}") = '') / count(*), 1)"""
        for c in cols)
    null_pcts = con.sql(f"SELECT {null_exprs} FROM {s}").fetchone()
    nulls = sorted(((p, c) for c, p in zip(cols, null_pcts) if p > 0), reverse=True)
    out(f"- Columns with blanks: {len(nulls)} of {len(cols)}")
    out("\n| Column | % blank |")
    out("|---|---:|")
    for p, c in nulls[:25]:
        out(f"| {c} | {p} |")

    ptype = find_col(cols, r"prvdr_type|provider_type")
    if ptype:
        n_types = con.sql(f'SELECT count(DISTINCT "{ptype}") FROM {s}').fetchone()[0]
        out(f"\n**Provider types:** {n_types} distinct in `{ptype}`. "
            "Behavioral-health candidates by year:\n")
        yrs = [year_of(f) for f in prov_files]
        out("| Provider type | " + " | ".join(map(str, yrs)) + " |")
        out("|---|" + "---:|" * len(yrs))
        union = " UNION ALL ".join(
            f"""SELECT {year_of(f)} AS yr, "{ptype}" AS t FROM {sources[f]}
                WHERE regexp_matches("{ptype}", '{BH_PATTERN}')"""
            for f in prov_files)
        rows = con.sql(f"""
            PIVOT ({union}) ON yr USING count(*) GROUP BY t ORDER BY t""").fetchall()
        for r in rows:
            out(f"| {r[0]} | " + " | ".join(f"{(v or 0):,}" for v in r[1:]) + " |")

# ------------------------------------------------------ 4. geo checks
geo_files = sorted(RAW.glob("geo_service_*.csv"))
if geo_files:
    out("\n## 4. Geography & service checks\n")
    cols = columns(sources[geo_files[-1]])
    lvl = find_col(cols, r"geo_lvl")
    hcpcs = find_col(cols, r"^hcpcs_cd$")
    out("| Year | Geo levels | Distinct HCPCS | Behavioral-health HCPCS rows |")
    out("|---|---|---:|---:|")
    codes = ", ".join(f"'{c}'" for c in BH_HCPCS)
    for f in geo_files:
        s = sources[f]
        levels = [r[0] for r in con.sql(
            f'SELECT DISTINCT "{lvl}" FROM {s} ORDER BY 1').fetchall()] if lvl else ["?"]
        n_codes, n_bh = con.sql(f"""
            SELECT count(DISTINCT "{hcpcs}"),
                   count(*) FILTER (WHERE "{hcpcs}" IN ({codes}))
            FROM {s}""").fetchone() if hcpcs else ("?", "?")
        out(f"| {year_of(f)} | {', '.join(map(str, levels))} | {n_codes:,} | {n_bh:,} |")

# ------------------------------------------------------ 5. CDC checks
cdc = RAW / "cdc_mental_health_care.csv"
if cdc.exists():
    s = sources[cdc]
    cols = columns(s)
    out("\n## 5. CDC Household Pulse checks\n")
    out("Columns: `" + "`, `".join(cols) + "`\n")
    for label, pattern in [("Indicator", r"^indicator$"), ("Group", r"^group$")]:
        c = find_col(cols, pattern)
        if c:
            rows = con.sql(f'SELECT "{c}", count(*) FROM {s} GROUP BY 1 ORDER BY 1').fetchall()
            out(f"**{label} values:**")
            for v, n in rows:
                out(f"- {v} ({n:,} rows)")
            out()
    start = find_col(cols, r"start.?date")
    end = find_col(cols, r"end.?date")
    if start and end:
        fmts = "['%m/%d/%Y', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S.%f']"
        lo, hi = con.sql(f'SELECT min(try_strptime("{start}", {fmts})), '
                         f'max(try_strptime("{end}", {fmts})) FROM {s}').fetchone()
        out(f"- Date range: {lo} to {hi}")
    val = find_col(cols, r"^value$")
    if val:
        blank = con.sql(f"""SELECT count(*) FILTER (WHERE "{val}" IS NULL OR trim("{val}") = ''),
                            count(*) FROM {s}""").fetchone()
        out(f"- Blank `{val}`: {blank[0]:,} of {blank[1]:,} rows (suppressed estimates)")

DOCS.mkdir(exist_ok=True)
REPORT.write_text("\n".join(lines))
print(f"\nReport written to {REPORT}")