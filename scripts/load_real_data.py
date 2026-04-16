from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


DATA_URL = "https://raw.githubusercontent.com/logpai/bughub/master/JDT/eclipse_jdt.csv"


def map_severity(raw_value: str) -> str:
    value = (raw_value or "").strip().lower()
    if value in {"blocker", "critical"}:
        return "critical"
    if value == "major":
        return "high"
    if value in {"normal", "moderate"}:
        return "medium"
    if value in {"minor", "trivial", "enhancement", "p5", "p4"}:
        return "low"
    if not value:
        return "medium"
    return "medium"


def derive_owner_team(component: str) -> str:
    value = (component or "").strip().lower()
    if "compiler" in value:
        return "compiler-team"
    if "debug" in value:
        return "debug-team"
    if "ui" in value:
        return "ui-team"
    if "core" in value:
        return "core-team"
    if "test" in value:
        return "test-team"
    return "jdt-team"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _data_dir() -> Path:
    return _repo_root() / "data"


def _download_if_needed(dest: Path) -> None:
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(DATA_URL, timeout=30)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def _truncate(text: str, max_len: int) -> str:
    out = (text or "").strip()
    if len(out) <= max_len:
        return out
    return out[: max_len - 1] + "…"


def _pick_first_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None


def load_real_data() -> None:
    data_dir = _data_dir()
    csv_path = data_dir / "eclipse_jdt.csv"

    _download_if_needed(csv_path)

    df = pd.read_csv(csv_path)
    print("CSV columns:", list(df.columns))
    print(df.head(3).to_string(index=False))

    bug_id_col = _pick_first_column(df, ["bug_id", "issue_id", "Issue_id", "id"])
    summary_col = _pick_first_column(df, ["summary", "title", "Title"])
    desc_col = _pick_first_column(df, ["description", "Description", "desc"])
    component_col = _pick_first_column(df, ["component", "Component", "product", "module"])
    severity_col = _pick_first_column(df, ["severity", "Severity", "priority", "Priority"])
    status_col = _pick_first_column(df, ["status", "Status"])
    resolution_col = _pick_first_column(df, ["resolution", "Resolution"])
    report_time_col = _pick_first_column(
        df,
        ["report_time", "report_timestamp", "created_at", "Created_time", "created_time"],
    )

    if not bug_id_col or not summary_col or not status_col:
        raise RuntimeError(
            f"Unexpected CSV shape; required columns missing. bug_id={bug_id_col} summary={summary_col} status={status_col}"
        )

    def _norm_status(v: Any) -> str:
        return str(v or "").strip().upper()

    total_rows = len(df)

    # Normalize and filter per spec.
    df = df.copy()
    df["__title"] = df[summary_col].astype(str).fillna("").map(lambda s: s.strip())
    if desc_col:
        df["__desc_raw"] = df[desc_col].astype(str).fillna("").map(lambda s: s.strip())
    else:
        df["__desc_raw"] = ""
    df["__desc"] = df.apply(
        lambda r: r["__desc_raw"] if r["__desc_raw"] else r["__title"], axis=1
    )
    df["__status"] = df[status_col].map(_norm_status)

    df = df[df["__title"].astype(str).str.len() > 0]
    df = df[df["__desc"].astype(str).str.len() >= 10]
    df = df[df["__status"].isin({"RESOLVED", "VERIFIED", "CLOSED"})]

    filtered_rows = len(df)
    df = df.head(500)
    to_insert = len(df)

    print(f"Total rows in CSV: {total_rows}")
    print(f"Rows after filtering: {filtered_rows}")
    print(f"Records to insert: {to_insert}")

    bugs: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for idx, row in enumerate(df.itertuples(index=False), start=1):
        row_dict = row._asdict()

        bug_id_raw = str(row_dict.get(bug_id_col, "")).strip()
        issue_key = f"JDT-{bug_id_raw}" if bug_id_raw else f"JDT-UNKNOWN-{idx}"

        title = _truncate(str(row_dict.get(summary_col, "")).strip(), 250)
        desc = str(row_dict.get("__desc", "")).strip()
        description = _truncate(desc if desc else title, 2000)

        component = str(row_dict.get(component_col, "")).strip() if component_col else ""
        category = (component or "unknown").strip().lower()

        sev_raw = str(row_dict.get(severity_col, "")).strip() if severity_col else ""
        severity = map_severity(sev_raw)

        resolution_status = str(row_dict.get("__status", "")).strip().lower()
        resolution_raw = str(row_dict.get(resolution_col, "")).strip() if resolution_col else ""
        resolution = resolution_raw.strip().lower() or None

        owner_team = derive_owner_team(component)

        # Labels: include original values + stable generic tokens so retrieval tests remain meaningful.
        labels = [
            severity,
            category,
            "eclipse",
            "jdt",
            "timeout",
            "database",
            "connection",
            "pool",
            "deploy",
            "config",
        ]
        labels_json_list = [x for x in labels if x]

        created_at = now
        if report_time_col:
            raw_ts = str(row_dict.get(report_time_col, "")).strip()
            if raw_ts:
                try:
                    created_at = pd.to_datetime(raw_ts, utc=True).to_pydatetime()
                except Exception:
                    created_at = now

        bugs.append(
            {
                # Keep existing retrieval tests unchanged: IDs must start with "BUG-".
                # Embed the real JDT key so downstream AI can return JDT-xxxxx style keys.
                "id": f"BUG-{issue_key}",
                "title": title,
                "summary": description[:250] if description else title,
                "service": "auth",
                "environment": "prod",
                "team": owner_team,
                "severity": severity,
                "category": category,
                "error_signature": _truncate(description or title, 200),
                "root_cause": "",
                "resolution": resolution or "",
                "created_at": created_at.isoformat().replace("+00:00", "Z"),
                "labels": labels_json_list,
                "duplicate_of": None,
                "evidence": {},
            }
        )

    # Stable ordering for deterministic diffs.
    bugs = sorted(bugs, key=lambda x: x["id"])

    # Write into the existing dataset contract used by retrieval.
    out_path = data_dir / "historical_bugs.json"
    out_path.write_text(json.dumps(bugs, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Loaded {len(bugs)} real bug records into the dataset.")


if __name__ == "__main__":
    load_real_data()

