#!/usr/bin/env python3
"""Validate that generated PDFs are readable and contain the full case corpus."""
from __future__ import annotations

import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "data/cases.json").read_text(encoding="utf-8"))

for filename in ("low-cost-life-guide.pdf", "low-cost-life-guide-a5.pdf"):
    path = ROOT / "downloads" / filename
    if not path.exists() or path.stat().st_size < 20_000:
        raise SystemExit(f"ERROR: missing or too-small PDF: {path}")
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if len(reader.pages) < 5:
        raise SystemExit(f"ERROR: {filename} has too few pages")
    if "低性价比" not in text or "证据与来源" not in text:
        raise SystemExit(f"ERROR: {filename} missing title or evidence sections")
    missing = [case["id"] for case in CASES if case["id"] not in text]
    if missing:
        raise SystemExit(f"ERROR: {filename} missing case ids: {', '.join(missing)}")
    print(f"Validated {filename}: {len(reader.pages)} pages, {path.stat().st_size} bytes")