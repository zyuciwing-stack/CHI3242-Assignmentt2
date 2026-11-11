# -*- coding: utf-8 -*-
"""Build the sentence-level corpus from the manifest.

Outputs:
  data/sources.csv
  data/sentences_all.csv
  data/dataset_v1.csv, data/dataset_v2.csv
  data/train.csv, data/test.csv
  data/excluded.csv, data/uncertain.csv, data/pending.csv
  output/corpus_summary_v1.json, output/corpus_summary_v2.json
  output/reserved_overlap.csv
"""

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from corpus_manifest import WORKS, STATUS_LABELS

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
SEED = 42
MAX_PER_WORK = 80
MAX_PER_AUTHOR = 160
BALANCE_RATIO = 1.25

VARIANT_MAP = str.maketrans({
    "㠯": "以", "无": "無", "説": "說", "爲": "為", "敎": "教", "卽": "即",
    "旣": "既", "衆": "眾", "眞": "真", "冨": "富", "敍": "敘", "矦": "侯",
    "幷": "並", "竝": "並", "弃": "棄", "𢿱": "散", "羣": "群", "畱": "留",
    "衞": "衛", "閒": "間", "脩": "修", "覩": "睹", "迺": "乃", "靑": "青",
    "顚": "顛", "飜": "翻", "鬭": "鬥", "麤": "粗", "黙": "默", "隷": "隸",
    "寍": "寧", "𡩬": "寧", "槩": "概", "昬": "昏", "牀": "床", "疎": "疏",
    "皐": "皋", "筭": "算", "縂": "總", "聦": "聰", "舩": "船", "艸": "草",
    "虵": "蛇", "蝨": "虱", "譌": "訛", "賸": "剩", "趂": "趁", "隣": "鄰",
    "霑": "沾", "鞵": "鞋", "韈": "襪", "頫": "俯", "餧": "餵", "驩": "歡",
    "齅": "嗅", "㜸": "孽", "㦧": "慘", "懃": "勤", "慇": "殷", "柰": "奈",
    "寃": "冤", "寔": "實", "尢": "尤", "嵗": "歲", "彊": "強", "徧": "遍",
    "悞": "誤", "憇": "憩", "擧": "舉", "攷": "考", "斆": "學", "暦": "曆",
    "朞": "期", "棊": "棋", "榦": "幹", "欵": "款", "歛": "斂", "殀": "夭",
    "氷": "冰", "汙": "污", "湻": "淳", "溼": "濕", "煑": "煮", "犂": "犁",
    "猨": "猿", "玅": "妙", "甞": "嘗", "痺": "痹", "皷": "鼓", "盃": "杯",
    "睠": "眷", "祕": "秘", "稾": "稿", "窻": "窗", "竪": "豎", "箇": "個",
    "簷": "檐", "絃": "弦", "翺": "翱", "肎": "肯", "舘": "館", "茍": "苟",
    "蒐": "搜", "藴": "蘊", "衺": "邪", "袵": "衽", "覈": "核", "詘": "屈",
    "謌": "歌", "讐": "讎", "貍": "狸", "賔": "賓", "踰": "逾", "輙": "輒",
    "迯": "逃", "遯": "遁", "邨": "村", "醻": "酬", "釦": "扣", "閤": "閣",
    "陞": "升", "雋": "俊", "靣": "面", "飡": "餐", "餙": "飾", "駡": "罵",
    "骾": "鯁", "鴈": "雁", "鵰": "雕", "黴": "霉", "鼈": "鱉", "齗": "齦",
    "︰": "：",
})


def load_raw(base_id):
    path = RAW / f"{base_id}.txt"
    if not path.exists():
        path = ROOT / "data" / "_inspect" / f"{base_id}.txt"
    if not path.exists():
        raise FileNotFoundError(f"raw text not found: {base_id}")
    return path.read_text(encoding="utf-8")


