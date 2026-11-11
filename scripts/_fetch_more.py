import json
import re
import time
from pathlib import Path

import requests

S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
API = "https://zh.wikisource.org/w/api.php"
OUT = Path(__file__).resolve().parent.parent / "data" / "_inspect"
OUT.mkdir(parents=True, exist_ok=True)

titles = [
    "毛詩正義 (四庫全書本)/詩譜序",
    "孟子 (四部叢刊本)/題辭",
    "春秋公羊經傳解詁 (四部叢刊本)/序",
    "風俗通義序",
    "論衡/27",
    "管子 (四庫全書本)",
    "晏子春秋 (四部叢刊本)/目録",
    "説苑 (四庫全書本)",
]


def clean_wikitext(text):
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.S)
    text = re.sub(r"<onlyinclude>|</onlyinclude>", "", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text


for title in titles:
    ok = False
    for attempt in range(5):
        try:
            params = {"action": "query", "prop": "revisions|extracts", "titles": title,
                      "rvprop": "ids|timestamp|content", "explaintext": 1,
                      "format": "json", "formatversion": 2, "redirects": 1}
            r = S.get(API, params=params, timeout=90)
            if r.status_code != 200:
                print("### RETRY", title, r.status_code)
                time.sleep(15 + attempt * 10)
                continue
            data = r.json()
            pages = data.get("query", {}).get("pages", [])
            if not pages or pages[0].get("missing"):
                print("### MISSING", title)
                ok = True
                break
            page = pages[0]
            rev = page.get("revisions", [{}])[0]
            extract = page.get("extract", "")
            wikitext = rev.get("content", "")
            text = extract if extract.strip() else clean_wikitext(wikitext)
            print("###", title, "->", page.get("title"), "rev", rev.get("revid"),
                  "extract", len(extract), "wikitext", len(wikitext),
                  "used", len(text))
            print(text[:400].replace("\n", " / "))
            safe = title.replace("/", "_").replace(" ", "_")
            (OUT / f"{safe}.txt").write_text(text, encoding="utf-8")
            (OUT / f"{safe}.wikitext").write_text(wikitext, encoding="utf-8")
            (OUT / f"{safe}.json").write_text(
                json.dumps({"title": page.get("title"), "revid": rev.get("revid"),
                            "timestamp": rev.get("timestamp")},
                           ensure_ascii=False, indent=2), encoding="utf-8")
            ok = True
            break
        except Exception as exc:
            print("### ERROR", title, repr(exc))
            time.sleep(15 + attempt * 10)
    if not ok:
        print("### GAVE UP", title)
    time.sleep(5)
