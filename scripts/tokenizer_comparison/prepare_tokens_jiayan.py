# -*- coding: utf-8 -*-
"""Run the official Jiayan WordNgramTokenizer on the fixed sentences.

Jiayan's README says its models are trained on simplified Chinese.  This script
therefore converts the already-normalized text with OpenCC ``t2s`` for the
Jiayan arm only; the original Jieba baseline keeps the original text.

The official recommended CharHMMTokenizer requires KenLM.  KenLM cannot be
built in the current Windows environment (no C/C++ compiler and the NMake CMake
generator fails), so this comparison uses Jiayan's official
WordNgramTokenizer, which does not require the KenLM model.  This limitation is
recorded in the metadata and engineering record.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

import opencc
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "v3"
OUT = ROOT / "output" / "tokenizer_comparison" / "jiayan"
STUB = ROOT / "output" / "tokenizer_comparison" / "vendor_stub"
sys.path.insert(0, str(STUB))

from jiayan import WordNgramTokenizer  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cc = opencc.OpenCC("t2s")
    tokenizer = WordNgramTokenizer()
    dataset = pd.read_csv(DATA / "dataset_v3.csv", encoding="utf-8-sig")
    all_sentences = pd.read_csv(DATA / "sentences_all.csv", encoding="utf-8-sig")

    main_rows = []
    for row in dataset.itertuples(index=False):
        converted = cc.convert(str(row.text_normalized))
        tokens = list(tokenizer.tokenize(converted))
        main_rows.append({
            "sent_id": row.sent_id,
            "split": row.split,
            "period": row.period,
            "text_simplified": converted,
            "tokens": " ".join(tokens),
            "token_count": len(tokens),
        })
    chaoyi = all_sentences[all_sentences["work_id"] == "E01"].copy()
    chaoyi_rows = []
    for row in chaoyi.itertuples(index=False):
        converted = cc.convert(str(row.text_normalized))
        tokens = list(tokenizer.tokenize(converted))
        chaoyi_rows.append({
            "sent_id": row.sent_id,
            "period": row.period,
            "text_simplified": converted,
            "tokens": " ".join(tokens),
            "token_count": len(tokens),
        })
    pd.DataFrame(main_rows).to_csv(OUT / "tokens_main.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(chaoyi_rows).to_csv(OUT / "tokens_chaoyi.csv", index=False, encoding="utf-8-sig")

    dict_path = Path(__import__("jiayan").__file__).resolve().parent / "data" / "dict.txt"
    meta = {
        "tokenizer": "WordNgramTokenizer",
        "tokenizer_class": "jiayan.WordNgramTokenizer",
        "jiayan_version": importlib.metadata.version("jiayan"),
        "opencc": "opencc.OpenCC('t2s')",
        "opencc_package_version": importlib.metadata.version("opencc-python-reimplemented"),
        "char_hmm_kenlm_available": False,
        "kenlm_blocker": "KenLM build failed on Windows (no C/C++ compiler; NMake generator platform error); official jiayan.klm model not loaded.",
        "main_tokenizer_model": None,
        "dict_path": str(dict_path),
        "dict_sha256": sha(dict_path),
        "n_main": len(main_rows),
        "n_chaoyi": len(chaoyi_rows),
        "input_main_sha256": sha(DATA / "dataset_v3.csv"),
        "input_sentences_sha256": sha(DATA / "sentences_all.csv"),
        "tokens_main_sha256": sha(OUT / "tokens_main.csv"),
        "tokens_chaoyi_sha256": sha(OUT / "tokens_chaoyi.csv"),
    }
    (OUT / "tokenization_metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
