import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "v3" / "_inspect"
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

FILES = {
    "quanhan_040": ("全漢文_卷四十.txt", "全漢文/卷四十", 2300175),
    "quanhan_042": ("全漢文_卷四十二.txt", "全漢文/卷四十二", 2299588),
    "quanhouhan_062": ("全後漢文_卷六十二.txt", "全後漢文/卷六十二", 2584229),
    "quanhouhan_068": ("全後漢文_卷六十八.txt", "全後漢文/卷六十八", 2584236),
}

for sid, (filename, page, revid) in FILES.items():
    src = SRC / filename
    dst = RAW / f"{sid}.txt"
    if src.exists() and not dst.exists():
        shutil.copyfile(src, dst)
    meta = {
        "source_id": sid,
        "title": page,
        "revid": revid,
        "url": "https://zh.wikisource.org/wiki/" + page.replace(" ", "_"),
        "note": "v3 新增；工作副本見 data/v3/_inspect/",
    }
    (RAW / f"{sid}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    print("OK", sid, len((RAW / f"{sid}.txt").read_text(encoding="utf-8")))
