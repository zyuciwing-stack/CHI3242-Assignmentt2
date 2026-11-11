# -*- coding: utf-8 -*-
"""Exploratory control: Jieba on OpenCC-simplified text."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jieba
import opencc
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "v3"
OUT = ROOT / "output" / "tokenizer_comparison" / "exploratory_jieba_simplified"

USER_WORDS = [
    "文章", "著述", "鴻儒", "文人", "經傳", "詩賦", "辭賦", "離騷", "屈原",
    "雅頌", "風雅", "雕蟲", "篆刻", "諷諫", "作者", "篇章", "文辭", "筆墨",
    "論說", "傳書", "經藝", "鴻筆", "文采", "華藻", "模範", "儀表", "賦頌",
    "歌詩", "樂府", "石渠", "金馬", "史記", "漢書", "藝文志", "七略",
]
for word in USER_WORDS:
    jieba.add_word(word)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cc = opencc.OpenCC("t2s")
    dataset = pd.read_csv(DATA / "dataset_v3.csv", encoding="utf-8-sig")
    all_sentences = pd.read_csv(DATA / "sentences_all.csv", encoding="utf-8-sig")
    rows = []
    for row in dataset.itertuples(index=False):
        converted = cc.convert(str(row.text_normalized))
        tokens = jieba.lcut(converted)
        rows.append({"sent_id": row.sent_id, "split": row.split, "period": row.period,
                     "text_simplified": converted, "tokens": " ".join(tokens),
                     "token_count": len(tokens)})
    chao = all_sentences[all_sentences["work_id"] == "E01"].copy()
    chaoyi_rows = []
    for row in chao.itertuples(index=False):
        converted = cc.convert(str(row.text_normalized))
        tokens = jieba.lcut(converted)
        chaoyi_rows.append({"sent_id": row.sent_id, "period": row.period,
                            "text_simplified": converted, "tokens": " ".join(tokens),
                            "token_count": len(tokens)})
    pd.DataFrame(rows).to_csv(OUT / "tokens_main.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(chaoyi_rows).to_csv(OUT / "tokens_chaoyi.csv", index=False, encoding="utf-8-sig")
    meta = {
        "tokenizer": "jieba",
        "version": getattr(jieba, "__version__", "unknown"),
        "opencc": "opencc.OpenCC('t2s')",
        "note": "exploratory control: Jieba on the same simplified text used by Jiayan",
        "n_main": len(rows), "n_chaoyi": len(chaoyi_rows),
        "tokens_main_sha256": sha(OUT / "tokens_main.csv"),
        "tokens_chaoyi_sha256": sha(OUT / "tokens_chaoyi.csv"),
    }
    (OUT / "tokenization_metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
