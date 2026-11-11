import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
API = "https://zh.wikisource.org/w/api.php"

PAGES = [
    ("quanhan_026", "全漢文/卷二十六", "全漢文", "卷二十六", "司馬遷"),
    ("quanhan_035", "全漢文/卷三十五", "全漢文", "卷三十五", "劉向"),
    ("quanhan_036", "全漢文/卷三十六", "全漢文", "卷三十六", "劉向"),
    ("quanhan_037", "全漢文/卷三十七", "全漢文", "卷三十七", "劉向"),
    ("quanhan_038", "全漢文/卷三十八", "全漢文", "卷三十八", "劉向"),
    ("quanhan_039", "全漢文/卷三十九", "全漢文", "卷三十九", "劉向"),
    ("quanhouhan_012", "全後漢文/卷十二", "全後漢文", "卷十二", "桓譚"),
    ("quanhouhan_013", "全後漢文/卷十三", "全後漢文", "卷十三", "桓譚"),
    ("quanhouhan_014", "全後漢文/卷十四", "全後漢文", "卷十四", "桓譚"),
    ("quanhouhan_015", "全後漢文/卷十五", "全後漢文", "卷十五", "桓譚"),
    ("quanhouhan_024", "全後漢文/卷二十四", "全後漢文", "卷二十四", "班固"),
    ("quanhouhan_057", "全後漢文/卷五十七", "全後漢文", "卷五十七", "王逸"),
]


def clean_wikitext(text):
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.S)
    text = re.sub(r"<onlyinclude>|</onlyinclude>", "", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text


def fetch(title):
    params = {"action": "query", "prop": "revisions|extracts", "titles": title,
              "rvprop": "ids|timestamp|content", "explaintext": 1,
              "format": "json", "formatversion": 2, "redirects": 1}
    r = S.get(API, params=params, timeout=90)
    if r.status_code != 200:
        return None, r.status_code, r.text[:160]
    data = r.json()
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return None, "missing", ""
    page = pages[0]
    rev = page.get("revisions", [{}])[0]
    extract = page.get("extract", "")
    wikitext = rev.get("content", "")
    text = extract if extract.strip() else clean_wikitext(wikitext)
    return {
        "title": page.get("title"),
        "revid": rev.get("revid"),
        "timestamp": rev.get("timestamp"),
        "url": "https://zh.wikisource.org/wiki/" + page.get("title", "").replace(" ", "_"),
        "extract": extract,
        "wikitext": wikitext,
        "text": text,
    }, 200, ""


meta_rows = []
for sid, title, book, volume, author in PAGES:
    ok = False
    for attempt in range(6):
        try:
            result, status, msg = fetch(title)
            if status == 200 and result is not None:
                (RAW / f"{sid}.txt").write_text(result["text"], encoding="utf-8")
                (RAW / f"{sid}.wikitext").write_text(result["wikitext"], encoding="utf-8")
                meta = {k: result[k] for k in ("title", "revid", "timestamp", "url")}
                meta.update({"source_id": sid, "book": book, "volume": volume,
                             "author": author, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                             "extract_chars": len(result["extract"]),
                             "text_chars": len(result["text"])})
                (RAW / f"{sid}.json").write_text(
                    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
                meta_rows.append(meta)
                print("OK", sid, title, "rev", result["revid"],
                      "extract", len(result["extract"]), "text", len(result["text"]))
                heads = [ln for ln in result["text"].splitlines() if ln.startswith("===")]
                print("   headings:", " | ".join(heads[:12]))
                ok = True
                break
            print("RETRY", sid, status, msg)
            time.sleep(15 + attempt * 10)
        except Exception as exc:
            print("ERROR", sid, repr(exc))
            time.sleep(15 + attempt * 10)
    if not ok:
        print("GAVE UP", sid, title)
    time.sleep(4)

(ROOT / "data" / "quanwen_fetch_log.json").write_text(
    json.dumps(meta_rows, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", len(meta_rows), "records")
