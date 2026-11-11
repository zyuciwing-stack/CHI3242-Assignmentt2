# -*- coding: utf-8 -*-
"""Train and evaluate the Western/Eastern Han logistic-regression classifier.

The main run reads data/dataset_v2.csv (or dataset_v1.csv), whose train/test
split was fixed in build_corpus.py with seed 42, stratified by period.
The vectorizer is fitted on the training split only.
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import jieba
import joblib
import qhchina
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import GroupShuffleSplit, train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
SEED = 42

LABELS = {"西漢": 0, "東漢": 1}
LABEL_NAMES = ["西漢", "東漢"]

USER_WORDS = [
    "文章", "著述", "鴻儒", "文人", "經傳", "詩賦", "辭賦", "離騷", "屈原",
    "雅頌", "風雅", "雕蟲", "篆刻", "諷諫", "作者", "篇章", "文辭", "筆墨",
    "論說", "傳書", "經藝", "鴻筆", "文采", "華藻", "模範", "儀表", "賦頌",
    "歌詩", "樂府", "石渠", "金馬", "史記", "漢書", "藝文志", "七略",
]

for word in USER_WORDS:
    jieba.add_word(word)


def setup_matplotlib():
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def load_qhchina_stopwords():
    path = Path(qhchina.__file__).resolve().parent / "data" / "stopwords" / "zh_cl_tr.txt"
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()}


def segment(texts, stopwords=None):
    out = []
    for text in texts:
        tokens = jieba.lcut(str(text))
        if stopwords:
            tokens = [t for t in tokens if t not in stopwords]
        out.append(" ".join(tokens))
    return out


def build_vectorizer(ngram_max=1, min_df=2):
    return TfidfVectorizer(
        token_pattern=r"(?u)\b\w+\b",
        min_df=min_df,
        max_df=0.9,
        sublinear_tf=True,
        ngram_range=(1, ngram_max),
    )


def fit_predict(train_df, test_df, ngram_max=1, min_df=2, stopwords=None,
                class_weight=None):
    train_seg = segment(train_df["text_normalized"], stopwords)
    test_seg = segment(test_df["text_normalized"], stopwords)
    vectorizer = build_vectorizer(ngram_max=ngram_max, min_df=min_df)
    X_train = vectorizer.fit_transform(train_seg)
    X_test = vectorizer.transform(test_seg)
    model = LogisticRegression(max_iter=2000, random_state=SEED,
                               class_weight=class_weight)
    model.fit(X_train, train_df["label"].astype(int).values)
    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)
    return vectorizer, model, X_test, pred, prob


def evaluate(test_df, pred, prob):
    y_true = test_df["label"].astype(int).values
    cm = confusion_matrix(y_true, pred, labels=[0, 1])
    report = classification_report(y_true, pred, labels=[0, 1],
                                   target_names=LABEL_NAMES, output_dict=True,
                                   zero_division=0)
    support = {name: int(report[name]["support"]) for name in LABEL_NAMES}
    majority_class = max(support, key=support.get)
    metrics = {
        "accuracy": float(accuracy_score(y_true, pred)),
        "majority_class": majority_class,
        "majority_baseline": support[majority_class] / sum(support.values()),
        "confusion_matrix": cm.tolist(),
        "precision": {name: float(report[name]["precision"]) for name in LABEL_NAMES},
        "recall": {name: float(report[name]["recall"]) for name in LABEL_NAMES},
        "f1": {name: float(report[name]["f1-score"]) for name in LABEL_NAMES},
        "support": support,
        "macro_f1": float(f1_score(y_true, pred, average="macro")),
        "weighted_f1": float(f1_score(y_true, pred, average="weighted")),
    }
    return metrics, report


def top_contributions(row_vector, model, feature_names, top_n=5):
    coef = model.coef_[0]
    indices = row_vector.indices
    values = row_vector.data
    contrib = [(feature_names[i], float(values[j] * coef[i]))
               for j, i in enumerate(indices)]
    contrib.sort(key=lambda x: abs(x[1]), reverse=True)
    return contrib[:top_n]


def save_run(train_df, test_df, vectorizer, model, pred, prob, metrics, report,
             output_dir, run_name, config):
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # metrics
    with open(output_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    # classification report
    report_rows = []
    for name in LABEL_NAMES:
        report_rows.append({
            "class": name,
            "precision": report[name]["precision"],
            "recall": report[name]["recall"],
            "f1": report[name]["f1-score"],
            "support": report[name]["support"],
        })
    pd.DataFrame(report_rows).to_csv(output_dir / "classification_report.csv",
                                     index=False, encoding="utf-8-sig")

    # test predictions
    pred_df = test_df.copy().reset_index(drop=True)
    pred_df["period_true"] = pred_df["period"]
    pred_df["period_pred"] = [LABEL_NAMES[p] for p in pred]
    pred_df["prob_east"] = prob[:, 1]
    pred_df["prob_west"] = prob[:, 0]
    pred_df["correct"] = pred_df["period_true"] == pred_df["period_pred"]
    cols = ["sent_id", "work_id", "work_title", "author", "genre", "genre_group",
            "period_true", "period_pred", "prob_east", "prob_west", "correct",
            "text_original", "text_normalized"]
    pred_df[cols].to_csv(output_dir / "test_predictions.csv", index=False,
                         encoding="utf-8-sig")

    # top features
    feature_names = np.array(vectorizer.get_feature_names_out())
    coef = model.coef_[0]
    order = np.argsort(coef)
    top = []
    for idx in order[-30:][::-1]:
        top.append({"feature": feature_names[idx], "coefficient": float(coef[idx]),
                    "direction": "東漢"})
    for idx in order[:30]:
        top.append({"feature": feature_names[idx], "coefficient": float(coef[idx]),
                    "direction": "西漢"})
    pd.DataFrame(top).to_csv(output_dir / "top_features.csv", index=False,
                             encoding="utf-8-sig")

    # misclassified examples with contributions
    X_test = vectorizer.transform(segment(test_df["text_normalized"]))
    errors = []
    for i in range(len(test_df)):
        if pred[i] == test_df["label"].values[i]:
            continue
        row = test_df.iloc[i]
        contrib = top_contributions(X_test[i], model, feature_names, top_n=6)
        related = "; ".join(f"{tok}({val:+.3f})" for tok, val in contrib)
        errors.append({
            "sent_id": row["sent_id"],
            "work_title": row["work_title"],
            "author": row["author"],
            "genre": row["genre"],
            "period_true": row["period"],
            "period_pred": LABEL_NAMES[pred[i]],
            "prob_east": float(prob[i, 1]),
            "prob_west": float(prob[i, 0]),
            "text_original": row["text_original"],
            "related_words": related,
        })
    err_df = pd.DataFrame(errors)
    err_df.to_csv(output_dir / "misclassified_examples.csv", index=False,
                  encoding="utf-8-sig")

    md = ["# 誤判例", ""]
    fp = err_df[(err_df["period_true"] == "西漢") & (err_df["period_pred"] == "東漢")]
    fn = err_df[(err_df["period_true"] == "東漢") & (err_df["period_pred"] == "西漢")]
    for title, sub in [("西漢誤判為東漢", fp.head(5)), ("東漢誤判為西漢", fn.head(5))]:
        md.append(f"## {title}")
        md.append("")
        for _, row in sub.iterrows():
            md.append(f"- **{row['sent_id']}｜{row['author']}〈{row['work_title']}〉**")
            md.append(f"  - 原句：{row['text_original']}")
            md.append(f"  - 真實／預測：{row['period_true']}／{row['period_pred']}"
                      f"（P(東漢)={row['prob_east']:.3f}）")
            md.append(f"  - 相關詞：{row['related_words']}")
        md.append("")
    (output_dir / "misclassified_examples.md").write_text("\n".join(md), encoding="utf-8")

    # confusion matrix figure
    cm = np.array(metrics["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1], LABEL_NAMES)
    ax.set_yticks([0, 1], LABEL_NAMES)
    ax.set_xlabel("預測")
    ax.set_ylabel("真實")
    ax.set_title(f"Confusion matrix ({run_name})")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black",
                    fontsize=14)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(fig_dir / "confusion_matrix.png", dpi=200)
    plt.close(fig)

    # top features figure
    top_df = pd.DataFrame(top)
    east = top_df[top_df["direction"] == "東漢"].head(20)
    west = top_df[top_df["direction"] == "西漢"].head(20)
    fig, axes = plt.subplots(1, 2, figsize=(11, 6))
    axes[0].barh(east["feature"][::-1], east["coefficient"][::-1], color="#c44e52")
    axes[0].set_title("Top 20 東漢 features")
    axes[1].barh(west["feature"][::-1], west["coefficient"][::-1], color="#4c72b0")
    axes[1].set_title("Top 20 西漢 features")
    for ax in axes:
        ax.axvline(0, color="black", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(fig_dir / "top_features.png", dpi=200)
    plt.close(fig)

    # model and metadata
    joblib.dump({"vectorizer": vectorizer, "model": model, "config": config},
                output_dir / "model.joblib")
    metadata = {
        "run_name": run_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "train_period": {k: int(v) for k, v in train_df["period"].value_counts().items()},
        "test_period": {k: int(v) for k, v in test_df["period"].value_counts().items()},
        "n_features": int(len(feature_names)),
        "metrics": metrics,
    }
    with open(output_dir / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return err_df


def predict_texts(df, vectorizer, model, text_col="text_normalized"):
    seg = segment(df[text_col])
    X = vectorizer.transform(seg)
    pred = model.predict(X)
    prob = model.predict_proba(X)
    out = df.copy().reset_index(drop=True)
    out["period_pred"] = [LABEL_NAMES[p] for p in pred]
    out["prob_east"] = prob[:, 1]
    out["prob_west"] = prob[:, 0]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DATA / "dataset_v2.csv"))
    parser.add_argument("--sentences-path", default=str(DATA / "sentences_all.csv"))
    parser.add_argument("--output-dir", default=str(OUTPUT))
    parser.add_argument("--run-name", default="v2_main")
    parser.add_argument("--ngram-max", type=int, default=1)
    parser.add_argument("--min-df", type=int, default=2)
    parser.add_argument("--use-stopwords", action="store_true")
    parser.add_argument("--class-weight", default=None)
    parser.add_argument("--full", action="store_true",
                        help="use all trainable v2 sentences, then 80/20 split")
    parser.add_argument("--grouped", action="store_true",
                        help="grouped split by work_id, no work crosses train/test")
    parser.add_argument("--skip-independent", action="store_true")
    parser.add_argument("--leave-author-out", default=None,
                        help="train without this author, test on all his/her sentences")
    args = parser.parse_args()

    setup_matplotlib()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = Path(args.dataset)
    try:
        dataset_path = dataset_path.resolve().relative_to(ROOT)
    except ValueError:
        pass
    config = {
        "dataset": str(dataset_path),
        "ngram_max": args.ngram_max,
        "min_df": args.min_df,
        "use_stopwords": args.use_stopwords,
        "class_weight": args.class_weight,
        "full": args.full,
        "grouped": args.grouped,
        "seed": SEED,
        "jieba_user_words": USER_WORDS,
    }
    config["sentences_path"] = str(args.sentences_path)
    if args.full or args.leave_author_out:
        config["dataset"] = str(Path(args.sentences_path).resolve())

    if args.leave_author_out:
        df = pd.read_csv(args.sentences_path, encoding="utf-8-sig")
        df = df[df["include_full"] & (df["version_added"] <= 2)].copy()
        df = df.reset_index(drop=True)
        df["label"] = df["period"].map(LABELS)
        train_df = df[(df["trainable"]) &
                      (df["author"] != args.leave_author_out)].copy()
        test_df = df[df["author"] == args.leave_author_out].copy()
        config["leave_author_out"] = args.leave_author_out
    elif args.full:
        df = pd.read_csv(args.sentences_path, encoding="utf-8-sig")
        df = df[(df["trainable"]) & (df["version_added"] <= 2)].copy()
        df = df.reset_index(drop=True)
        df["label"] = df["period"].map(LABELS)
        train_idx, test_idx = train_test_split(
            df.index, test_size=0.2, random_state=SEED, stratify=df["label"])
        train_df = df.loc[train_idx].copy()
        test_df = df.loc[test_idx].copy()
    elif args.grouped:
        df = pd.read_csv(args.dataset, encoding="utf-8-sig").reset_index(drop=True)
        df["label"] = df["period"].map(LABELS)
        best = None
        total = len(df)
        for train_idx, test_idx in GroupShuffleSplit(
                n_splits=80, test_size=0.2, random_state=SEED).split(
                    df, groups=df["work_id"]):
            test = df.loc[test_idx]
            counts = test["period"].value_counts().to_dict()
            n_east = counts.get("東漢", 0)
            n_west = counts.get("西漢", 0)
            score = abs(len(test) / total - 0.2) + abs(n_east / max(len(test), 1) - 0.5) * 0.5
            if min(n_east, n_west) < 20:
                score += 1.0
            if best is None or score < best[0]:
                best = (score, train_idx, test_idx)
        _, train_idx, test_idx = best
        train_df = df.loc[train_idx].copy()
        test_df = df.loc[test_idx].copy()
        split_map = pd.concat([
            train_df[["work_id"]].assign(split="train"),
            test_df[["work_id"]].assign(split="test"),
        ]).drop_duplicates().sort_values("work_id")
        split_map.to_csv(output_dir / "group_split.csv", index=False,
                         encoding="utf-8-sig")
    else:
        df = pd.read_csv(args.dataset, encoding="utf-8-sig")
        df["label"] = df["period"].map(LABELS)
        train_df = df[df["split"] == "train"].copy()
        test_df = df[df["split"] == "test"].copy()

    stopwords = load_qhchina_stopwords() if args.use_stopwords else None
    if args.use_stopwords:
        config["stopwords"] = {
            "source": "qhchina 0.2.7 zh_cl_tr.txt",
            "path": "qhchina/data/stopwords/zh_cl_tr.txt",
            "count": len(stopwords),
        }

    vectorizer, model, X_test, pred, prob = fit_predict(
        train_df, test_df, ngram_max=args.ngram_max, min_df=args.min_df,
        stopwords=stopwords, class_weight=args.class_weight)
    metrics, report = evaluate(test_df, pred, prob)
    err_df = save_run(train_df, test_df, vectorizer, model, pred, prob,
                      metrics, report, output_dir, args.run_name, config)

    print(f"\n{args.run_name}: accuracy={metrics['accuracy']:.4f} "
          f"macro_f1={metrics['macro_f1']:.4f}")
    print("confusion matrix:", metrics["confusion_matrix"])
    print("per class:", metrics["precision"], metrics["recall"], metrics["f1"])

    if not args.skip_independent:
        all_df = pd.read_csv(args.sentences_path, encoding="utf-8-sig")
        reserved = all_df[(all_df["work_id"] == "E01") &
                          (all_df["include_full"])].copy()
        if len(reserved):
            reserved_pred = predict_texts(reserved, vectorizer, model)
            reserved_pred.to_csv(output_dir / "independent_predictions.csv",
                                 index=False, encoding="utf-8-sig")
            reserved_summary = {
                "text": "論衡·超奇",
                "n_sentences": int(len(reserved_pred)),
                "true_period": "東漢",
                "accuracy": float((reserved_pred["period_pred"] == "東漢").mean()),
                "prop_pred_east": float((reserved_pred["period_pred"] == "東漢").mean()),
                "mean_prob_east": float(reserved_pred["prob_east"].mean()),
            }
            with open(output_dir / "independent_summary.json", "w",
                      encoding="utf-8") as f:
                json.dump(reserved_summary, f, ensure_ascii=False, indent=2)
            print("independent (超奇):", reserved_summary)

        maoshi = all_df[(all_df["work_id"] == "U01") &
                        (all_df["include_full"])].copy()
        if len(maoshi):
            maoshi_pred = predict_texts(maoshi, vectorizer, model)
            maoshi_pred.to_csv(output_dir / "probe_maoshi_predictions.csv",
                               index=False, encoding="utf-8-sig")
            maoshi_summary = {
                "text": "毛詩序（大序）",
                "n_sentences": int(len(maoshi_pred)),
                "prop_pred_east": float((maoshi_pred["period_pred"] == "東漢").mean()),
                "mean_prob_east": float(maoshi_pred["prob_east"].mean()),
            }
            with open(output_dir / "probe_maoshi_summary.json", "w",
                      encoding="utf-8") as f:
                json.dump(maoshi_summary, f, ensure_ascii=False, indent=2)
            print("probe (毛詩序):", maoshi_summary)


if __name__ == "__main__":
    main()