def split_raw_paragraphs(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def extract_section(text, title):
    pattern = re.compile(
        rf"^(={{2,5}})\s*{re.escape(title)}\s*\1\s*$", re.M)
    match = pattern.search(text)
    if not match:
        raise ValueError(f"section not found: {title}")
    start = match.end()
    next_heading = re.search(r"^={2,5}\s*", text[start:], re.M)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def extract_non_shu_section(text, title, end_title=None):
    body = extract_section(text, title)
    kept = []
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("【疏】") or s.startswith("疏") or s.startswith("正義曰"):
            continue
        kept.append(s)
    return "\n".join(kept)


def clean_text(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.S)
    text = re.sub(r"<onlyinclude>|</onlyinclude>", "", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # editorial notes in 全漢文/全後漢文 and 史記/漢書 transcriptions
    for _ in range(4):
        new = re.sub(r"〈[^〈〉]*〉", "", text)
        if new == text:
            break
        text = new
    text = re.sub(r"〔[^〔〕]*〕", "", text)
    text = re.sub(r"（[^（）]*）", "", text)
    text = re.sub(r"【[^【】]*】", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    # drop headings and colophons
    lines = []
    for line in text.splitlines():
        s = line.replace("\u3000", " ").strip()
        if not s:
            continue
        if s.startswith("="):
            continue
        if "維基文庫" in s or "賜進士出身" in s:
            continue
        if re.search(r"《全(漢|後漢)文》卷.*終", s):
            continue
        lines.append(s)
    text = "\n".join(lines)
    text = re.sub(r"[ \t]+", "", text)
    return text.strip()


def split_sentences(text):
    pieces = re.findall(r"[^。！？]*[。！？]+[」』”’）】\]]*", text)
    tail = re.sub(r"^.*[。！？][」』”’）】\]]*", "", text, flags=re.S).strip()
    if tail:
        pieces.append(tail)
    sentences = []
    for p in pieces:
        s = re.sub(r"\s+", "", p).strip()
        if s:
            sentences.append(s)
    return sentences


def normalize_text(text):
    text = text.translate(VARIANT_MAP)
    return re.sub(r"[「」『』]", "", text)


def dedupe_key(text):
    key = re.sub(r"[^\u3400-\u9fffA-Za-z0-9]", "", normalize_text(text))
    return key


def cjk_len(text):
    return len(re.findall(r"[\u3400-\u9fff]", text))


def is_bad_sentence(s):
    if cjk_len(s) < 4:
        return "too_short"
    if s.startswith("【疏】") or s.startswith("疏正義"):
        return "editorial_note"
    if s.startswith("案︰") or s.startswith("案："):
        return "editorial_note"
    if "維基文庫" in s or "賜進士出身" in s:
        return "colophon"
    if re.search(r"《全(漢|後漢)文》卷.*終", s):
        return "colophon"
    if re.fullmatch(r"[。！？：；、，\s]+", s):
        return "punctuation_only"
    if re.fullmatch(r"第[一二三四五六七八九十百]+。", s):
        return "catalog_fragment"
    if re.fullmatch(r"作.{0,40}第[一二三四五六七八九十百]+。", s):
        return "catalog_fragment"
    return None


def extract_work_sentences(work):
    text = load_raw(work["base_id"]) if work["base_id"] else ""
    mode = work["extract_mode"]
    spec = work.get("extract_spec", {})
    if mode == "whole":
        body = text
    elif mode == "section":
        body = extract_section(text, spec["section"])
    elif mode == "sections":
        body = "\n".join(extract_section(text, t) for t in spec["sections"])
    elif mode == "paragraphs":
        paras = split_raw_paragraphs(text)
        body = "\n".join(paras[i] for i in spec["indices"] if i < len(paras))
    elif mode == "section_paragraphs":
        section_body = extract_section(text, spec["section"])
        paras = split_raw_paragraphs(section_body)
        body = "\n".join(paras[i] for i in spec["indices"] if i < len(paras))
    elif mode == "non_shu_section":
        body = extract_non_shu_section(text, spec["section"], spec.get("end_section"))
    else:
        raise ValueError(f"unknown extract mode: {mode}")
    cleaned = clean_text(body)
    sents = split_sentences(cleaned)
    return cleaned, sents


def build_all_sentences():
    works = [w for w in WORKS if w["status"] in
             {"included", "included_secondary", "reserved", "uncertain"}]
    # reserved first, so duplicates in training are measured against it
    works.sort(key=lambda w: (0 if w["status"] == "reserved" else 1, w["work_id"]))
    rows = []
    for work in works:
        try:
            cleaned, sents = extract_work_sentences(work)
        except Exception as exc:
            print("EXTRACT ERROR", work["work_id"], work["work_title"], repr(exc))
            continue
        for i, s in enumerate(sents, 1):
            reason = is_bad_sentence(s)
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
                "text_normalized": normalize_text(s),
                "char_len": cjk_len(s),
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


def mark_duplicates(df):
    exact = {}
    near_groups = defaultdict(list)
    for idx, row in df.iterrows():
        if not row["include_full"]:
            continue
        key = dedupe_key(row["text_original"])
        if not key:
            continue
        if key in exact:
            df.at[idx, "include_full"] = False
            df.at[idx, "trainable"] = False
            df.at[idx, "exclusion_reason"] = (
                "duplicate_reserved" if df.at[exact[key], "status"] == "reserved"
                else "duplicate")
            df.at[idx, "duplicate_of"] = df.at[exact[key], "sent_id"]
            df.at[idx, "duplicate_similarity"] = 1.0
            continue
        exact[key] = idx
        # near-duplicate check within a length bucket
        bucket = len(key) // 12
        duplicate_of = None
        best = 0.0
        for b in (bucket - 1, bucket, bucket + 1):
            for other_idx in near_groups.get(b, []):
                other_key = dedupe_key(df.at[other_idx, "text_original"])
                if abs(len(other_key) - len(key)) > max(10, len(key) * 0.35):
                    continue
                ratio = SequenceMatcher(None, key, other_key).ratio()
                if ratio > best:
                    best = ratio
                    duplicate_of = other_idx
        if duplicate_of is not None and best >= 0.90:
            df.at[idx, "include_full"] = False
            df.at[idx, "trainable"] = False
            df.at[idx, "exclusion_reason"] = (
                "duplicate_reserved" if df.at[duplicate_of, "status"] == "reserved"
                else "duplicate_near")
            df.at[idx, "duplicate_of"] = df.at[duplicate_of, "sent_id"]
            df.at[idx, "duplicate_similarity"] = round(best, 4)
            continue
        near_groups[bucket].append(idx)
    return df


def sample_dataset(df, version):
    base = df[(df["trainable"]) & (df["version_added"] <= version)].copy()
    if base.empty:
        return base
    rng = 42
    parts = []
    for work_id, group in base.groupby("work_id", sort=False):
        if len(group) > MAX_PER_WORK:
            group = group.sample(MAX_PER_WORK, random_state=rng)
        parts.append(group)
    capped = pd.concat(parts, ignore_index=True)
    parts = []
    for author, group in capped.groupby("author", sort=False):
        if len(group) > MAX_PER_AUTHOR:
            group = group.sample(MAX_PER_AUTHOR, random_state=rng)
        parts.append(group)
    capped = pd.concat(parts, ignore_index=True)
    counts = capped["period"].value_counts()
    if len(counts) == 2 and counts.max() / counts.min() > BALANCE_RATIO:
        target = counts.min()
        parts = []
        for period, group in capped.groupby("period", sort=False):
            if len(group) > target:
                group = group.sample(target, random_state=rng)
            parts.append(group)
        capped = pd.concat(parts, ignore_index=True)
    capped = capped.sample(frac=1.0, random_state=rng).reset_index(drop=True)
    if capped["period"].nunique() == 2 and capped["period"].value_counts().min() >= 2:
        train_idx, test_idx = train_test_split(
            capped.index, test_size=0.2, random_state=SEED,
            stratify=capped["period"])
    else:
        train_idx, test_idx = train_test_split(
            capped.index, test_size=0.2, random_state=SEED)
    capped["split"] = "train"
    capped.loc[test_idx, "split"] = "test"
    return capped


def summary_for(df, label):
    included = df[(df["trainable"]) & (df["include_full"])]
    out = {"label": label, "total": int(len(included))}
    out["by_period"] = {
        period: {
            "sentences": int(len(group)),
            "works": int(group["work_id"].nunique()),
            "authors": int(group["author"].nunique()),
            "genres": {k: int(v) for k, v in group["genre_group"].value_counts().items()},
            "max_work_share": round(group["work_title"].value_counts().iloc[0] / len(group), 4) if len(group) else 0,
            "max_work": group["work_title"].value_counts().index[0] if len(group) else "",
            "max_author_share": round(group["author"].value_counts().iloc[0] / len(group), 4) if len(group) else 0,
            "max_author": group["author"].value_counts().index[0] if len(group) else "",
            "top_works": {k: int(v) for k, v in group["work_title"].value_counts().head(8).items()},
        }
        for period, group in included.groupby("period")
    }
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-dedupe", action="store_true")
    args = parser.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    df = build_all_sentences()
    if not args.skip_dedupe:
        df = mark_duplicates(df)

    # source table
    sources = pd.DataFrame(WORKS)
    sources["status_label"] = sources["status"].map(STATUS_LABELS).fillna(sources["status"])

    def fmt_rev(value):
        if pd.isna(value) or str(value).strip() == "":
            return ""
        try:
            return str(int(float(value)))
        except Exception:
            return str(value)

    sources["base_revision"] = sources["base_revision"].apply(fmt_rev)
    sources.to_csv(DATA / "sources.csv", index=False, encoding="utf-8-sig")
    df.to_csv(DATA / "sentences_all.csv", index=False, encoding="utf-8-sig")

    excluded = df[~df["include_full"]].copy()
    excluded.to_csv(DATA / "excluded.csv", index=False, encoding="utf-8-sig")
    uncertain = df[df["status"] == "uncertain"].copy()
    uncertain.to_csv(DATA / "uncertain.csv", index=False, encoding="utf-8-sig")
    pending = sources[sources["status"] == "pending"].copy()
    pending.to_csv(DATA / "pending.csv", index=False, encoding="utf-8-sig")

    summaries = {}
    for version in (1, 2):
        sampled = sample_dataset(df, version)
        sampled.to_csv(DATA / f"dataset_v{version}.csv", index=False, encoding="utf-8-sig")
        summary = summary_for(df[df["version_added"] <= version], f"v{version} full corpus")
        summary["main_sample"] = {
            "total": int(len(sampled)),
            "by_period": {k: int(v) for k, v in sampled["period"].value_counts().items()},
            "by_split": {k: int(v) for k, v in sampled["split"].value_counts().items()},
            "split_by_period": {
                period: {k: int(v) for k, v in group["split"].value_counts().items()}
                for period, group in sampled.groupby("period")
            },
            "works": int(sampled["work_id"].nunique()),
            "authors": int(sampled["author"].nunique()),
            "max_work_share": round(sampled["work_title"].value_counts().iloc[0] / len(sampled), 4),
            "max_work": sampled["work_title"].value_counts().index[0],
            "max_author_share": round(sampled["author"].value_counts().iloc[0] / len(sampled), 4),
            "max_author": sampled["author"].value_counts().index[0],
        }
        summaries[f"v{version}"] = summary
        print(f"\n=== v{version} ===")
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    # final v2 train/test
    v2 = pd.read_csv(DATA / "dataset_v2.csv", encoding="utf-8-sig")
    v2[v2["split"] == "train"].to_csv(DATA / "train.csv", index=False, encoding="utf-8-sig")
    v2[v2["split"] == "test"].to_csv(DATA / "test.csv", index=False, encoding="utf-8-sig")

    # reserved overlap
    reserved = df[(df["status"] == "reserved") & (df["include_full"])]
    overlap = df[(df["duplicate_of"].astype(str).str.startswith("E01")) |
                 ((df["status"] == "reserved") & (~df["include_full"]))]
    overlap.to_csv(OUTPUT / "reserved_overlap.csv", index=False, encoding="utf-8-sig")

    with open(OUTPUT / "corpus_summary_v1.json", "w", encoding="utf-8") as f:
        json.dump(summaries["v1"], f, ensure_ascii=False, indent=2)
    with open(OUTPUT / "corpus_summary_v2.json", "w", encoding="utf-8") as f:
        json.dump(summaries["v2"], f, ensure_ascii=False, indent=2)

    # markdown summary
    lines = ["# 語料摘要", "", "完整表格與文類分布見 `sufficiency_check.md`。", ""]
    for version in (1, 2):
        s = summaries[f"v{version}"]
        lines.append(f"## v{version}")
        lines.append("")
        for period, info in s["by_period"].items():
            lines.append(f"- {period}：{info['sentences']} 句／{info['works']} 篇／"
                         f"{info['authors']} 作者；最大篇目 {info['max_work']} "
                         f"({info['max_work_share']:.1%})；最大作者 {info['max_author']} "
                         f"({info['max_author_share']:.1%})")
        ms = s["main_sample"]
        lines.append(f"- 主訓練樣本：{ms['total']} 句；"
                     f"西漢 {ms['by_period'].get('西漢', 0)}／東漢 {ms['by_period'].get('東漢', 0)}；"
                     f"訓練 {ms['by_split'].get('train', 0)}／測試 {ms['by_split'].get('test', 0)}；"
                     f"最大篇目 {ms['max_work']} ({ms['max_work_share']:.1%})；"
                     f"最大作者 {ms['max_author']} ({ms['max_author_share']:.1%})")
        lines.append("")
    (OUTPUT / "corpus_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nWrote corpus files and summaries.")


if __name__ == "__main__":
    main()
