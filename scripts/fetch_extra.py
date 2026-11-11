import json
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
    ("shiji_084", "史記/卷084"),
    ("shijing_xu", "詩經/序"),
    ("lunheng_025", "論衡/25"),
    ("lunheng_026", "論衡/26"),
    ("lunheng_036", "論衡/36"),
    ("lunheng_083", "論衡/83"),
]

rows = []
for sid, title in PAGES:
    ok = False
    for attempt in range(6):
        try:
            params = {"action": "query", "prop": "revisions|extracts", "titles": title,
                      "rvprop": "ids|timestamp", "explaintext": 1,
                      "format": "json", "formatversion": 2, "redirects": 1}
            r = S.get(API, params=params, timeout=90)
            if r.status_code != 200:
                print("RETRY", sid, r.status_code)
                time.sleep(15 + attempt * 10)
                continue
            data = r.json()
            pages = data.get("query", {}).get("pages", [])
            if not pages or pages[0].get("missing"):
                print("MISSING", sid, title)
                ok = True
                break
            page = pages[0]
            rev = page.get("revisions", [{}])[0]
            text = page.get("extract", "")
            (RAW / f"{sid}.txt").write_text(text, encoding="utf-8")
            meta = {
                "source_id": sid, "title": page.get("title"),
                "revid": rev.get("revid"), "timestamp": rev.get("timestamp"),
                "url": "https://zh.wikisource.org/wiki/" + page.get("title", "").replace(" ", "_"),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "chars": len(text),
            }
            (RAW / f"{sid}.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            rows.append(meta)
            print("OK", sid, title, "rev", meta["revid"], "chars", len(text))
            print(text[:160].replace("\n", " / "))
            ok = True
            break
        except Exception as exc:
            print("ERROR", sid, repr(exc))
            time.sleep(15 + attempt * 10)
    if not ok:
        print("GAVE UP", sid)
    time.sleep(4)

(ROOT / "data" / "extra_fetch_log.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", len(rows))
