# -*- coding: utf-8 -*-
"""Summarise test errors by work, author, and genre."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"


def summarise(pred_path, label):
    df = pd.read_csv(pred_path, encoding="utf-8-sig")
    df["error"] = ~df["correct"]
    rows = []
    for group_col in ["work_title", "author", "genre_group", "genre"]:
        g = (df.groupby(group_col)
               .agg(n=("error", "size"), errors=("error", "sum"),
                    accuracy=("correct", "mean"))
               .reset_index()
               .rename(columns={group_col: "group"}))
        g["group_type"] = group_col
        g["run"] = label
        g["error_rate"] = 1 - g["accuracy"]
        rows.append(g)
    out = pd.concat(rows, ignore_index=True)
    out = out[["run", "group_type", "group", "n", "errors", "error_rate", "accuracy"]]
    return out, df


v2, v2df = summarise(OUTPUT / "v2" / "test_predictions.csv", "v2_main")
grp, grpdf = summarise(OUTPUT / "grouped" / "test_predictions.csv", "v2_grouped")
all_errors = pd.concat([v2, grp], ignore_index=True)
all_errors.to_csv(OUTPUT / "error_analysis.csv", index=False, encoding="utf-8-sig")

lines = ["# Error analysis", ""]
for label, df in [("v2_main", v2df), ("v2_grouped", grpdf)]:
    lines.append(f"## {label}")
    lines.append("")
    lines.append(f"- Test sentences: {len(df)}")
    lines.append(f"- Accuracy: {df['correct'].mean():.4f}")
    lines.append("")
    lines.append("### By genre group")
    lines.append("")
    lines.append("| genre | n | errors | error rate |")
    lines.append("|---|---:|---:|---:|")
    g = (df.groupby("genre_group")
           .agg(n=("correct", "size"), errors=("correct", lambda s: int((~s).sum())))
           .sort_values("n", ascending=False))
    for idx, row in g.iterrows():
        lines.append(f"| {idx} | {row['n']} | {row['errors']} | {row['errors']/row['n']:.1%} |")
    lines.append("")
    lines.append("### Works with most errors")
    lines.append("")
    lines.append("| work | n | errors | error rate |")
    lines.append("|---|---:|---:|---:|")
    w = (df.groupby(["work_title", "author"])
           .agg(n=("correct", "size"), errors=("correct", lambda s: int((~s).sum())))
           .reset_index())
    w["error_rate"] = w["errors"] / w["n"]
    w = w[w["n"] >= 5].sort_values(["error_rate", "errors"], ascending=False).head(12)
    for _, row in w.iterrows():
        lines.append(f"| {row['work_title']}（{row['author']}） | {row['n']} | "
                     f"{row['errors']} | {row['error_rate']:.1%} |")
    lines.append("")

(OUTPUT / "error_analysis.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
