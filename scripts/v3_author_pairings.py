# -*- coding: utf-8 -*-
"""v3 cross-author comparison: four 子書 Western/Eastern Han held-out pairs.

For each pair, train on all authors outside the pair (full-class), and also
on 子書 authors outside the pair (子書-only), then test on all sentences by
the two held-out authors. Train/test authors never overlap.
"""

import json
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

import train_model as tm

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "v3"
OUT = ROOT / "output" / "v3" / "author_pairings"
OUT.mkdir(parents=True, exist_ok=True)

PAIRS = [
    ("P1_liuan_wangchong", "劉安", "王充"),
    ("P2_liuan_huantan", "劉安", "桓譚"),
    ("P3_yangxiong_wangchong", "揚雄", "王充"),
    ("P4_yangxiong_huantan", "揚雄", "桓譚"),
]


def run(train_df, test_df, out_dir, name):
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
    metrics, _ = tm.evaluate(test, pred, prob)
    metrics["n_train"] = int(len(train))
    metrics["n_test"] = int(len(test))
    metrics["train_period"] = {k: int(v) for k, v in train["period"].value_counts().items()}
    metrics["test_period"] = {k: int(v) for k, v in test["period"].value_counts().items()}
    with open(out_dir / f"metrics_{name}.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    pred_df = test.copy().reset_index(drop=True)
    pred_df["period_true"] = pred_df["period"]
    pred_df["period_pred"] = [tm.LABEL_NAMES[p] for p in pred]
    pred_df["prob_east"] = prob[:, 1]
    pred_df["prob_west"] = prob[:, 0]
    pred_df["correct"] = pred_df["period_true"] == pred_df["period_pred"]
    pred_df[["sent_id", "work_title", "author", "period_true", "period_pred",
             "prob_east", "prob_west", "correct", "text_original"]].to_csv(
        out_dir / f"test_predictions_{name}.csv", index=False, encoding="utf-8-sig")
    return metrics


def main():
    df = pd.read_csv(DATA / "sentences_all.csv", encoding="utf-8-sig")
    df = df[(df["trainable"]) & (df["include_full"]) &
            (df["version_added"] <= 3) &
            (df["period"].isin(["西漢", "東漢"]))].copy()

    rows = []
    for pair_id, west_author, east_author in PAIRS:
        test_authors = [west_author, east_author]
        test = df[df["author"].isin(test_authors)].copy()
        train_full = df[~df["author"].isin(test_authors)].copy()
        train_zip = train_full[train_full["genre_group"] == "子書"].copy()
        out_dir = OUT / pair_id
        out_dir.mkdir(parents=True, exist_ok=True)

        full = run(train_full, test, out_dir, "full_class")
        ziponly = run(train_zip, test, out_dir, "zip_only")

        info = {
            "pair": pair_id,
            "west_author": west_author,
            "east_author": east_author,
            "test_authors": test_authors,
            "train_authors_full": sorted(train_full["author"].unique().tolist()),
            "train_authors_zip": sorted(train_zip["author"].unique().tolist()),
            "test_sentences": int(len(test)),
            "test_period": {k: int(v) for k, v in test["period"].value_counts().items()},
            "train_full_sentences": int(len(train_full)),
            "train_full_period": {k: int(v) for k, v in train_full["period"].value_counts().items()},
            "train_zip_sentences": int(len(train_zip)),
            "train_zip_period": {k: int(v) for k, v in train_zip["period"].value_counts().items()},
            "baseline": full["majority_baseline"],
            "baseline_class": full["majority_class"],
        }
        (out_dir / "split_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2),
                                                 encoding="utf-8")
        rows.append({
            "pair": pair_id,
            "west_author": west_author,
            "east_author": east_author,
            "test_sentences": len(test),
            "test_west": info["test_period"].get("西漢", 0),
            "test_east": info["test_period"].get("東漢", 0),
            "baseline": full["majority_baseline"],
            "baseline_class": full["majority_class"],
            "train_full": len(train_full),
            "train_zip": len(train_zip),
            "full_acc": full["accuracy"],
            "full_macro_f1": full["macro_f1"],
            "full_east_recall": full["recall"]["東漢"],
            "zip_acc": ziponly["accuracy"],
            "zip_macro_f1": ziponly["macro_f1"],
            "zip_east_recall": ziponly["recall"]["東漢"],
        })
        print(pair_id, "test", len(test), "train_full", len(train_full),
              "train_zip", len(train_zip), "full", full["accuracy"],
              "zip", ziponly["accuracy"])

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "summary.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# 四種子書西漢／東漢留出配對",
        "",
        "每組訓練與測試作者不重疊；測試作者在四組中會重複使用，分開報告。",
        "測試集不含〈超奇〉（E01 仍整篇留出）。",
        "",
        "| pair | 西漢測試作者 | 東漢測試作者 | 測試句數 | 西漢 | 東漢 | 當組基準 | 全類訓練 n | 子書訓練 n | 全類 acc | 全類 macro F1 | 子書 acc | 子書 macro F1 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['pair']} | {row['west_author']} | {row['east_author']} | "
            f"{row['test_sentences']} | {row['test_west']} | {row['test_east']} | "
            f"{row['baseline_class']} {row['baseline']:.4f} | {row['train_full']} | "
            f"{row['train_zip']} | {row['full_acc']:.4f} | {row['full_macro_f1']:.4f} | "
            f"{row['zip_acc']:.4f} | {row['zip_macro_f1']:.4f} |")
    lines += [
        "",
        "各組混淆矩陣與逐句預測見 `P*/metrics_*.json`、`P*/test_predictions_*.csv`。",
        "",
    ]
    (OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT / "summary.md")


if __name__ == "__main__":
    main()
