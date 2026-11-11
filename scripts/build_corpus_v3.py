# -*- coding: utf-8 -*-
"""Build v3 corpora: label-fix-only and label-fix + new authors.

v2 outputs are left untouched. v3 outputs go to data/v3/ and output/v3/.
"""

import json
from pathlib import Path

import pandas as pd

import build_corpus as bc
from corpus_manifest_v3 import WORKS_V3, STATUS_LABELS_V3

ROOT = Path(__file__).resolve().parent.parent
V3 = ROOT / "data" / "v3"
OUT = ROOT / "output" / "v3"
V3.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)


def build_all_sentences_v3():
    works = [w for w in WORKS_V3 if w["status"] in
             {"included", "included_secondary", "reserved", "uncertain",
              "uncertain_attribution"}]
    works.sort(key=lambda w: (0 if w["status"] == "reserved" else 1, w["work_id"]))
    rows = []
    for work in works:
        try:
            cleaned, sents = bc.extract_work_sentences(work)
        except Exception as exc:
            print("EXTRACT ERROR", work["work_id"], work["work_title"], repr(exc))
            continue
        for i, s in enumerate(sents, 1):
            reason = bc.is_bad_sentence(s)
            rows.append({
                "sent_id": f"{work['work_id']}-{i:03d}",
                "work_id": work["work_id"],
                "work_title": work["work_title"],
                "author": work["author"],
                "period": work["period"],
                "genre": work["genre"],
                "genre_group": work["genre_group"],
                "carrier": work["carrier"],
                "cao_section": work["cao_section"],
                "cao_pages": work["cao_pages"],
                "cao_status": work["cao_status"],
                "quanwen_check": work["quanwen_check"],
                "base_id": work["base_id"],
                "base_page": work["base_page"],
                "base_revision": work["base_revision"],
                "base_url": work["base_url"],
                "dating_basis": work["dating_basis"],
                "status": work["status"],
                "version_added": work["version_added"],
                "sent_order": i,
                "text_original": s,
                "text_normalized": bc.normalize_text(s),
                "char_len": bc.cjk_len(s),
                "include_full": reason is None,
                "exclusion_reason": reason or "",
                "duplicate_of": "",
                "duplicate_similarity": float("nan"),
                "trainable": work["status"] in {"included", "included_secondary"} and reason is None,
            })
        print(f"{work['work_id']} {work['work_title']}: {len(sents)} sentences")
    df = pd.DataFrame(rows)
    df["duplicate_similarity"] = pd.to_numeric(df["duplicate_similarity"], errors="coerce")
    return df


