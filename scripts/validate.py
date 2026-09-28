#!/usr/bin/env python3
"""Validate the static case dataset without third-party dependencies."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cases.json"
REQUIRED = {
    "id", "slug", "title", "summary", "category", "category_key", "risk_type",
    "tags", "severity", "likelihood", "reversibility", "horizon", "evidence_grade",
    "confidence", "warning", "wrong_advice", "scenario", "why_attractive",
    "hidden_costs", "failure_mechanism", "score", "evidence", "stop_loss",
    "safer_alternative", "decision_checklist", "related_cases", "chapter", "updated_at",
}
VALID_GRADES = {"A", "B", "C"}
VALID_SEVERITY = {"low", "medium", "high", "critical"}
VALID_RISKS = {"money", "time", "opportunity", "privacy", "health", "legal", "reputation"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if not DATA.exists():
        fail(f"missing {DATA}")
    try:
        cases = json.loads(DATA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {exc}")
    if not isinstance(cases, list) or not cases:
        fail("cases.json must contain a non-empty array")

    ids: set[str] = set()
    slugs: set[str] = set()
    for index, case in enumerate(cases, start=1):
        prefix = f"case #{index}"
        if not isinstance(case, dict):
            fail(f"{prefix} must be an object")
        missing = REQUIRED - case.keys()
        if missing:
            fail(f"{prefix} missing fields: {', '.join(sorted(missing))}")
        if case["id"] in ids:
            fail(f"duplicate id: {case['id']}")
        if case["slug"] in slugs:
            fail(f"duplicate slug: {case['slug']}")
        ids.add(case["id"])
        slugs.add(case["slug"])
        if case["evidence_grade"] not in VALID_GRADES:
            fail(f"{case['slug']}: invalid evidence_grade")
        if case["severity"] not in VALID_SEVERITY:
            fail(f"{case['slug']}: invalid severity")
        if not set(case["risk_type"]).issubset(VALID_RISKS):
            fail(f"{case['slug']}: unknown risk_type")
        score = case["score"]
        for field in ("apparent_gain", "cost"):
            if not isinstance(score.get(field), int) or not 0 <= score[field] <= 5:
                fail(f"{case['slug']}: {field} must be an integer 0..5")
        if not isinstance(score.get("irreversibility_penalty"), int) or not 0 <= score["irreversibility_penalty"] <= 3:
            fail(f"{case['slug']}: irreversibility_penalty must be an integer 0..3")
        if not isinstance(score.get("low_value_index"), int) or not 0 <= score["low_value_index"] <= 100:
            fail(f"{case['slug']}: low_value_index must be an integer 0..100")
        if not case["evidence"]:
            fail(f"{case['slug']}: at least one evidence item is required")
        for source in case["evidence"]:
            if source.get("grade") not in VALID_GRADES:
                fail(f"{case['slug']}: invalid source grade")
            url = source.get("url", "")
            if source["grade"] in {"A", "B"}:
                parsed = urlparse(url)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    fail(f"{case['slug']}: A/B source needs an http(s) URL")
        for related in case["related_cases"]:
            if related not in slugs:
                # Cross references can point forward; check after the loop below.
                continue

    for case in cases:
        for related in case["related_cases"]:
            if related not in slugs:
                fail(f"{case['slug']}: unknown related case {related}")

    print(f"Validated {len(cases)} cases, {len(set(c['category_key'] for c in cases))} categories.")
    print("Schema, score ranges, evidence URLs and cross-references are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())