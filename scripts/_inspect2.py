import time
from pathlib import Path

import requests

S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
API = "https://zh.wikisource.org/w/api.php"
OUT = Path(__file__).resolve().parent.parent / "data" / "_inspect"
OUT.mkdir(parents=True, exist_ok=True)

titles = [
    "論衡 (四部叢刊本)/目録",
    "楚辭 (四部叢刊本)/目録",
    "毛詩正義 (四庫全書本)/詩譜序",
    "漢書/卷030",
    "兩都賦序",
    "揚子法言 (四部叢刊本)/卷第二",
    "新論/01", "新論/09", "新論/12",
    "論衡/39", "論衡/61",
    "楚辭章句/卷01", "楚辭章句/卷一",
    "楚辭 (四部叢刊本)/卷第一",
]

for title in titles:
    done = False
    for attempt in range(5):
        try:
            params = {"action": "query", "prop": "revisions|extracts", "titles": title,
                      "rvprop": "ids|timestamp", "explaintext": 1, "format": "json",
                      "formatversion": 2, "redirects": 1}
            r = S.get(API, params=params, timeout=60)
            if r.status_code != 200:
                print("### HTTP", r.status_code, title, "attempt", attempt)
                time.sleep(10 + attempt * 10)
                continue
            data = r.json()
            pages = data.get("query", {}).get("pages", [])
            if not pages or pages[0].get("missing"):
                print("### MISSING", title)
                done = True
                break
            page = pages[0]
            rev = page.get("revisions", [{}])[0]
            text = page.get("extract", "")
            print("###", title, "->", page.get("title"), "rev", rev.get("revid"),
                  "len", len(text))
            print(text[:700].replace("\n", " / "))
            safe = title.replace("/", "_").replace(" ", "_")
            (OUT / f"{safe}.txt").write_text(text, encoding="utf-8")
            done = True
            break
        except Exception as exc:
            print("### ERROR", title, repr(exc))
            time.sleep(10)
    if not done:
        print("### GAVE UP", title)
    time.sleep(3)
