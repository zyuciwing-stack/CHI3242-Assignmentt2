# -*- coding: utf-8 -*-
"""Fit the fixed TF-IDF + logistic-regression pipeline to two token streams.

Run this in the original analysis environment (the same scikit-learn version)
after the Jieba and Jiayan token files have been produced.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "v3"
OUT = ROOT / "output" / "tokenizer_comparison"
LABELS = {"西漢": 0, "東漢": 1}
NAMES = ["西漢", "東漢"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit_and_predict(train, test, train_tokens, test_tokens):
    vectorizer = TfidfVectorizer(
        token_pattern=r"(?u)\b\w+\b",
        min_df=2,
        max_df=0.9,
        sublinear_tf=True,
        ngram_range=(1, 1),
    )
    X_train = vectorizer.fit_transform(train_tokens)
    X_test = vectorizer.transform(test_tokens)
    model = LogisticRegression(
        max_iter=2000, random_state=42, class_weight=None
    )
    model.fit(X_train, train["label"].astype(int).values)
    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)
    return vectorizer, model, X_train, X_test, pred, prob


def metrics_for(test, pred, prob, vectorizer, X_test):
    y = test["label"].astype(int).values
    cm = confusion_matrix(y, pred, labels=[0, 1])
    nnz = np.asarray(X_test.sum(axis=1)).ravel()
    support = {NAMES[i]: int((y == i).sum()) for i in range(2)}
    majority = max(support, key=support.get)
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro")),
        "weighted_f1": float(f1_score(y, pred, average="weighted")),
        "majority_class": majority,
        "majority_baseline": support[majority] / len(y),
        "confusion_matrix": cm.tolist(),
        "precision": {NAMES[i]: float(precision_score(y == i, pred == i, zero_division=0)) for i in range(2)},
        "recall": {NAMES[i]: float(recall_score(y == i, pred == i, zero_division=0)) for i in range(2)},
        "f1": {NAMES[i]: float(f1_score(y == i, pred == i, zero_division=0)) for i in range(2)},
        "support": support,
        "vocabulary_size": int(len(vectorizer.vocabulary_)),
        "test_zero_features": int((nnz == 0).sum()),
        "test_one_feature": int((nnz == 1).sum()),
        "prob_max": float(prob.max(axis=1).max()),
    }


def predictions_frame(df, pred, prob):
    out = df[["sent_id", "work_id", "work_title", "author", "genre", "genre_group",
              "period", "text_original", "text_normalized"]].copy()
    out = out.rename(columns={"period": "period_true"})
    out["period_pred"] = [NAMES[int(x)] for x in pred]
    out["prob_east"] = prob[:, 1]
    out["prob_west"] = prob[:, 0]
    out["correct"] = out["period_true"] == out["period_pred"]
    return out


def main() -> None:
    dataset = pd.read_csv(DATA / "dataset_v3.csv", encoding="utf-8-sig")
    chaoyi = pd.read_csv(DATA / "sentences_all.csv", encoding="utf-8-sig")
    chaoyi = chaoyi[chaoyi["work_id"] == "E01"].copy()
    dataset["label"] = dataset["period"].map(LABELS)
    chaoyi["label"] = chaoyi["period"].map(LABELS)

    train = dataset[dataset["split"] == "train"].copy()
    test = dataset[dataset["split"] == "test"].copy()
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)
    chaoyi = chaoyi.reset_index(drop=True)

    train_ids = train["sent_id"].tolist()
    test_ids = test["sent_id"].tolist()
    assert not set(train_ids) & set(test_ids)
    assert len(train_ids) == 930 and len(test_ids) == 233

    results = {}
    paired_frames = {}
    token_frames = {}
    for name in ("jieba", "jiayan"):
        tok_dir = OUT / name
        main_tok = pd.read_csv(tok_dir / "tokens_main.csv", encoding="utf-8-sig")
        chao_tok = pd.read_csv(tok_dir / "tokens_chaoyi.csv", encoding="utf-8-sig")
        assert main_tok["sent_id"].tolist() == dataset["sent_id"].tolist()
        assert chao_tok["sent_id"].tolist() == chaoyi["sent_id"].tolist()
        train_tok = main_tok.set_index("sent_id").loc[train_ids, "tokens"].tolist()
        test_tok = main_tok.set_index("sent_id").loc[test_ids, "tokens"].tolist()
        chaoyi_tok = chao_tok.set_index("sent_id").loc[chaoyi["sent_id"].tolist(), "tokens"].tolist()
        vectorizer, model, X_train, X_test, pred, prob = fit_and_predict(
            train, test, train_tok, test_tok)
        metrics = metrics_for(test, pred, prob, vectorizer, X_test)
        pred_frame = predictions_frame(test, pred, prob)
        pred_frame["tokens"] = test_tok
        metrics["train_size"] = len(train)
        metrics["test_size"] = len(test)
        metrics["train_period"] = train["period"].value_counts().to_dict()
        metrics["test_period"] = test["period"].value_counts().to_dict()
        metrics["tfidf_params"] = {
            "token_pattern": r"(?u)\b\w+\b",
            "min_df": 2, "max_df": 0.9, "sublinear_tf": True, "ngram_range": [1, 1],
        }
        metrics["logistic_params"] = {
            "max_iter": 2000, "random_state": 42, "class_weight": None,
            "C": 1.0, "solver": "lbfgs",
        }
        metrics["tokenizer"] = name
        (tok_dir / "metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        pred_frame.to_csv(tok_dir / "test_predictions.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame({
            "feature": vectorizer.get_feature_names_out(),
            "index": np.arange(len(vectorizer.vocabulary_)),
        }).to_csv(tok_dir / "feature_names.csv", index=False, encoding="utf-8-sig")
        joblib.dump({"vectorizer": vectorizer, "model": model}, tok_dir / "model.joblib")

        # Chaoyi is transformed by the model fitted on the 930 training sentences.
        Xc = vectorizer.transform(chaoyi_tok)
        pc = model.predict(Xc)
        probc = model.predict_proba(Xc)
        cf = predictions_frame(chaoyi, pc, probc)
        cf["tokens"] = chaoyi_tok
        cf["zero_features"] = np.asarray(Xc.sum(axis=1)).ravel() == 0
        cf["one_feature"] = np.asarray(Xc.sum(axis=1)).ravel() == 1
        cf.to_csv(tok_dir / "independent_predictions.csv", index=False, encoding="utf-8-sig")
        indep = {
            "n": int(len(cf)),
            "east": int((cf["period_pred"] == "東漢").sum()),
            "west": int((cf["period_pred"] == "西漢").sum()),
            "zero_features": int(cf["zero_features"].sum()),
            "one_feature": int(cf["one_feature"].sum()),
            "prob_east_mean": float(cf["prob_east"].mean()),
        }
        (tok_dir / "independent_metrics.json").write_text(
            json.dumps(indep, ensure_ascii=False, indent=2), encoding="utf-8")

        results[name] = metrics
        paired_frames[name] = pred_frame[["sent_id", "period_pred", "prob_east", "correct"]].rename(
            columns={"period_pred": f"{name}_pred", "prob_east": f"{name}_prob_east",
                     "correct": f"{name}_correct"})
        token_frames[name] = main_tok[["sent_id", "tokens"]].rename(
            columns={"tokens": f"{name}_tokens"})

    # Combined Chaoyi comparison.csv
    ji = pd.read_csv(OUT / "jieba" / "independent_predictions.csv", encoding="utf-8-sig")
    ja = pd.read_csv(OUT / "jiayan" / "independent_predictions.csv", encoding="utf-8-sig")
    ind_compare = ji.merge(ja, on="sent_id", suffixes=("_jieba", "_jiayan"))
    ind_compare.to_csv(OUT / "independent_comparison.csv", index=False, encoding="utf-8-sig")

    # Reproduce the saved Jieba baseline.
    saved = pd.read_csv(ROOT / "output" / "v3" / "test_predictions.csv", encoding="utf-8-sig")
    j = paired_frames["jieba"].rename(columns={"jieba_pred": "period_pred", "jieba_prob_east": "prob_east"})
    cmp = saved.merge(j, on="sent_id", suffixes=("_saved", "_rerun"))
    label_mismatch = int((cmp["period_pred_saved"] != cmp["period_pred_rerun"]).sum())
    prob_max_diff = float((cmp["prob_east_saved"] - cmp["prob_east_rerun"]).abs().max())
    baseline = {
        "label_mismatch": label_mismatch,
        "prob_max_abs_diff": prob_max_diff,
        "n": int(len(cmp)),
        "saved_correct": int(cmp["correct"].sum()),
        "rerun_correct": int(cmp["jieba_correct"].sum()),
    }

    # Saved independent Jieba comparison.
    saved_ind = pd.read_csv(ROOT / "output" / "v3" / "independent_predictions.csv", encoding="utf-8-sig")
    ind = pd.read_csv(OUT / "jieba" / "independent_predictions.csv", encoding="utf-8-sig")
    ind_cmp = saved_ind.merge(ind, on="sent_id", suffixes=("_saved", "_rerun"))
    indep_repro = {
        "label_mismatch": int((ind_cmp["period_pred_saved"] != ind_cmp["period_pred_rerun"]).sum()),
        "prob_max_abs_diff": float((ind_cmp["prob_east_saved"] - ind_cmp["prob_east_rerun"]).abs().max()),
        "saved_east": int((ind_cmp["period_pred_saved"] == "東漢").sum()),
        "rerun_east": int((ind_cmp["period_pred_rerun"] == "東漢").sum()),
        "n": int(len(ind_cmp)),
    }

    # Paired main comparison.
    paired = paired_frames["jieba"].merge(
        paired_frames["jiayan"], on="sent_id", how="inner")
    paired = paired.merge(
        test[["sent_id", "work_id", "work_title", "author", "genre", "genre_group",
              "period", "text_original", "text_normalized"]], on="sent_id", how="left")
    paired = paired.merge(token_frames["jieba"], on="sent_id", how="left")
    paired = paired.merge(token_frames["jiayan"], on="sent_id", how="left")
    paired = paired.rename(columns={"period": "period_true"})
    paired["jieba_correct"] = paired["jieba_correct"].astype(bool)
    paired["jiayan_correct"] = paired["jiayan_correct"].astype(bool)
    b = int((~paired["jieba_correct"] & paired["jiayan_correct"]).sum())
    c = int((paired["jieba_correct"] & ~paired["jiayan_correct"]).sum())
    both_right = int((paired["jieba_correct"] & paired["jiayan_correct"]).sum())
    both_wrong = int((~paired["jieba_correct"] & ~paired["jiayan_correct"]).sum())
    exact = binomtest(b, b + c, 0.5) if (b + c) else None
    paired["improvement"] = np.where(~paired["jieba_correct"] & paired["jiayan_correct"], "jieba_wrong_jiayan_right",
                              np.where(paired["jieba_correct"] & ~paired["jiayan_correct"], "jieba_right_jiayan_wrong",
                                       np.where(paired["jieba_correct"], "both_right", "both_wrong")))
    paired.to_csv(OUT / "paired_predictions.csv", index=False, encoding="utf-8-sig")

    metrics_rows = []
    for name in ("jieba", "jiayan"):
        m = results[name]
        metrics_rows.append({
            "tokenizer": name,
            "accuracy": m["accuracy"],
            "balanced_accuracy": m["balanced_accuracy"],
            "macro_f1": m["macro_f1"],
            "east_precision": m["precision"]["東漢"],
            "east_recall": m["recall"]["東漢"],
            "east_f1": m["f1"]["東漢"],
            "west_precision": m["precision"]["西漢"],
            "west_recall": m["recall"]["西漢"],
            "west_f1": m["f1"]["西漢"],
            "majority_baseline": m["majority_baseline"],
            "vocabulary_size": m["vocabulary_size"],
            "test_zero_features": m["test_zero_features"],
            "test_one_feature": m["test_one_feature"],
            "correct": int(round(m["accuracy"] * len(test))),
        })
    pd.DataFrame(metrics_rows).to_csv(OUT / "comparison_metrics.csv", index=False, encoding="utf-8-sig")

    summary = {
        "fixed_split": {
            "n": len(dataset), "train": len(train), "test": len(test),
            "train_period": train["period"].value_counts().to_dict(),
            "test_period": test["period"].value_counts().to_dict(),
            "ids_train_first": train_ids[:3], "ids_test_first": test_ids[:3],
        },
        "baseline_reproduction": baseline,
        "independent_reproduction": indep_repro,
        "metrics": results,
        "paired": {
            "n": int(len(paired)),
            "both_right": both_right,
            "both_wrong": both_wrong,
            "jieba_wrong_jiayan_right": b,
            "jieba_right_jiayan_wrong": c,
            "accuracy_delta": results["jiayan"]["accuracy"] - results["jieba"]["accuracy"],
            "macro_f1_delta": results["jiayan"]["macro_f1"] - results["jieba"]["macro_f1"],
            "east_recall_delta": results["jiayan"]["recall"]["東漢"] - results["jieba"]["recall"]["東漢"],
            "net_correct": b - c,
            "mcnemar_binomial_p_exploratory": float(exact.pvalue) if exact else None,
            "mcnemar_note": "paired exact binomial on discordant pairs; sentences within works are not independent; exploratory only",
        },
        "chaoyi": {
            name: json.loads((OUT / name / "independent_metrics.json").read_text(encoding="utf-8"))
            for name in ("jieba", "jiayan")
        },
        "token_counts": {
            name: {
                "main_total": int(pd.read_csv(OUT / name / "tokens_main.csv", encoding="utf-8-sig")["token_count"].sum()),
                "main_mean": float(pd.read_csv(OUT / name / "tokens_main.csv", encoding="utf-8-sig")["token_count"].mean()),
            }
            for name in ("jieba", "jiayan")
        },
        "hashes": {
            "tokens_jieba_main": sha(OUT / "jieba" / "tokens_main.csv"),
            "tokens_jiayan_main": sha(OUT / "jiayan" / "tokens_main.csv"),
            "test_predictions_saved": sha(ROOT / "output" / "v3" / "test_predictions.csv"),
            "dataset_v3": sha(DATA / "dataset_v3.csv"),
        },
    }
    (OUT / "comparison_results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
