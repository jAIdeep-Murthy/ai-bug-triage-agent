from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def verify_data() -> None:
    data_dir = _repo_root() / "data"
    path = data_dir / "historical_bugs.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise RuntimeError("historical_bugs.json is not a JSON list.")

    print(f"Total HistoricalBug records: {len(records)}")

    severities = Counter((r.get("severity") or "unknown") for r in records if isinstance(r, dict))
    print("Severity distribution:")
    for sev, cnt in severities.most_common():
        print(f"  {sev}: {cnt}")

    categories = Counter((r.get("category") or "unknown") for r in records if isinstance(r, dict))
    print("Top 10 categories:")
    for cat, cnt in categories.most_common(10):
        print(f"  {cat}: {cnt}")

    print("Sample records:")
    for r in records[:3]:
        if not isinstance(r, dict):
            continue
        print(
            f"  {r.get('id')} | {str(r.get('title', ''))[:80]} | {r.get('severity')} | {r.get('category')}"
        )

    if len(records) >= 100:
        print("Retrieval layer is ready.")
    else:
        print("WARNING: Fewer than 100 records loaded; retrieval quality may be poor.")


if __name__ == "__main__":
    verify_data()

