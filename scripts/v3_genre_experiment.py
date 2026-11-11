# -*- coding: utf-8 -*-
"""v3 same-genre comparison: full-class training vs 子書-only training.

Both models are tested on the same held-out 子書 sentences from the v3
main sample (dataset_v3.csv test split).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

import train_model as tm

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "v3"
OUT = ROOT / "output" / "v3" / "genre_experiment"
OUT.mkdir(parents=True, exist_ok=True)


def run(train_df, test_df, name):
    train = train_df.copy()
    test = test_df.copy()
    train["label"] = train["period"].map(tm.LABELS)
    test["label"] = test["period"].map(tm.LABELS)
    train_seg = tm.segment(train["text_normalized"])
    test_seg = tm.segment(test["text_normalized"])
    vectorizer = tm.build_vectorizer(ngram_max=1, min_df=2)
    X_train = vectorizer.fit_transform(train_seg)
    X_test = vectorizer.transform(test_seg)
    model = LogisticRegression(max_iter=2000, random_state=tm.SEED)
    model.fit(X_train, train["label"].astype(int).values)
    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)
    metrics, report = tm.evaluate(test, pred, prob)
    metrics["n_train"] = int(len(train))
    metrics["n_test"] = int(len(test))
    metrics["train_period"] = {k: int(v) for k, v in train["period"].value_counts().items()}
    metrics["test_period"] = {k: int(v) for k, v in test["period"].value_counts().items()}
    with open(OUT / f"metrics_{name}.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    pred_df = test.copy().reset_index(drop=True)
    pred_df["period_true"] = pred_df["period"]
    pred_df["period_pred"] = [tm.LABEL_NAMES[p] for p in pred]
    pred_df["prob_east"] = prob[:, 1]
    pred_df["prob_west"] = prob[:, 0]
    pred_df["correct"] = pred_df["period_true"] == pred_df["period_pred"]
    pred_df[["sent_id", "work_title", "author", "period_true", "period_pred",
             "prob_east", "prob_west", "correct", "text_original"]].to_csv(
        OUT / f"test_predictions_{name}.csv", index=False, encoding="utf-8-sig")
    print(name, "n_train", len(train), "n_test", len(test),
          "acc", metrics["accuracy"], "macro_f1", metrics["macro_f1"],
          "baseline", metrics["majority_baseline"])
    return metrics


def main():
    df = pd.read_csv(DATA / "dataset_v3.csv", encoding="utf-8-sig")
    train_all = df[df["split"] == "train"].copy()
    test_zip = df[(df["split"] == "test") & (df["genre_group"] == "子書")].copy()
    train_zip = train_all[train_all["genre_group"] == "子書"].copy()
    print("子書 test", len(test_zip), test_zip["period"].value_counts().to_dict())
    print("full train", len(train_all), train_all["period"].value_counts().to_dict())
    print("子書 train", len(train_zip), train_zip["period"].value_counts().to_dict())

    full = run(train_all, test_zip, "full_class")
    ziponly = run(train_zip, test_zip, "zip_only")

    lines = [
        "# 同文類對照：留出子書句",
        "",
        "兩個模型使用同一批留出的子書測試句；只改變訓練集。",
        "",
        "| 訓練 | 訓練句數 | 訓練西漢 | 訓練東漢 | 測試句數 | 測試西漢 | 測試東漢 | 多數類基準 | accuracy | macro F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, m in [("全類訓練", full), ("子書訓練", ziponly)]:
        lines.append(
            f"| {name} | {m['n_train']} | {m['train_period'].get('西漢', 0)} | "
            f"{m['train_period'].get('東漢', 0)} | {m['n_test']} | "
            f"{m['test_period'].get('西漢', 0)} | {m['test_period'].get('東漢', 0)} | "
            f"{m['majority_baseline']:.4f} | {m['accuracy']:.4f} | {m['macro_f1']:.4f} |")
    lines += [
        "",
        "混淆矩陣：",
        "",
        f"- 全類訓練：{full['confusion_matrix']}",
        f"- 子書訓練：{ziponly['confusion_matrix']}",
        "",
    ]
    (OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT / "summary.md")


if __name__ == "__main__":
    main()
