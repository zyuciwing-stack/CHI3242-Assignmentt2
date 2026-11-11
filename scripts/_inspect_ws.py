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
    "論衡", "法言", "新論", "楚辭章句", "楚辭",
    "漢書/卷30", "全漢文/卷三十七", "全後漢文/目錄", "文選/卷1",
    "詩譜", "毛詩序", "欽定四庫全書總目/卷019",
]

for title in titles:
    for attempt in range(4):
        try:
            params = {"action": "query", "prop": "revisions|extracts", "titles": title,
                      "rvprop": "ids|timestamp", "explaintext": 1, "format": "json",
                      "formatversion": 2, "redirects": 1}
            r = S.get(API, params=params, timeout=60)
            if r.status_code != 200:
                print("### HTTP", r.status_code, title, r.text[:120])
                time.sleep(3)
                continue
            data = r.json()
            pages = data.get("query", {}).get("pages", [])
            if not pages or pages[0].get("missing"):
                print("### MISSING", title)
                break
            page = pages[0]
            rev = page.get("revisions", [{}])[0]
            text = page.get("extract", "")
            print("###", title, "->", page.get("title"), "rev", rev.get("revid"),
                  "len", len(text))
            print(text[:500].replace("\n", " / "))
            safe = title.replace("/", "_").replace(" ", "_")
            (OUT / f"{safe}.txt").write_text(text, encoding="utf-8")
            break
        except Exception as exc:
            print("### ERROR", title, repr(exc))
            time.sleep(3)
    time.sleep(1)
