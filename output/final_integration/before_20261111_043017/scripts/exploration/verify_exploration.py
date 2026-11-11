# -*- coding: utf-8 -*-
"""Verify the exploration data, PCA/similarity invariants, and offline HTML."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "output" / "exploration" / "data"
OUT = ROOT / "output" / "exploration"
HTML = OUT / "index.html"

checks = []


def check(name, ok, detail=""):
    checks.append({"check": name, "ok": bool(ok), "detail": detail})
    print(("PASS" if ok else "FAIL"), name, detail)


def sha256(path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main():
    catalogue = pd.read_csv(ROOT / "corpus_catalogue.csv", encoding="utf-8-sig")
    ref = catalogue[catalogue["用途"] == "主樣本"]
    works = pd.read_csv(DATA / "works.csv", encoding="utf-8-sig")
    sentences = pd.read_csv(DATA / "sentences.csv", encoding="utf-8-sig")
    check("52 reference works", len(ref) == 52 and len(works) == 52,
          f"catalogue={len(ref)}, works.csv={len(works)}")
    check("1654 sentences", len(sentences) == 1654, f"rows={len(sentences)}")
    periods = sentences["period"].value_counts().to_dict()
    check("period sentence counts 702/952",
          periods.get("西漢") == 702 and periods.get("東漢") == 952,
          str(periods))

    per_work = sentences.groupby("work_id").size().to_dict()
    mismatches = []
    for _, row in ref.iterrows():
        wid = row["編號"]
        if int(per_work.get(wid, 0)) != int(row["可建模全庫句"]):
            mismatches.append((wid, int(row["可建模全庫句"]), int(per_work.get(wid, 0))))
    check("per-work sentence counts match catalogue", not mismatches, str(mismatches))

    for n in [100, 50]:
        features = pd.read_csv(DATA / f"features_{n}.csv", encoding="utf-8-sig")
        counts = pd.read_csv(DATA / f"feature_counts_{n}.csv", encoding="utf-8-sig", index_col=0)
        zscores = pd.read_csv(DATA / f"feature_zscores_{n}.csv", encoding="utf-8-sig", index_col=0)
        coords = pd.read_csv(DATA / f"pca_coordinates_{n}.csv", encoding="utf-8-sig")
        ev = json.loads((DATA / f"explained_variance_{n}.json").read_text(encoding="utf-8"))
        check(f"{n} features available", len(features) == n,
              f"features={len(features)}")
        check(f"{n} feature matrix shape", counts.shape == (52, n),
              f"{counts.shape}")
        check(f"{n} feature matrix has no label columns",
              not any(c in counts.columns for c in ("period", "author", "genre", "genre_group")),
              "no period/author/genre columns")
        check(f"{n} z-score matrix has no NaN", not zscores.isna().any().any(),
              f"NaN={int(zscores.isna().sum().sum())}")
        check(f"{n} PCA coordinates shape",
              len(coords) == 52 and {"work_id", "PC1", "PC2", "PC3"}.issubset(coords.columns),
              f"{coords.shape}, columns={list(coords.columns)}")
        check(f"{n} PCA has three components", ev["n_components"] == 3,
              f"n_components={ev['n_components']}")
        check(f"{n} explained variance finite",
              all(np.isfinite(ev["explained_variance_ratio"])),
              str(ev["explained_variance_ratio"]))

        sim = pd.read_csv(DATA / f"similarity_{n}.csv", encoding="utf-8-sig", index_col=0)
        matrix = sim.values
        check(f"{n} similarity shape", matrix.shape == (52, 52), f"{matrix.shape}")
        check(f"{n} similarity symmetric", np.allclose(matrix, matrix.T, atol=1e-12),
              f"max asym={np.max(np.abs(matrix-matrix.T)):.2e}")
        check(f"{n} similarity diagonal 1", np.allclose(np.diag(matrix), 1.0, atol=1e-12),
              f"diag range={np.diag(matrix).min():.6f}-{np.diag(matrix).max():.6f}")
        check(f"{n} similarity no missing", not np.isnan(matrix).any(),
              f"NaN={int(np.isnan(matrix).sum())}")

        fs = json.loads((DATA / f"feature_selection_{n}.json").read_text(encoding="utf-8"))
        check(f"{n} fit has 52 documents", fs["n_fit_documents"] == 52,
              f"n_fit={fs['n_fit_documents']}")
        check(f"{n} 超奇 excluded from fit", "E01" not in fs["document_ids"],
              "E01 not in document_ids")

        ch = json.loads((DATA / f"chaoyi_projection_{n}.json").read_text(encoding="utf-8"))
        check(f"{n} 超奇 projection-only",
              ch["excluded_from_fit"] and ch["fit_work_count"] == 52,
              f"fit_work_count={ch['fit_work_count']}, overlap={ch['feature_overlap_ratio']:.3f}")
        check(f"{n} 超奇 not in works.csv", "E01" not in set(works["work_id"]),
              "E01 absent from 52-work table")

    exact = pd.read_csv(DATA / "reuse_exact.csv", encoding="utf-8-sig")
    approx = pd.read_csv(DATA / "reuse_approx.csv", encoding="utf-8-sig")
    special = json.loads((DATA / "reuse_special_check.json").read_text(encoding="utf-8"))
    check("exact cross-work matches", len(exact) == 0,
          f"rows={len(exact)} (deduped corpus; duplicates logged in data/v3/excluded.csv)")
    check("approximate candidates present", len(approx) == 30, f"rows={len(approx)}")
    check("W06/E11 special check detected", special["detected_by_approx"],
          f"containment={special['containment']:.3f}, shared={special['shared_ngrams']}, LCS={special['lcs_len']}")
    check("special check exact equality is false", not special["exact_normalized_equal"],
          "exact_normalized_equal=false; approximate method is the one that catches it")

    check("HTML exists", HTML.exists(), str(HTML))
    if HTML.exists():
        html = HTML.read_text(encoding="utf-8")
        check("HTML has no external script src", not re.search(r"<script[^>]+src=", html),
              "no <script src=...>")
        external = re.findall(
            r"<(?:script|link)[^>]+(?:src|href)=[\"'](https?://[^\"']+)", html, re.I)
        check("HTML has no external script/link resources", not external,
              str(external[:3]))
        check("2D/3D share the same coordinate source",
              "const ref2 = makeReferenceTrace(false);" in html and
              "const ref3 = makeReferenceTrace(true);" in html and
              "DATA.pca[String(n)].coords[w.work_id]" in html,
              "both views read DATA.pca[String(n)].coords; no second fit")
        check("HTML placeholders replaced",
              "__PLOTLY_JS__" not in html and "__DATA_JSON__" not in html,
              "placeholders absent")
        check("HTML contains Plotly and data",
              "Plotly" in html and "W06-015" in html and "1,654" in html,
              f"size={len(html):,} chars")
        check("HTML contains 超奇 projection", "E01" in html and "超奇" in html,
              "E01/超奇 present")

    # Hashes of files that the exploration must not modify.
    protected = [
        ROOT / "corpus_catalogue.csv",
        ROOT / "data" / "v3" / "dataset_v3.csv",
        ROOT / "data" / "v3" / "sentences_all.csv",
        ROOT / "data" / "v3" / "sources.csv",
        ROOT / "output" / "v3" / "metrics.json",
        ROOT / "output" / "v3" / "test_predictions.csv",
        ROOT / "output" / "v3" / "independent_predictions.csv",
    ]
    hashes = {str(p.relative_to(ROOT)): sha256(p) for p in protected if p.exists()}
    report_html = ROOT / "report.html"
    if report_html.exists():
        hashes["report.html"] = sha256(report_html)
    (OUT / "protected_hashes.json").write_text(
        json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = {
        "checks": checks,
        "passed": sum(1 for c in checks if c["ok"]),
        "failed": sum(1 for c in checks if not c["ok"]),
        "protected_hashes": hashes,
        "notes": [
            "Only one 3-component PCA was fitted per feature setting; the 2D view is the PC1/PC2 subset of the same coordinates.",
            "The HTML uses the same DATA.pca coordinates for the 2D and 3D plots; toggling visibility does not refit.",
            "Exact cross-work duplicates are 0 because the build_corpus_v3 dedupe kept only the first occurrence; duplicates are logged in data/v3/excluded.csv.",
            "相似度矩陣在原始 z-score 特徵上計算，不是 PCA 二維距離。",
        ],
    }
    (OUT / "verification.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Exploration verification", "",
             f"Passed: {payload['passed']} / {len(checks)}", ""]
    for c in checks:
        lines.append(f"- [{'x' if c['ok'] else ' '}] {c['check']} — {c['detail']}")
    lines += ["", "Protected file hashes are in `protected_hashes.json`; the exploration scripts only read these files.", ""]
    (OUT / "verification.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT / "verification.json", OUT / "verification.md")


if __name__ == "__main__":
    main()
