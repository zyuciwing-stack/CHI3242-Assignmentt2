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


def check(name, ok, detail="", category="program"):
    checks.append({"check": name, "ok": bool(ok), "detail": detail, "category": category})
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

    check("HTML exists", HTML.exists(), str(HTML), category="browser")
    html = HTML.read_text(encoding="utf-8") if HTML.exists() else ""
    if HTML.exists():
        check("HTML has no external script src", not re.search(r"<script[^>]+src=", html),
              "no <script src=...>", category="browser")
        external = re.findall(
            r"<(?:script|link)[^>]+(?:src|href)=[\"'](https?://[^\"']+)", html, re.I)
        check("HTML has no external script/link resources", not external,
              str(external[:3]), category="browser")
        check("2D/3D share the same coordinate source",
              "const ref2 = makeReferenceTrace(false);" in html and
              "const ref3 = makeReferenceTrace(true);" in html and
              "DATA.pca[String(n)].coords[w.work_id]" in html,
              "both views read DATA.pca[String(n)].coords; no second fit",
              category="browser")
        check("HTML placeholders replaced",
              "__PLOTLY_JS__" not in html and "__DATA_JSON__" not in html,
              "placeholders absent", category="browser")
        check("HTML contains Plotly and data",
              "Plotly" in html and "W06-015" in html and "1,654" in html,
              f"size={len(html):,} chars", category="browser")
        check("HTML contains 超奇 projection", "E01" in html and "超奇" in html,
              "E01/超奇 present", category="browser")

    # Verify the complete signed contribution table against independently saved vectors/counts.
    import math
    for n in (100, 50):
        sh = pd.read_csv(DATA / f"chaoyi_shared_features_{n}.csv", encoding="utf-8-sig")
        raw = pd.read_csv(DATA / f"feature_counts_{n}.csv", encoding="utf-8-sig", index_col=0)
        zz = pd.read_csv(DATA / f"feature_zscores_{n}.csv", encoding="utf-8-sig", index_col=0)
        cz = pd.read_csv(DATA / f"chaoyi_zscores_{n}.csv", encoding="utf-8-sig").set_index("feature")["z_chaoyi"]
        nb = pd.read_csv(DATA / f"chaoyi_neighbors_{n}.csv", encoding="utf-8-sig").set_index("target_work_id")
        norm_a = math.sqrt(sum(float(x)**2 for x in cz))
        sums_ok = True; raw_ok = True; components_ok = True; zprod_ok = True
        for wid,g in sh.groupby("neighbor_work_id"):
            sums_ok &= len(g) == n and g["feature"].nunique() == n and abs(g["cosine_contribution"].sum()-nb.loc[wid,"similarity"]) < 1e-12
            norm_b = math.sqrt(sum(float(x)**2 for x in zz.loc[wid]))
            for _,r in g.iterrows():
                f = r["feature"]
                raw_ok &= int(r["count_neighbor"]) == int(raw.loc[wid,f])
                zprod = float(cz[f])*float(zz.loc[wid,f])
                zprod_ok &= abs(float(r["z_product"]) - zprod) < 1e-12
                components_ok &= abs(float(r["cosine_contribution"])-zprod/(norm_a*norm_b)) < 1e-12
        check(f"{n} complete signed contribution sums", sums_ok, "each top-10 neighbor has all N features; sum equals cosine")
        check(f"{n} contributions independently recomputed", components_ok, "saved z vectors and scalar cosine formula")
        check(f"{n} z_product independently recomputed", zprod_ok, "z_product = z_chaoyi * z_neighbor")
        check(f"{n} neighbor raw counts", raw_ok, "compared with raw count matrix")
        expected_present=(sh["count_chaoyi"]>0)&(sh["count_neighbor"]>0)
        check(f"{n} both-present filter", (expected_present==sh["both_present"]).all(), "zero-count words never labelled both-present")
        expected_cat=np.where((sh.z_chaoyi>0)&(sh.z_neighbor>0),"both_above_mean",np.where((sh.z_chaoyi<0)&(sh.z_neighbor<0),"both_below_mean","other"))
        check(f"{n} contribution categories", (expected_cat==sh.category).all(), "both above, both below, or opposite/zero")
        cc = json.loads((DATA / f"chaoyi_contribution_checks_{n}.json").read_text(encoding="utf-8"))
        check(f"{n} saved contribution-check JSON",
              all(c["n_features"] == n and abs(c["contribution_sum"] - c["similarity"]) < 1e-12
                  and c["both_above_count"] + c["both_below_count"] + c["other_count"] == n
                  for c in cc),
              f"{len(cc)} neighbors; all-feature sum equals cosine")
        if n == 100:
            e02 = next(c for c in cc if c["neighbor_work_id"] == "E02")
            check("E02 contribution-check counts",
                  e02["both_present_count"] == 55 and e02["both_above_count"] == 23
                  and e02["both_below_count"] == 52 and e02["other_count"] == 25,
                  "55 both-present; 23 both-high; 52 both-low; 25 other")
    a=pd.read_csv(DATA/"chaoyi_neighbors_100.csv",encoding="utf-8-sig")
    b=pd.read_csv(DATA/"chaoyi_neighbors_50.csv",encoding="utf-8-sig")
    check("超奇 top-5 overlap",len(set(a.head(5).target_work_id)&set(b.head(5).target_work_id))==3,"3/5")
    check("超奇 top-10 overlap",len(set(a.head(10).target_work_id)&set(b.head(10).target_work_id))==8,"8/10")
    check("超奇 nearest E02 in both settings",a.iloc[0].target_work_id==b.iloc[0].target_work_id=="E02","論衡·佚文")
    check("超奇 E05 and E03 in both top-10",
          "E05" in set(a.head(10).target_work_id) & set(b.head(10).target_work_id)
          and "E03" in set(a.head(10).target_work_id) & set(b.head(10).target_work_id),
          "E05/E03 present in both top-10 lists")
    overlap_data = json.loads((DATA / "chaoyi_neighbor_overlap.json").read_text(encoding="utf-8"))
    check("超奇 overlap JSON computed from neighbours",
          overlap_data["top5_overlap_count"] == 3 and overlap_data["top10_overlap_count"] == 8
          and overlap_data["e02_rank_100"] == 1 and overlap_data["e02_rank_50"] == 1
          and overlap_data["e05_top10_100"] and overlap_data["e05_top10_50"]
          and overlap_data["e03_top10_100"] and overlap_data["e03_top10_50"]
          and set(overlap_data["top10_only_100"]) == {"E33", "W03"}
          and set(overlap_data["top10_only_50"]) == {"E11", "W11"},
          json.dumps(overlap_data, ensure_ascii=False))
    stability = pd.read_csv(DATA / "neighbor_stability.csv", encoding="utf-8-sig")
    check("31/52 works have >=3/5 stable neighbours",
          len(stability) == 52 and int((stability["stable_count"] >= 3).sum()) == 31,
          f"{int((stability['stable_count'] >= 3).sum())}/52")
    check("reuse author and period composition",
          int((approx.author_a==approx.author_b).sum())==29
          and int((approx.period_a==approx.period_b).sum())==29
          and int((approx.period_a!=approx.period_b).sum())==1,
          "30 pairs: 29 same-author, 29 same-period, one cross-period")
    baseline_path=ROOT/"output/final_integration/baseline.json"
    baseline=json.loads(baseline_path.read_text(encoding="utf-8"))
    expected=dict(baseline["protected"])
    revision_path=ROOT/"output/final_integration/source_revision.json"
    if revision_path.exists():
        revision=json.loads(revision_path.read_text(encoding="utf-8"))
        assert revision["previous_catalogue_sha256"]==expected["corpus_catalogue.csv"]
        expected["corpus_catalogue.csv"]=revision["new_catalogue_sha256"]
    mismatches=[name for name,digest in expected.items() if sha256(ROOT/name)!=digest]
    check("protected data/models and authorized catalogue citation revision",not mismatches,str(mismatches))
    check("HTML contribution controls and all-feature table",
          all(x in html for x in ['id="bothPresentOnly"', 'id="chaoyiNeighborSelect"',
                                  'id="chaoyiCategoryFilter"', 'id="chaoyiSort"',
                                  'z_product', 'cosine_contribution']),
          "neighbor selector, category/sort filters, z_product and contribution",
          category="browser")
    check("HTML all-feature summary not top-8 only",
          "表列 " in html and "all.length" in html and "rows.length" in html
          and "前八項" not in html,
          "summary uses all features; filtered rows are not the sum",
          category="browser")
    check("HTML corrected sign-flip caveat",
          "不能由座標變號認定不穩定" in html and '"co_loading"' not in html,
          "no co_loading; no claim that sign flip proves instability",
          category="interpretation")
    findings_path = OUT / "research_findings.md"
    findings = findings_path.read_text(encoding="utf-8") if findings_path.exists() else ""
    check("findings avoids '壓過' causal claim", "壓過" not in findings,
          "author/genre labels describe visible structure; no causal 'override' claim",
          category="interpretation")
    check("findings avoids '前30名' wording", "前30名" not in findings,
          "reuse described as all 30 qualifying pairs, not a top-30 ranking",
          category="interpretation")
    check("findings avoids stale top-8/1,000-column wording",
          "前八項" not in findings and "1000列" not in findings,
          "table/findings describe all features, not a top-8 list",
          category="interpretation")
    check("findings W09 retained-material caveat",
          "本次保留材料" in findings and "原篇全文" in findings,
          "14 words are this excerpt, not the full original",
          category="interpretation")
    check("findings 200-word threshold caveat",
          "200詞只是顯示提醒" in findings and "可靠性界線" in findings,
          "200 words is a reminder threshold, not a validated boundary",
          category="interpretation")
    check("findings exact-match caveat",
          "正規化完全相同且最少8漢字" in findings and "0對" in findings,
          "0 exact pairs under dedupe + minimum 8 CJK characters",
          category="interpretation")
    check("findings W06/E11 only cross-period pair",
          "30對中29對同作者、29對同期，唯一跨期者為W06-015／E11-018" in findings,
          "all 30 approximate candidates; one cross-period",
          category="interpretation")
    check("findings E05/E03 in both top-10",
          "E05、E03也在兩套前十" in findings,
          "E05/E03 in both 100- and 50-feature top-10",
          category="interpretation")
    check("findings E02 contribution check",
          "0.5584869926694443" in findings and "55個在兩篇都實際出現" in findings,
          "all-feature sum and both-present count reported",
          category="interpretation")

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
    (OUT / "protected_hashes.json").write_text(
        json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")

    category_labels = {
        "program": "程式檢查",
        "browser": "瀏覽器檢查",
        "interpretation": "研究解釋檢查",
    }
    by_category = {}
    for cat in category_labels:
        subset = [c for c in checks if c["category"] == cat]
        by_category[cat] = {
            "passed": sum(1 for c in subset if c["ok"]),
            "failed": sum(1 for c in subset if not c["ok"]),
            "total": len(subset),
        }
    payload = {
        "checks": checks,
        "passed": sum(1 for c in checks if c["ok"]),
        "failed": sum(1 for c in checks if not c["ok"]),
        "by_category": by_category,
        "protected_hashes": hashes,
        "notes": [
            "Only one 3-component PCA was fitted per feature setting; the 2D view is the PC1/PC2 subset of the same coordinates.",
            "The HTML uses the same DATA.pca coordinates for the 2D and 3D plots; toggling visibility does not refit.",
            "Exact cross-work duplicates are 0 because the build_corpus_v3 dedupe kept only the first occurrence; duplicates are logged in data/v3/excluded.csv.",
            "相似度矩陣在原始 z-score 特徵上計算，不是 PCA 二維距離。",
            "Browser checks here are static/offline HTML checks; mouse rotation/zoom was not simulated. See browser_check.md.",
            "Research interpretation checks verify wording against computed data; they do not establish causal claims.",
        ],
    }
    (OUT / "verification.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Exploration verification", "",
             f"Total: {payload['passed']} / {len(checks)} passed", ""]
    for cat, label in category_labels.items():
        subset = [c for c in checks if c["category"] == cat]
        stat = by_category[cat]
        lines += [f"## {label}", "",
                  f"Passed: {stat['passed']} / {stat['total']}", ""]
        for c in subset:
            lines.append(f"- [{'x' if c['ok'] else ' '}] {c['check']} — {c['detail']}")
        lines.append("")
    lines += ["## Notes", ""]
    lines += [f"- {n}" for n in payload["notes"]]
    lines += ["", "Protected file hashes are in `protected_hashes.json`; the exploration scripts only read these files.", ""]
    (OUT / "verification.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT / "verification.json", OUT / "verification.md")
    if payload["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
