# -*- coding: utf-8 -*-
"""Exploratory control: Jieba on OpenCC-simplified text, same classifier."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "v3"
OUT = ROOT / "output" / "tokenizer_comparison" / "exploratory_jieba_simplified"
LABELS = {"西漢": 0, "東漢": 1}
NAMES = ["西漢", "東漢"]

import sys
sys.path.insert(0, str(ROOT / "scripts" / "tokenizer_comparison"))
from run_comparison import fit_and_predict, metrics_for, predictions_frame  # noqa: E402


def main() -> None:
    dataset = pd.read_csv(DATA / "dataset_v3.csv", encoding="utf-8-sig")
    chaoyi = pd.read_csv(DATA / "sentences_all.csv", encoding="utf-8-sig")
    chaoyi = chaoyi[chaoyi["work_id"] == "E01"].copy()
    dataset["label"] = dataset["period"].map(LABELS)
    chaoyi["label"] = chaoyi["period"].map(LABELS)
    train = dataset[dataset["split"] == "train"].reset_index(drop=True)
    test = dataset[dataset["split"] == "test"].reset_index(drop=True)
    chaoyi = chaoyi.reset_index(drop=True)

    main_tok = pd.read_csv(OUT / "tokens_main.csv", encoding="utf-8-sig")
    chao_tok = pd.read_csv(OUT / "tokens_chaoyi.csv", encoding="utf-8-sig")
    tok = main_tok.set_index("sent_id")
    train_tok = tok.loc[train["sent_id"], "tokens"].tolist()
    test_tok = tok.loc[test["sent_id"], "tokens"].tolist()
    vectorizer, model, X_train, X_test, pred, prob = fit_and_predict(
        train, test, train_tok, test_tok)
    metrics = metrics_for(test, pred, prob, vectorizer, X_test)
    metrics["tokenizer"] = "jieba_on_opencc_simplified"
    metrics["note"] = "exploratory control, not a replacement for the main Jieba baseline"
    (OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    pf = predictions_frame(test, pred, prob)
    pf["tokens"] = test_tok
    pf.to_csv(OUT / "test_predictions.csv", index=False, encoding="utf-8-sig")

    Xc = vectorizer.transform(chao_tok.set_index("sent_id").loc[chaoyi["sent_id"], "tokens"].tolist())
    pc = model.predict(Xc)
    probc = model.predict_proba(Xc)
    cf = predictions_frame(chaoyi, pc, probc)
    cf["tokens"] = chao_tok.set_index("sent_id").loc[chaoyi["sent_id"], "tokens"].tolist()
    cf["zero_features"] = np.asarray(Xc.sum(axis=1)).ravel() == 0
    cf.to_csv(OUT / "independent_predictions.csv", index=False, encoding="utf-8-sig")
    summary = {
        "metrics": metrics,
        "chaoyi_east": int((cf["period_pred"] == "東漢").sum()),
        "chaoyi_zero_features": int(cf["zero_features"].sum()),
        "token_total": int(main_tok["token_count"].sum()),
        "token_mean": float(main_tok["token_count"].mean()),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
