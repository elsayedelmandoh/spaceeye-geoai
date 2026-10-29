"""Export coded source provenance and exact generation settings,never raw quotes/name mapping."""

from urllib.parse import urlparse

import pandas as pd

from src.pipeline import gates, run_all
from src.pipeline.common import BASE_DIR, CFG, PRIVATE, REAL, SRC
from src.pipeline.component_data import write_json


def main():
    out = BASE_DIR / "data"
    reference = SRC / "26_data_audit/reference"
    patterns = gates._patterns(gates.forbidden_names())
    registry = pd.read_csv(reference / "records_register.csv").fillna("")
    statuses = registry.drop_duplicates("record_id").set_index("record_id")
    used = set(pd.read_parquet(REAL / "statements.parquet").record_id.dropna())
    links = []
    for path in sorted(reference.glob("live_quote_*.csv")):
        frame = pd.read_csv(path)
        if {"record_id", "url"} <= set(frame):
            links.extend(frame[["record_id", "url"]].dropna().to_dict("records"))
    local = pd.read_csv(PRIVATE / "evidence_sources.csv")
    links.extend(local[["record_id", "url"]].dropna().to_dict("records"))
    rows = []
    for row in links:
        record, url = str(row["record_id"]), str(row["url"])
        safe = not gates._hits(url, patterns)
        domain = urlparse(url).netloc
        info = statuses.loc[record] if record in statuses.index else {}
        rows.append({"record_id": record, "scope": "current_statement_evidence" if record in used else "background_audit_reference",
                     "domain": domain if not gates._hits(domain, patterns) else "withheld",
                     "url": url if safe else "", "url_status": "included" if safe else "withheld_project_name_in_URL",
                     "published_date": info.get("published_date", ""), "recorded_verdict": info.get("team_verdict", ""),
                     "recorded_decision": info.get("decision", ""), "source_domain_group": info.get("dataset", "")})
    present = {r["record_id"] for r in rows}
    for record in sorted(set(statuses.index) | used):
        if record not in present:
            info = statuses.loc[record] if record in statuses.index else {}
            rows.append({"record_id": record, "scope": "current_statement_evidence" if record in used else "background_audit_reference",
                         "domain": "", "url": "", "url_status": "not_available_in_local_link_registry",
                         "published_date": info.get("published_date", ""), "recorded_verdict": info.get("team_verdict", ""),
                         "recorded_decision": info.get("decision", ""), "source_domain_group": info.get("dataset", "")})
    catalog = pd.DataFrame(rows).drop_duplicates(["record_id", "url", "url_status"]).sort_values(["scope", "record_id", "url"])
    catalog.to_csv(out / "SOURCE_CATALOG.csv", index=False, encoding="utf-8-sig")
    inputs = []
    for key, value in CFG["sources"].items():
        if "*" in value:
            paths = sorted(SRC.glob(value))
        else:
            path = SRC / value
            paths = sorted(path.glob("*.csv")) if path.is_dir() else [path]
        for path in paths:
            if path.is_file():
                inputs.append({"config_key": key, "source_file": path.relative_to(SRC).as_posix(), "sha256": run_all.sha(path), "kind": "cached_source_or_reference"})
    pd.DataFrame(inputs).to_csv(out / "SOURCE_INPUTS.csv", index=False)
    write_json(out / "GENERATION_PARAMETERS.json", {k: CFG[k] for k in ["seed", "computed_on", "scope_districts", "levels", "cycle_capacity", "fines", "compounds", "drivers", "generator"]})
    print(f"source catalog:{len(catalog)}coded references;input inventory:{len(inputs)}files;no raw quotes/name mapping exported")


if __name__ == "__main__":
    main()
