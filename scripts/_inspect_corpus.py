import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data" / "sentences_all.csv", encoding="utf-8-sig")

print("rows", len(df))
print("\nExclusion reasons:")
print(df["exclusion_reason"].fillna("(none)").value_counts().to_string())

print("\nLeftover markers:")
for pat in ["【", "】", "〈", "〉", "==", "疏", "案︰", "維基", "賜進士", "（", "）", "〔", "〕"]:
    n = df["text_original"].astype(str).str.contains(pat, regex=False).sum()
    print(f"  {pat}: {n}")

print("\nSamples by work (first 3, last 2):")
for wid, group in df.groupby("work_id", sort=False):
    texts = group["text_original"].tolist()
    print(f"\n### {wid} {group['work_title'].iloc[0]} ({len(texts)})")
    for t in texts[:3]:
        print("  +", t[:160])
    if len(texts) > 5:
        print("  ...")
    for t in texts[-2:]:
        print("  -", t[:160])
