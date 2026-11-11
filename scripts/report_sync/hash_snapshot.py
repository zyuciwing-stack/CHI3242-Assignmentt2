# -*- coding: utf-8 -*-
"""Write SHA-256 hashes for the files that the sync must not alter."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> dict:
    files = [
        ROOT / "report.md",
        ROOT / "report.pdf",
        ROOT / "report.docx",
        ROOT / "report.html",
        ROOT / "corpus_catalogue.csv",
        ROOT / "corpus_catalogue.md",
        ROOT / "output" / "report_support" / "corpus_appendix.md",
        ROOT / "output" / "report_support" / "prose_revision_record.md",
        ROOT / "output" / "report_support" / "prose_revision_verification.json",
    ]
    for directory in [
        ROOT / "data" / "v3",
        ROOT / "output" / "v3",
        ROOT / "output" / "exploration",
        ROOT / "output" / "uncertain_probe",
    ]:
        if directory.exists():
            files.extend(sorted(p for p in directory.rglob("*") if p.is_file()))
    result = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in files if p.exists()}
    out = ROOT / "output" / "report_sync" / "pre_sync_hashes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out, len(result))
    return result


if __name__ == "__main__":
    main()
