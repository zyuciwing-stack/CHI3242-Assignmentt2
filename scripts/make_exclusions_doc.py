# -*- coding: utf-8 -*-
"""Write data/exclusions.md: excluded notes, duplicates, and catalog fragments."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

df = pd.read_csv(DATA / "excluded.csv", encoding="utf-8-sig")
df["exclusion_reason"] = df["exclusion_reason"].fillna("")

lines = [
    "# 排除紀錄",
    "",
    "本檔記錄切句後的排除項；底本中的編輯附註在切句前已刪除，不進入句子表。",
    "",
    "## 1. 編輯附註與版本說明",
    "",
    "- 《全漢文》《全後漢文》底本中的〈…〉來源小註、〔…〕與（…）異文、",
    "  《楚辭章句》的【…】標記，均為底本註記或異文，不是古文正文；切句前刪除，不計入句數。",
    "- 同一篇同時見於曹本與《全漢文》／《全後漢文》時，只取一個實際底本（見 `sources.csv`），",
    "  另一版本只作核查，不重複計句。",
    "- 維基文庫頁面與《全漢文》／《全後漢文》轉錄如有重複版本，以卷次本為實際底本；",
    "  網址與修訂號見 `sources.csv`。",
    "",
    "## 2. 排除原因統計",
    "",
    "| 原因 | 句數 |",
    "|---|---:|",
]
counts = df["exclusion_reason"].value_counts()
for reason, count in counts.items():
    lines.append(f"| {reason or '(空白)'} | {count} |")
lines += [
    "",
    "## 3. 重複引文／重複版本",
    "",
    "| sent_id | 篇名 | 原句 | 重複於 | 相似度 | 原因 |",
    "|---|---|---|---|---:|---|",
]
dup = df[df["exclusion_reason"].str.startswith("duplicate")]
for _, row in dup.iterrows():
    text = str(row["text_original"]).replace("|", "｜")
    lines.append(
        f"| {row['sent_id']} | {row['work_title']} | {text} | {row['duplicate_of']} | "
        f"{row['duplicate_similarity']} | {row['exclusion_reason']} |")
lines += [
    "",
    "## 4. 目錄片段與過短句",
    "",
    "| sent_id | 篇名 | 原句 | 原因 |",
    "|---|---|---|---|",
]
short = df[df["exclusion_reason"].isin(["catalog_fragment", "too_short"])]
for _, row in short.head(80).iterrows():
    text = str(row["text_original"]).replace("|", "｜")
    lines.append(f"| {row['sent_id']} | {row['work_title']} | {text} | {row['exclusion_reason']} |")
lines += [
    "",
    "> 過短句 40 句、目錄片段 2 句，共 42 句；此表全部列出，完整欄位見 `excluded.csv`。",
    "",
]
(DATA / "exclusions.md").write_text("\n".join(lines), encoding="utf-8")
print("wrote data/exclusions.md")
