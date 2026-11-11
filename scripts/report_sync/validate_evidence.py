# -*- coding: utf-8 -*-
"""Recompute the report anchors from the saved CSV/JSON evidence.

Read-only.  Does not train, tokenise, or modify data/model/report files.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "report.md"
APPENDIX_MD = ROOT / "output" / "report_support" / "corpus_appendix.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def md_table_rows(path: Path):
    """Return (group_heading, rows) for each Markdown table in a file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    heading = None
    rows = []
    for line in lines:
        s = line.strip()
        if s.startswith("###"):
            heading = s.lstrip("#").strip()
        if s.startswith("|"):
            if re.match(r"^\|[-:|]+\|$", s):
                continue
            rows.append([c.strip() for c in s.strip("|").split("|")])
        elif rows:
            out.append((heading, rows))
            rows = []
    if rows:
        out.append((heading, rows))
    return out


def main() -> dict:
    sources = pd.read_csv(ROOT / "data" / "v3" / "sources.csv", encoding="utf-8-sig")
    sentences = pd.read_csv(ROOT / "data" / "v3" / "sentences_all.csv", encoding="utf-8-sig")
    dataset = pd.read_csv(ROOT / "data" / "v3" / "dataset_v3.csv", encoding="utf-8-sig")
    catalogue = pd.read_csv(ROOT / "corpus_catalogue.csv", encoding="utf-8-sig")
    test = pd.read_csv(ROOT / "output" / "v3" / "test_predictions.csv", encoding="utf-8-sig")
    independent = pd.read_csv(ROOT / "output" / "v3" / "independent_predictions.csv", encoding="utf-8-sig")
    metrics = json.loads((ROOT / "output" / "v3" / "metrics.json").read_text(encoding="utf-8"))
    grouped = json.loads((ROOT / "output" / "v3" / "grouped" / "run_metadata.json").read_text(encoding="utf-8"))
    genre_full = json.loads((ROOT / "output" / "v3" / "genre_experiment" / "metrics_full_class.json").read_text(encoding="utf-8"))
    genre_zip = json.loads((ROOT / "output" / "v3" / "genre_experiment" / "metrics_only.json").read_text(encoding="utf-8")) if (ROOT / "output" / "v3" / "genre_experiment" / "metrics_only.json").exists() else json.loads((ROOT / "output" / "v3" / "genre_experiment" / "metrics_zip_only.json").read_text(encoding="utf-8"))
    author = pd.read_csv(ROOT / "output" / "v3" / "author_pairings" / "summary.csv", encoding="utf-8-sig")
    p1_full = json.loads((ROOT / "output" / "v3" / "author_pairings" / "P1_liuan_wangchong" / "metrics_full_class.json").read_text(encoding="utf-8"))
    p1_zip = json.loads((ROOT / "output" / "v3" / "author_pairings" / "P1_liuan_wangchong" / "metrics_zip_only.json").read_text(encoding="utf-8"))
    uncertain = pd.read_csv(ROOT / "output" / "uncertain_probe" / "summary.csv", encoding="utf-8-sig")
    overlap = json.loads((ROOT / "output" / "exploration" / "data" / "chaoyi_neighbor_overlap.json").read_text(encoding="utf-8"))
    checks = json.loads((ROOT / "output" / "exploration" / "data" / "chaoyi_contribution_checks_100.json").read_text(encoding="utf-8"))
    explained = json.loads((ROOT / "output" / "exploration" / "data" / "explained_variance_100.json").read_text(encoding="utf-8"))

    full = sentences[sentences["trainable"] == True]
    trainable_ids = set(full["work_id"])
    full_by_period = full["period"].value_counts().to_dict()
    main_by_period = dataset["period"].value_counts().to_dict()
    split_period = pd.crosstab(dataset["split"], dataset["period"]).to_dict()
    conf = [[int(((test.period_true == a) & (test.period_pred == b)).sum()) for b in ["西漢", "東漢"]] for a in ["西漢", "東漢"]]
    grouped_conf = grouped["metrics"]["confusion_matrix"]
    probes = uncertain[uncertain["scope"] == "沿用原清理條件的句"].copy()
    probe_counts = [
        {
            "work_id": r.work_id,
            "title": r.title,
            "n": int(r.n),
            "west": int(r.west),
            "east": int(r.east),
            "zero_feature_sentences": int(r.zero_feature_sentences),
        }
        for r in probes.itertuples()
    ]
    # Appendix tables are grouped; count rows and sum the numeric columns.
    appendix_tables = md_table_rows(APPENDIX_MD)
    appendix_rows = []
    group_counts = {}
    for heading, rows in appendix_tables:
        if not rows or rows[0][0] != "編號":
            continue
        group_counts[heading] = len(rows) - 1
        appendix_rows.extend(rows[1:])
    appendix_ids = [r[0] for r in appendix_rows]
    appendix_sums = {
        "candidate": sum(int(r[3].split("／")[0]) for r in appendix_rows),
        "full": sum(int(r[3].split("／")[1]) for r in appendix_rows),
        "main": sum(int(r[4].split("／")[0]) for r in appendix_rows),
        "train": sum(int(r[4].split("／")[1]) for r in appendix_rows),
        "test": sum(int(r[4].split("／")[2]) for r in appendix_rows),
    }
    catalogue_usage = catalogue.set_index("編號")["用途"].to_dict()
    appendix_usage_diff = {
        r[0]: {"appendix": r[5], "catalogue": catalogue_usage.get(r[0])}
        for r in appendix_rows
        if r[5] != catalogue_usage.get(r[0])
    }
    # Compare appendix counts to catalogue counts.
    count_diff = {}
    for r in appendix_rows:
        c = catalogue[catalogue["編號"] == r[0]]
        if c.empty:
            count_diff[r[0]] = "missing from catalogue"
            continue
        c = c.iloc[0]
        cand, full_n, main_n, train_n, test_n = [int(x) for x in r[3].split("／")] + [int(x) for x in r[4].split("／")]
        expected = [int(c["候選句"]), int(c["可建模全庫句"]), int(c["主樣本句"]), int(c["訓練句"]), int(c["測試句"])]
        actual = [cand, full_n, main_n, train_n, test_n]
        if actual != expected:
            count_diff[r[0]] = {"appendix": actual, "catalogue": expected}

    e02 = next(c for c in checks if c["neighbor_work_id"] == "E02")
    body = REPORT_MD.read_text(encoding="utf-8")
    body_without_back = body.split("## 參考書目", 1)[0]
    visible = re.sub(r"^\|[-:|]+\|$", "", body_without_back, flags=re.M)
    visible = re.sub(r"[#*|\s\u3000]", "", visible)
    body_counts = {
        "visible_nonspace": len(visible),
        "han_characters": len(re.findall(r"[\u3400-\u9fff]", visible)),
    }

    result = {
        "report_md_sha256": sha(REPORT_MD),
        "report_pdf_sha256": sha(ROOT / "report.pdf"),
        "report_md_mtime": REPORT_MD.stat().st_mtime,
        "report_pdf_mtime": (ROOT / "report.pdf").stat().st_mtime,
        "report_md_body_counts": body_counts,
        "main": {
            "sentences": int(len(dataset)),
            "split": dataset["split"].value_counts().to_dict(),
            "period": main_by_period,
            "split_period": split_period,
            "works": int(dataset["work_id"].nunique()),
            "authors": int(dataset["author"].nunique()),
            "test_works": int(test["work_id"].nunique()),
            "test_authors": int(test["author"].nunique()),
        },
        "corpus": {
            "works": int(len(trainable_ids)),
            "authors": int(full["author"].nunique()),
            "sentences": int(len(full)),
            "sentences_all": int(len(sentences)),
            "period": full_by_period,
            "works_by_period": full.groupby("period")["work_id"].nunique().to_dict(),
            "authors_by_period": full.groupby("period")["author"].nunique().to_dict(),
        },
        "model": {
            "accuracy": metrics["accuracy"],
            "majority_baseline": metrics["majority_baseline"],
            "macro_f1": metrics["macro_f1"],
            "confusion": conf,
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
        },
        "grouped": {
            "n_test": grouped["n_test"],
            "correct": int(grouped_conf[0][0] + grouped_conf[1][1]),
            "confusion": grouped_conf,
        },
        "genre": {
            "n_test": genre_full["n_test"],
            "full_correct": int(genre_full["confusion_matrix"][0][0] + genre_full["confusion_matrix"][1][1]),
            "zip_correct": int(genre_zip["confusion_matrix"][0][0] + genre_zip["confusion_matrix"][1][1]),
            "full_confusion": genre_full["confusion_matrix"],
            "zip_confusion": genre_zip["confusion_matrix"],
        },
        "author_pair": {
            "P1": {
                **author[author["pair"] == "P1_liuan_wangchong"].iloc[0][
                    ["test_sentences", "test_east", "full_acc", "zip_acc"]
                ].to_dict(),
                "full_east_hits": int(p1_full["confusion_matrix"][1][1]),
                "zip_east_hits": int(p1_zip["confusion_matrix"][1][1]),
            }
        },
        "uncertain": {
            "probes": probe_counts,
            "total_clean": int(sum(p["n"] for p in probe_counts)),
            "zero_features": int(sum(p["zero_feature_sentences"] for p in probe_counts)),
        },
        "exploration": {
            "chaoyi_n": int(len(independent)),
            "chaoyi_east": int((independent["period_pred"] == "東漢").sum()),
            "pca_cum3_100": explained["cumulative_explained"][-1],
            "overlap5": overlap["top5_overlap_count"],
            "overlap10": overlap["top10_overlap_count"],
            "e02_similarity": e02["similarity"],
            "e02_contribution_sum": e02["contribution_sum"],
            "e02_both_present": e02["both_present_count"],
        },
        "appendix": {
            "rows": len(appendix_rows),
            "unique_ids": len(set(appendix_ids)),
            "groups": group_counts,
            "sums": appendix_sums,
            "usage_diff": appendix_usage_diff,
            "count_diff": count_diff,
        },
        "catalogue": {
            "rows": int(len(catalogue)),
            "usage": catalogue["用途"].value_counts().to_dict(),
        },
        "pdf_status": {
            "pdf_mtime_older_than_md": (ROOT / "report.pdf").stat().st_mtime < REPORT_MD.stat().st_mtime,
            "support_record_says_pdf_unchanged": True,
        },
    }
    return result


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
