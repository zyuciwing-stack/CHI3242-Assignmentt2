import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSPECT = ROOT / "data" / "_inspect"
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

COPIES = {
    "huainanzi_yaolue": ("淮南子_要略.txt", "淮南子/要略", 9458285),
    "shiji_130": ("史記_卷130.txt", "史記/卷130", 2609362),
    "baoren_anshu": ("報任少卿書.txt", "報任少卿書", 12761153),
    "fayan_02": ("法言_02.txt", "法言/02", 2269064),
    "fayan_05": ("法言_05.txt", "法言/05", 2269138),
    "fayan_07": ("法言_07.txt", "法言/07", 2269136),
    "fayan_10": ("法言_10.txt", "法言/10", 2269139),
    "lunheng_039": ("論衡_39.txt", "論衡/39", 2326276),
    "lunheng_061": ("論衡_61.txt", "論衡/61", 2325845),
    "lunheng_084": ("論衡_84.txt", "論衡/84", 2372823),
    "lunheng_085": ("論衡_85.txt", "論衡/85", 2603875),
    "lunheng_027": ("論衡_27.txt", "論衡/27", 2325815),
    "liangdufu_xu": ("兩都賦序.txt", "兩都賦序", 2395749),
    "hanshu_030": ("漢書_卷030.txt", "漢書/卷030", 7908197),
    "chuci_zhangju_01": ("楚辭章句_卷01.txt", "楚辭章句/卷01", 2396569),
    "chuci_zhangju_02": ("楚辭章句_卷02.txt", "楚辭章句/卷02", 2149505),
    "chuci_zhangju_03": ("楚辭章句_卷03.txt", "楚辭章句/卷03", 2316447),
    "chuci_zhangju_04": ("楚辭章句_卷04.txt", "楚辭章句/卷04", 2149513),
    "chuci_zhangju_05": ("楚辭章句_卷05.txt", "楚辭章句/卷05", 2149510),
    "chuci_zhangju_06": ("楚辭章句_卷06.txt", "楚辭章句/卷06", 2149516),
    "chuci_zhangju_07": ("楚辭章句_卷07.txt", "楚辭章句/卷07", 2149518),
    "chuci_zhangju_08": ("楚辭章句_卷08.txt", "楚辭章句/卷08", 2149519),
    "xinlun_01": ("新論_01.txt", "新論/01", 363049),
    "xinlun_09": ("新論_09.txt", "新論/09", 360582),
    "xinlun_12": ("新論_12.txt", "新論/12", 360706),
    "fengsu_tongyi_xu": ("風俗通義序.txt", "風俗通義序", 366444),
    "maoshi_zhengyi_xu": ("毛詩正義_序.txt", "毛詩正義/序", 7911162),
}

now = datetime.now(timezone.utc).isoformat()
rows = []
for sid, (filename, page, revid) in COPIES.items():
    src = INSPECT / filename
    dst = RAW / f"{sid}.txt"
    if src.exists() and not dst.exists():
        shutil.copyfile(src, dst)
    if not dst.exists():
        print("MISSING", sid, src)
        continue
    meta_path = RAW / f"{sid}.json"
    meta = {
        "source_id": sid,
        "title": page,
        "revid": revid,
        "url": "https://zh.wikisource.org/wiki/" + page.replace(" ", "_"),
        "retrieved_at": now,
        "note": "工作副本；原件見 data/_inspect/",
    }
    if not meta_path.exists():
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    rows.append(meta)

# Existing JSON metadata (full fetch logs) take precedence for the 全漢文/全後漢文 volumes.
for path in sorted(RAW.glob("quan*_*.json")):
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
        if "source_id" in meta:
            rows.append(meta)
    except Exception:
        pass

# Write a combined manifest, de-duplicated by source_id.
seen = {}
for meta in rows:
    seen[meta["source_id"]] = meta
combined = [seen[k] for k in sorted(seen)]
(ROOT / "data" / "raw_manifest.json").write_text(
    json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
print("raw files:", len(list(RAW.glob("*.txt"))), "manifest records:", len(combined))
