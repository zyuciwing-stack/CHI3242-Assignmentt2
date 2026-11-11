# -*- coding: utf-8 -*-
"""Build the fixed, outcome-independent sample and transparent case review."""

from __future__ import annotations

import random
from pathlib import Path

import opencc
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "tokenizer_comparison"
SEED = 20261111


def sample_stratified(df: pd.DataFrame, n_per_period: int = 10) -> pd.DataFrame:
    rng = random.Random(SEED)
    selected = []
    for period in ("西漢", "東漢"):
        pool = df[df["period_true"] == period].copy()
        authors = sorted(pool["author"].unique().tolist())
        rng.shuffle(authors)
        order = {}
        for author in authors:
            rows = pool[pool["author"] == author].reset_index(drop=True)
            order[author] = list(range(len(rows)))
            rng.shuffle(order[author])
        period_selected = []
        while len(period_selected) < n_per_period:
            added = False
            for author in authors:
                if len(period_selected) >= n_per_period:
                    break
                if order[author]:
                    idx = order[author].pop(0)
                    period_selected.append(pool[pool["author"] == author].iloc[idx])
                    added = True
            if not added:
                break
        selected.extend(period_selected)
    return pd.DataFrame(selected).reset_index(drop=True)


def md_table(df: pd.DataFrame, columns, headers=None) -> str:
    headers = headers or columns
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(["---"] * len(columns)) + "|"]
    for _, row in df.iterrows():
        vals = []
        for c in columns:
            vals.append(str(row[c]).replace("|", "／"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def tokens_with_mark(tokens: str, target: str) -> str:
    parts = tokens.split()
    if target in parts:
        return "／".join(parts)
    return "／".join(parts)


def main() -> None:
    paired = pd.read_csv(OUT / "paired_predictions.csv", encoding="utf-8-sig")
    indep = pd.read_csv(OUT / "independent_comparison.csv", encoding="utf-8-sig")
    sample = sample_stratified(paired, 10)
    sample.to_csv(OUT / "segmentation_sample.csv", index=False, encoding="utf-8-sig")

    imp = paired[paired["improvement"] == "jieba_wrong_jiayan_right"].copy()
    reg = paired[paired["improvement"] == "jieba_right_jiayan_wrong"].copy()
    imp["shift"] = imp["jiayan_prob_east"] - imp["jieba_prob_east"]
    reg["shift"] = reg["jiayan_prob_east"] - reg["jieba_prob_east"]
    imp = imp.sort_values("shift", ascending=False).head(5)
    reg = reg.sort_values("shift", ascending=True).head(5)
    imp["case"] = "改善（按結果選出）"
    reg["case"] = "退步（按結果選出）"
    cases = pd.concat([imp, reg], ignore_index=True)
    cases.to_csv(OUT / "segmentation_cases.csv", index=False, encoding="utf-8-sig")

    # Term-level audit.  Prefer test sentences; fall back to the full main set
    # and then the Chaoyi holdout for terms absent from the test split.
    cc = opencc.OpenCC("t2s")
    dataset = pd.read_csv(ROOT / "data" / "v3" / "dataset_v3.csv", encoding="utf-8-sig")
    all_sent = pd.read_csv(ROOT / "data" / "v3" / "sentences_all.csv", encoding="utf-8-sig")
    jt = pd.read_csv(OUT / "jieba" / "tokens_main.csv", encoding="utf-8-sig")[["sent_id", "tokens"]].rename(columns={"tokens": "jieba_tokens"})
    qt = pd.read_csv(OUT / "jiayan" / "tokens_main.csv", encoding="utf-8-sig")[["sent_id", "tokens"]].rename(columns={"tokens": "jiayan_tokens"})
    full = dataset.merge(jt, on="sent_id").merge(qt, on="sent_id")
    full["period_true"] = full["period"]
    e01 = all_sent[all_sent["work_id"] == "E01"].merge(
        pd.read_csv(OUT / "jieba" / "tokens_chaoyi.csv", encoding="utf-8-sig")[["sent_id", "tokens"]].rename(columns={"tokens": "jieba_tokens"}),
        on="sent_id").merge(
        pd.read_csv(OUT / "jiayan" / "tokens_chaoyi.csv", encoding="utf-8-sig")[["sent_id", "tokens"]].rename(columns={"tokens": "jiayan_tokens"}),
        on="sent_id")
    e01["period_true"] = e01["period"]
    terms = [
        ("鴻儒", "鸿儒"), ("文人", "文人"), ("文辭", "文辞"),
        ("詩賦", "诗赋"), ("孔子", "孔子"), ("屈原", "屈原"),
        ("春秋", "春秋"), ("而", "而"),
    ]
    term_rows = []
    for trad, simp in terms:
        for scope, pool in (("test", paired), ("main", full), ("chaoyi", e01)):
            candidates = pool[
                pool["text_normalized"].astype(str).str.contains(trad, regex=False)
                | pool["text_normalized"].astype(str).map(lambda x: simp in cc.convert(str(x)))
            ]
            if candidates.empty:
                continue
            row = None
            for _, candidate in candidates.iterrows():
                jp = candidate["jieba_tokens"].split()
                qp = candidate["jiayan_tokens"].split()
                if (trad in jp) or (simp in qp):
                    row = candidate
                    if (trad in jp) and (simp in qp):
                        break
            if row is None:
                row = candidates.iloc[0]
            jieba_parts = row["jieba_tokens"].split()
            jiayan_parts = row["jiayan_tokens"].split()
            term_rows.append({
                "term_traditional": trad,
                "term_simplified": simp,
                "source_scope": scope,
                "sent_id": row["sent_id"],
                "author": row["author"],
                "title": row["work_title"],
                "period": row["period_true"],
                "jieba_as_word": trad in jieba_parts,
                "jiayan_as_word": simp in jiayan_parts,
                "jieba_tokens": "／".join(jieba_parts),
                "jiayan_tokens": "／".join(jiayan_parts),
            })
            break
    terms_df = pd.DataFrame(term_rows)
    terms_df.to_csv(OUT / "term_examples.csv", index=False, encoding="utf-8-sig")

    # Chaoyi transitions.
    jc = indep["period_pred_jieba"].tolist()
    qc = indep["period_pred_jiayan"].tolist()
    chao_counts = {
        "jieba_east": int(sum(x == "東漢" for x in jc)),
        "jiayan_east": int(sum(x == "東漢" for x in qc)),
        "both_east": int(sum(a == "東漢" and b == "東漢" for a, b in zip(jc, qc))),
        "jieba_west_jiayan_east": int(sum(a == "西漢" and b == "東漢" for a, b in zip(jc, qc))),
        "jieba_east_jiayan_west": int(sum(a == "東漢" and b == "西漢" for a, b in zip(jc, qc))),
        "both_west": int(sum(a == "西漢" and b == "西漢" for a, b in zip(jc, qc))),
    }

    sample_cols = ["sent_id", "period_true", "author", "work_title",
                   "jieba_pred", "jieba_prob_east", "jiayan_pred", "jiayan_prob_east",
                   "text_original", "jieba_tokens", "jiayan_tokens"]
    sample_west = sample[sample["period_true"] == "西漢"]
    sample_east = sample[sample["period_true"] == "東漢"]
    case_cols = ["case", "sent_id", "period_true", "author", "work_title",
                 "jieba_pred", "jieba_prob_east", "jiayan_pred", "jiayan_prob_east",
                 "text_original", "jieba_tokens", "jiayan_tokens"]
    term_cols = ["term_traditional", "term_simplified", "source_scope", "sent_id", "author", "title",
                 "jieba_as_word", "jiayan_as_word", "jieba_tokens", "jiayan_tokens"]

    lines = [
        "# 切詞抽查與改善／退步例證",
        "",
        "本文件是輔助核讀，不是分詞準確率評測。Jieba 組使用既有 35 個文論補充詞目；Jiayan 組使用官方 `WordNgramTokenizer` 的內建詞典，沒有另行加入自訂詞目，且依官方說明先以 OpenCC `t2s` 轉為簡體。兩組的詞表與切分顆粒度因此不同。",
        "",
        "## 一、固定隨機抽查",
        "",
        f"固定種子 `{SEED}`；按文獻分期分層，從 233 句測試集抽 20 句（西漢 10、東漢 10），兼顧不同作者。此抽樣與哪一組預測較好無關。完整欄位見 `segmentation_sample.csv`。",
        "",
        "### 西漢",
        "",
        md_table(sample_west, sample_cols, ["sent_id", "分期", "作者", "篇名", "Jieba預測", "P(東漢)", "Jiayan預測", "P(東漢)", "原文", "Jieba tokens", "Jiayan tokens"]),
        "",
        "### 東漢",
        "",
        md_table(sample_east, sample_cols, ["sent_id", "分期", "作者", "篇名", "Jieba預測", "P(東漢)", "Jiayan預測", "P(東漢)", "原文", "Jieba tokens", "Jiayan tokens"]),
        "",
        "## 二、改善與退步例證",
        "",
        "以下按測試結果選出，**不是隨機樣本，也不能當成整體分詞品質估計**。改善取「Jieba 錯、Jiayan 對」中東漢分數上升最多者；退步取「Jieba 對、Jiayan 錯」中東漢分數下降最多者，各至多 5 句。",
        "",
        md_table(cases, case_cols, ["類別", "sent_id", "分期", "作者", "篇名", "Jieba預測", "P(東漢)", "Jiayan預測", "P(東漢)", "原文", "Jieba tokens", "Jiayan tokens"]),
        "",
        "## 三、人名、書名、文論詞與虛詞",
        "",
        "下表優先從測試集找含目標詞的句子，測試集沒有時改用主樣本或〈超奇〉；這只是切分對照，不是詞語層級準確率。`jieba_as_word`／`jiayan_as_word` 只表示該詞在該句是否恰好成為單一 token。完整見 `term_examples.csv`。",
        "",
        md_table(terms_df, term_cols, ["繁體詞", "簡體詞", "來源", "sent_id", "作者", "篇名", "Jieba單詞", "Jiayan單詞", "Jieba tokens", "Jiayan tokens"]),
        "",
        "觀察重點：",
        "",
        "- Jiayan 的 `WordNgramTokenizer` 常把句子切成較細的單位，甚至以單字為主；它能保留部分雙字詞（如「民間」「利害」），但也會把一些人名、書名或文論複合詞拆開。",
        "- Jieba 組因加入了「鴻儒」「文人」「文辭」「詩賦」「屈原」等 35 個文論詞目，對這些詞的整體切分通常較穩定；Jiayan 組沒有相同的自訂詞目，不能把差異全歸因於算法。",
        "- Jiayan 組的 token 數較多（主樣本 27,313 vs Jieba 19,531；平均 23.48 vs 16.79），加上簡體轉換，令測試集零有效特徵句由 7 降至 1、僅一項由 20 降至 0；這可能提高覆蓋，但不保證切詞更符合古漢語詞法。",
        "- 少數例句的改善可能來自單字化後保留更多上下文詞項，也可能來自簡體／異體合併；本輪不足以分離兩者。",
        "",
        "## 四、〈超奇〉附帶檢驗",
        "",
        f"Jieba 判東漢 {chao_counts['jieba_east']}／129；Jiayan 判東漢 {chao_counts['jiayan_east']}／129。轉換：兩者皆東漢 {chao_counts['both_east']}、Jieba 西漢→Jiayan 東漢 {chao_counts['jieba_west_jiayan_east']}、Jieba 東漢→Jiayan 西漢 {chao_counts['jieba_east_jiayan_west']}、兩者皆西漢 {chao_counts['both_west']}。",
        "",
        "〈超奇〉是同作者留出篇章（訓練已含王充其他篇章），不是跨作者盲測；原本也已分析過，不能當成全新驗證。",
        "",
        "## 五、限制",
        "",
        "- 官方建議的 `CharHMMTokenizer` 需 KenLM；本環境沒有可用的 C/C++ 編譯器，KenLM 建置失敗，故本輪只能用官方 `WordNgramTokenizer`。這不是 Jiayan 的最佳分詞設定。",
        "- Jiayan 官方說明模型以簡體訓練；本輪以 OpenCC `t2s` 轉換輸入，Jieba 組保留原本繁體輸入。此差異已用「Jieba＋OpenCC」探索對照檢查，未見只靠轉換即可解釋全部變化。",
        "- Jieba 組有 35 個補充詞目；Jiayan 組未使用自訂詞目。兩者不是純粹算法 A/B。",
        "- 以上切詞判讀由 AI 輔助整理，未經使用者逐句人工確認；少量例句不代表整體分詞準確率。",
    ]
    (OUT / "segmentation_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print({"sample": len(sample), "improvements": len(imp), "regressions": len(reg), "terms": len(terms_df), "chaoyi": chao_counts})


if __name__ == "__main__":
    main()
