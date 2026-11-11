# -*- coding: utf-8 -*-
"""Verify the fixed-split tokenizer comparison and protection of prior outputs."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "tokenizer_comparison"
DATA = ROOT / "data" / "v3"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    checks = []
    limitations = [
        "Jiayan's recommended CharHMMTokenizer requires KenLM/jiayan.klm; KenLM could not be built in this Windows environment. The comparison uses the official WordNgramTokenizer.",
        "Jiayan input is OpenCC t2s; Jieba keeps the original traditional text. Jieba-on-OpenCC is reported as an exploratory control, not as the main baseline.",
        "Jieba keeps 35 project-specific user words; Jiayan uses its bundled dictionary without a post-hoc custom lexicon.",
        "One fixed split and one corpus version; sentences within works are not independent.",
        "Chaoyi is an already-analysed same-author holdout, not a new cross-author blind test.",
        "The AI-assisted segmentation review is not a human token-level gold standard.",
    ]

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    dataset = pd.read_csv(DATA / "dataset_v3.csv", encoding="utf-8-sig")
    train = dataset[dataset["split"] == "train"]
    test = dataset[dataset["split"] == "test"]
    train_ids = train["sent_id"].tolist()
    test_ids = test["sent_id"].tolist()
    check("main sample 1163", len(dataset) == 1163, str(len(dataset)))
    check("fixed split 930/233", len(train) == 930 and len(test) == 233, f"{len(train)}/{len(test)}")
    check("split period counts", train["period"].value_counts().to_dict() == {"西漢": 505, "東漢": 425} and test["period"].value_counts().to_dict() == {"西漢": 127, "東漢": 106}, f"{train['period'].value_counts().to_dict()} / {test['period'].value_counts().to_dict()}")
    check("train/test IDs disjoint", not set(train_ids) & set(test_ids), "no overlap")

    for name in ("jieba", "jiayan"):
        mt = pd.read_csv(OUT / name / "tokens_main.csv", encoding="utf-8-sig")
        ct = pd.read_csv(OUT / name / "tokens_chaoyi.csv", encoding="utf-8-sig")
        check(f"{name} token rows", len(mt) == 1163 and len(ct) == 129, f"{len(mt)}/{len(ct)}")
        check(f"{name} token IDs/order match main", mt["sent_id"].tolist() == dataset["sent_id"].tolist(), "same order")
        check(f"{name} token split match", mt["split"].tolist() == dataset["split"].tolist(), "same split")
        check(f"{name} no empty token rows", (mt["token_count"] > 0).all() and (ct["token_count"] > 0).all(), "all positive")

    result = json.loads((OUT / "comparison_results.json").read_text(encoding="utf-8"))
    metrics = pd.read_csv(OUT / "comparison_metrics.csv", encoding="utf-8-sig").set_index("tokenizer")
    j = result["metrics"]["jieba"]
    q = result["metrics"]["jiayan"]
    check("Jieba baseline 148/233", int(round(j["accuracy"] * 233)) == 148 and np.array_equal(j["confusion_matrix"], [[100, 27], [58, 48]]), f"{j['accuracy']:.6f}, {j['confusion_matrix']}")
    check("Jieba macro F1", abs(j["macro_f1"] - 0.616070563148202) < 1e-12, str(j["macro_f1"]))
    check("Jiayan 167/233", int(round(q["accuracy"] * 233)) == 167 and q["confusion_matrix"] == [[100, 27], [39, 67]], f"{q['accuracy']:.6f}, {q['confusion_matrix']}")
    check("Jiayan macro F1", abs(q["macro_f1"] - 0.7109398496240602) < 1e-12, str(q["macro_f1"]))
    check("comparison_metrics matches JSON", all(abs(metrics.loc[name, "accuracy"] - result["metrics"][name]["accuracy"]) < 1e-12 for name in ("jieba", "jiayan")), "accuracy rows")
    check("paired four cells sum 233", sum(result["paired"][k] for k in ("both_right", "both_wrong", "jieba_wrong_jiayan_right", "jieba_right_jiayan_wrong")) == 233, str(result["paired"]))
    check("paired net equation", result["paired"]["jieba_wrong_jiayan_right"] - result["paired"]["jieba_right_jiayan_wrong"] == 167 - 148, "45-26=19")
    check("zero/one feature counts", (j["test_zero_features"], j["test_one_feature"], q["test_zero_features"], q["test_one_feature"]) == (7, 20, 1, 0), str((j["test_zero_features"], j["test_one_feature"], q["test_zero_features"], q["test_one_feature"])))
    check("TF-IDF/LogReg settings", all(j["tfidf_params"] == q["tfidf_params"] and j["logistic_params"] == q["logistic_params"] for _ in [0]), str(j["tfidf_params"]) + " / " + str(j["logistic_params"]))

    baseline = result["baseline_reproduction"]
    check("Jieba saved baseline reproduced", baseline["label_mismatch"] == 0 and baseline["prob_max_abs_diff"] < 1e-12 and baseline["saved_correct"] == baseline["rerun_correct"] == 148, str(baseline))
    indep = result["independent_reproduction"]
    check("Jieba Chaoyi baseline reproduced", indep["label_mismatch"] == 0 and indep["saved_east"] == indep["rerun_east"] == 56, str(indep))

    paired = pd.read_csv(OUT / "paired_predictions.csv", encoding="utf-8-sig")
    check("paired_predictions schema", len(paired) == 233 and {"sent_id", "author", "work_title", "genre", "period_true", "text_original", "jieba_tokens", "jiayan_tokens", "jieba_pred", "jiayan_pred"}.issubset(paired.columns), str(paired.columns.tolist()))
    check("paired_predictions unique IDs", paired["sent_id"].nunique() == 233, str(paired["sent_id"].nunique()))
    ind = pd.read_csv(OUT / "independent_comparison.csv", encoding="utf-8-sig")
    check("independent_comparison 129", len(ind) == 129 and ind["sent_id"].nunique() == 129, str(len(ind)))
    check("Chaoyi 56/90", result["chaoyi"]["jieba"]["east"] == 56 and result["chaoyi"]["jiayan"]["east"] == 90, str(result["chaoyi"]))

    control = json.loads((OUT / "exploratory_jieba_simplified" / "summary.json").read_text(encoding="utf-8"))
    check("OpenCC control does not replace baseline", abs(control["metrics"]["accuracy"] - j["accuracy"]) < 1e-12 and control["chaoyi_east"] == 63, json.dumps(control, ensure_ascii=False)[:500])

    jm = json.loads((OUT / "jiayan" / "tokenization_metadata.json").read_text(encoding="utf-8"))
    check("Jiayan metadata blocker recorded", jm["tokenizer"] == "WordNgramTokenizer" and jm["jiayan_version"] == "0.0.21" and jm["char_hmm_kenlm_available"] is False and "KenLM" in jm["kenlm_blocker"], json.dumps(jm, ensure_ascii=False)[:600])

    review = (OUT / "segmentation_review.md").read_text(encoding="utf-8")
    sample = pd.read_csv(OUT / "segmentation_sample.csv", encoding="utf-8-sig")
    cases = pd.read_csv(OUT / "segmentation_cases.csv", encoding="utf-8-sig")
    terms = pd.read_csv(OUT / "term_examples.csv", encoding="utf-8-sig")
    check("segmentation sample 20 stratified", len(sample) == 20 and sample["period_true"].value_counts().to_dict() == {"西漢": 10, "東漢": 10}, str(len(sample)))
    check("segmentation outcome-selected cases", len(cases) == 10 and (cases["case"] == "改善（按結果選出）").sum() == 5 and (cases["case"] == "退步（按結果選出）").sum() == 5, str(cases["case"].value_counts().to_dict()))
    check("term audit covers names/books/terms/function words", len(terms) >= 8 and {"鴻儒", "孔子", "屈原", "春秋", "而"}.issubset(set(terms["term_traditional"])), str(terms["term_traditional"].tolist()))
    check("review discloses AI-assisted, non-gold limitation", "AI 輔助" in review and "不是分詞準確率" in review, "AI-assisted caveat present")

    # Protection: compare with the pre-sync snapshot, excluding the two files
    # deliberately updated by the Word/HTML sync task.
    pre = json.loads((ROOT / "output" / "report_sync" / "pre_sync_hashes.json").read_text(encoding="utf-8"))
    changed = []
    for rel, old in pre.items():
        p = ROOT / rel
        if not p.exists():
            changed.append((rel, "missing"))
        elif sha(p) != old:
            changed.append((rel, "changed"))
    unexpected = [x for x in changed if x[0] not in ("report.docx", "report.html")]
    check("prior data/model/exploration/report files unchanged", not unexpected, str(unexpected))
    sync_ver = json.loads((ROOT / "output" / "report_sync" / "verification.json").read_text(encoding="utf-8"))
    check("report.docx/html equal post-sync hashes", sha(ROOT / "report.docx") == sync_ver["hashes"]["report_docx"] and sha(ROOT / "report.html") == sync_ver["hashes"]["report_html"], "post-sync versions kept")
    check("report.md/pdf unchanged", sha(ROOT / "report.md") == pre["report.md"] and sha(ROOT / "report.pdf") == pre["report.pdf"], "md/pdf hashes")

    output_files = ["comparison_summary.md", "comparison_metrics.csv", "paired_predictions.csv",
                    "segmentation_review.md", "independent_comparison.csv", "engineering_record.md"]
    check("required deliverables exist", all((OUT / f).exists() for f in output_files), str([f for f in output_files if not (OUT / f).exists()]))

    result_payload = {
        "checks": checks,
        "passed": sum(1 for c in checks if c["ok"]),
        "failed": sum(1 for c in checks if not c["ok"]),
        "known_limitations": limitations,
        "hashes": {
            "report.md": sha(ROOT / "report.md"),
            "report.pdf": sha(ROOT / "report.pdf"),
            "report.docx": sha(ROOT / "report.docx"),
            "report.html": sha(ROOT / "report.html"),
            "dataset_v3": sha(DATA / "dataset_v3.csv"),
            "tokens_jieba_main": sha(OUT / "jieba" / "tokens_main.csv"),
            "tokens_jiayan_main": sha(OUT / "jiayan" / "tokens_main.csv"),
            "paired_predictions": sha(OUT / "paired_predictions.csv"),
        },
        "environment": {
            "classifier": "original project venv; Python 3.12.10; scikit-learn 1.9.1; pandas 3.0.6; numpy 2.5.3; jieba 0.42.1",
            "jiayan": "isolated venv; Python 3.12.10; jiayan 0.0.21; python-crfsuite 0.9.12; opencc-python-reimplemented 0.1.7",
            "kenlm": "not installed; build failed (no C/C++ compiler; NMake CMake platform error)",
            "jiayan_tokenizer": "WordNgramTokenizer",
            "jiayan_model": None,
            "opencc": "t2s, Jiayan arm only",
        },
    }
    out = OUT / "verification.json"
    out.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": result_payload["passed"], "failed": result_payload["failed"], "hashes": result_payload["hashes"]}, ensure_ascii=False, indent=2))
    if result_payload["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
