import json
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "v3" / "_inspect"
OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
API = "https://zh.wikisource.org/w/api.php"

TITLES = [
    "四子講德論",
    "移書讓太常博士",
    "全漢文/卷四十二",
    "全漢文/卷四十",
    "孟子註疏/孟子注疏題辭解",
    "孟子注疏 (四庫全書本)/序",
    "全後漢文/卷六十二",
    "春秋公羊傳註疏/序",
    "春秋公羊傳注疏 (四庫全書本)/序",
    "全後漢文/卷七十七",
    "全後漢文/目錄",
]


def clean_wikitext(text):
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.S)
    text = re.sub(r"<onlyinclude>|</onlyinclude>", "", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text


for title in TITLES:
    ok = False
    for attempt in range(6):
        try:
            params = {"action": "query", "prop": "revisions|extracts", "titles": title,
                      "rvprop": "ids|timestamp|content", "explaintext": 1,
                      "format": "json", "formatversion": 2, "redirects": 1}
            r = S.get(API, params=params, timeout=90)
            if r.status_code != 200:
                print("RETRY", title, r.status_code)
                time.sleep(15 + attempt * 10)
                continue
            data = r.json()
            pages = data.get("query", {}).get("pages", [])
            if not pages or pages[0].get("missing"):
                print("MISSING", title)
                ok = True
                break
            page = pages[0]
            rev = page.get("revisions", [{}])[0]
            extract = page.get("extract", "")
            wikitext = rev.get("content", "")
            text = extract if extract.strip() else clean_wikitext(wikitext)
            safe = title.replace("/", "_").replace(" ", "_")
            (OUT / f"{safe}.txt").write_text(text, encoding="utf-8")
            (OUT / f"{safe}.wikitext").write_text(wikitext, encoding="utf-8")
            meta = {"title": page.get("title"), "revid": rev.get("revid"),
                    "timestamp": rev.get("timestamp"),
                    "url": "https://zh.wikisource.org/wiki/" + page.get("title", "").replace(" ", "_"),
                    "extract_chars": len(extract), "text_chars": len(text)}
            (OUT / f"{safe}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
            print("OK", title, "rev", meta["revid"], "extract", len(extract), "text", len(text))
            print(text[:220].replace("\n", " / "))
            ok = True
            break
        except Exception as exc:
            print("ERROR", title, repr(exc))
            time.sleep(15 + attempt * 10)
    if not ok:
        print("GAVE UP", title)
    time.sleep(4)
