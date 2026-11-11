import json
import time
from pathlib import Path

import requests

S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
API = "https://zh.wikisource.org/w/api.php"
OUT = Path(__file__).resolve().parent.parent / "data" / "_inspect"
OUT.mkdir(parents=True, exist_ok=True)

titles = [
    "法言/02", "法言/05", "法言/07", "法言/10",
    "論衡/84", "論衡/85", "論衡/60",
    "楚辭章句/卷02", "楚辭章句/卷03", "楚辭章句/卷04",
    "楚辭章句/卷05", "楚辭章句/卷06", "楚辭章句/卷07",
    "楚辭章句/卷08",
    "毛詩正義/序",
    "史記/卷130", "報任少卿書", "淮南子/要略",
    "毛詩正義 (四庫全書本)/詩譜序",
]


def fetch(title):
    params = {"action": "query", "prop": "revisions|extracts", "titles": title,
              "rvprop": "ids|timestamp", "explaintext": 1, "format": "json",
              "formatversion": 2, "redirects": 1}
    r = S.get(API, params=params, timeout=90)
    if r.status_code != 200:
        return None, r.status_code, r.text[:120]
    data = r.json()
    pages = data.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return None, "missing", ""
    page = pages[0]
    rev = page.get("revisions", [{}])[0]
    text = page.get("extract", "")
    meta = {"title": page.get("title"), "revid": rev.get("revid"),
            "timestamp": rev.get("timestamp"), "len": len(text)}
    return (text, meta), 200, ""


for title in titles:
    ok = False
    for attempt in range(5):
        try:
            result, status, msg = fetch(title)
            if status == 200 and result is not None:
                text, meta = result
                print("###", title, "->", meta["title"], "rev", meta["revid"],
                      "len", meta["len"])
                print(text[:220].replace("\n", " / "))
                safe = title.replace("/", "_").replace(" ", "_")
                (OUT / f"{safe}.txt").write_text(text, encoding="utf-8")
                (OUT / f"{safe}.json").write_text(
                    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
                ok = True
                break
            print("### RETRY", title, status, msg)
            time.sleep(12 + attempt * 8)
        except Exception as exc:
            print("### ERROR", title, repr(exc))
            time.sleep(12 + attempt * 8)
    if not ok:
        print("### GAVE UP", title)
    time.sleep(4)