def main():
    df = build_all_sentences_v3()
    df = bc.mark_duplicates(df)

    sources = pd.DataFrame(WORKS_V3)
    sources["status_label"] = sources["status"].map(STATUS_LABELS_V3).fillna(sources["status"])

    def fmt_rev(value):
        if pd.isna(value) or str(value).strip() == "":
            return ""
        try:
            return str(int(float(value)))
        except Exception:
            return str(value)

    sources["base_revision"] = sources["base_revision"].apply(fmt_rev)
    sources.to_csv(V3 / "sources.csv", index=False, encoding="utf-8-sig")
    df.to_csv(V3 / "sentences_all.csv", index=False, encoding="utf-8-sig")

    excluded = df[~df["include_full"]].copy()
    excluded.to_csv(V3 / "excluded.csv", index=False, encoding="utf-8-sig")
    uncertain = df[df["status"] == "uncertain"].copy()
    uncertain.to_csv(V3 / "uncertain.csv", index=False, encoding="utf-8-sig")
    uncertain_attr = df[df["status"] == "uncertain_attribution"].copy()
    uncertain_attr.to_csv(V3 / "uncertain_attribution.csv", index=False, encoding="utf-8-sig")
    pending = sources[sources["status"] == "pending"].copy()
    pending.to_csv(V3 / "pending.csv", index=False, encoding="utf-8-sig")

    # label-fix log
    label_fix = []
    for wid in ["W17", "W18"]:
        sub = df[df["work_id"] == wid]
        meta = sources[sources["work_id"] == wid].iloc[0]
        label_fix.append({
            "work_id": wid,
            "work_title": meta["work_title"],
            "author_old": meta["author"],
            "period_old": "西漢（v2）",
            "period_v3": meta["period"],
            "status_v3": meta["status_label"],
            "sentences": len(sub),
            "reason": meta["notes"],
            "dating_basis": meta["dating_basis"],
            "base_page": meta["base_page"],
            "base_revision": meta["base_revision"],
            "base_url": meta["base_url"],
        })
    pd.DataFrame(label_fix).to_csv(V3 / "label_fix.csv", index=False, encoding="utf-8-sig")

    # samples
    labelonly = bc.sample_dataset(df, 2)
    v3 = bc.sample_dataset(df, 3)
    labelonly.to_csv(V3 / "dataset_labelonly.csv", index=False, encoding="utf-8-sig")
    v3.to_csv(V3 / "dataset_v3.csv", index=False, encoding="utf-8-sig")
    v3[v3["split"] == "train"].to_csv(V3 / "train.csv", index=False, encoding="utf-8-sig")
    v3[v3["split"] == "test"].to_csv(V3 / "test.csv", index=False, encoding="utf-8-sig")

    # new materials: full vs main sample
    new_ids = ["W24", "W25", "E37", "E38", "E39"]
    new_rows = []
    for wid in new_ids:
        meta = sources[sources["work_id"] == wid].iloc[0]
        full_n = int((df[(df["work_id"] == wid) & (df["include_full"])]).shape[0])
        main_n = int((v3[v3["work_id"] == wid]).shape[0])
        new_rows.append({
            "work_id": wid,
            "work_title": meta["work_title"],
            "author": meta["author"],
            "period": meta["period"],
            "genre": meta["genre"],
            "genre_group": meta["genre_group"],
            "cao_pages": meta["cao_pages"],
            "base_page": meta["base_page"],
            "base_revision": meta["base_revision"],
            "base_url": meta["base_url"],
            "extract_spec": meta["extract_spec"],
            "full_sentences": full_n,
            "main_sample_sentences": main_n,
            "dating_basis": meta["dating_basis"],
            "notes": meta["notes"],
        })
    new_df = pd.DataFrame(new_rows)
    new_df.to_csv(V3 / "new_materials.csv", index=False, encoding="utf-8-sig")

    # summaries
    labelonly_summary = bc.summary_for(df[df["version_added"] <= 2], "v3 label-fix only")
    v3_summary = bc.summary_for(df[df["version_added"] <= 3], "v3 label-fix + new authors")
    for summary, sample, name in [
        (labelonly_summary, labelonly, "corpus_summary_labelonly.json"),
        (v3_summary, v3, "corpus_summary_v3.json"),
    ]:
        summary["main_sample"] = {
            "total": int(len(sample)),
            "by_period": {k: int(v) for k, v in sample["period"].value_counts().items()},
            "by_split": {k: int(v) for k, v in sample["split"].value_counts().items()},
            "split_by_period": {
                period: {k: int(v) for k, v in group["split"].value_counts().items()}
                for period, group in sample.groupby("period")
            },
            "works": int(sample["work_id"].nunique()),
            "authors": int(sample["author"].nunique()),
            "max_work_share": round(sample["work_title"].value_counts().iloc[0] / len(sample), 4),
            "max_work": sample["work_title"].value_counts().index[0],
            "max_author_share": round(sample["author"].value_counts().iloc[0] / len(sample), 4),
            "max_author": sample["author"].value_counts().index[0],
        }
        (OUT / name).write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        print("\n===", name, "===")
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    # reserved overlap
    overlap = df[(df["duplicate_of"].astype(str).str.startswith("E01")) |
                 ((df["status"] == "reserved") & (~df["include_full"]))]
    overlap.to_csv(OUT / "reserved_overlap.csv", index=False, encoding="utf-8-sig")

    # readable new materials summary
    lines = [
        "# v3 新增材料",
        "",
        f"- 新增作者數：{new_df['author'].nunique()}（{'、'.join(new_df['author'].drop_duplicates())}）",
        f"- 新增篇目數：{len(new_df)}",
        f"- 全庫新增句數：{int(new_df['full_sentences'].sum())}",
        f"- 主樣本實際納入句數：{int(new_df['main_sample_sentences'].sum())}",
        "- 底本網址見 `data/v3/new_materials.csv` 的 `base_url` 欄；下表只列頁面與修訂號。",
        "",
        "| 篇名 | 作者 | 分期 | 文類 | 底本 | 修訂號 | 全庫句數 | 主樣本句數 |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for _, row in new_df.iterrows():
        lines.append(
            f"| {row['work_title']} | {row['author']} | {row['period']} | {row['genre']} | "
            f"{row['base_page']} | {row['base_revision']} | {row['full_sentences']} | "
            f"{row['main_sample_sentences']} |")
    lines += [
        "",
        "節選範圍與理由：",
        "",
    ]
    for _, row in new_df.iterrows():
        lines.append(f"- **{row['work_title']}**：`{row['extract_spec']}`；{row['notes']}")
    lines += [
        "",
        "## 標籤修正",
        "",
        "| 篇名 | 舊題作者 | v2 分期 | v3 狀態 | 句數 | 理由 |",
        "|---|---|---|---|---:|---|",
    ]
    for row in label_fix:
        lines.append(
            f"| {row['work_title']} | {row['author_old']} | {row['period_old']} | "
            f"{row['status_v3']} | {row['sentences']} | {row['reason']} |")
    (OUT / "new_materials_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nWrote v3 corpus files.")


if __name__ == "__main__":
    main()
