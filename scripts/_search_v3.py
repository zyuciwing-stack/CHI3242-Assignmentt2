import time

import requests

S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
API = "https://zh.wikisource.org/w/api.php"

terms = [
    "四子講德論", "王褒 四子講德", "移書讓太常博士", "劉歆 移書讓太常",
    "孟子題辭", "趙岐 孟子題辭", "孟子章句 題辭",
    "春秋公羊經傳解詁序", "何休 公羊 序", "春秋公羊傳註疏 序",
    "全漢文 王褒", "全漢文 劉歆", "全後漢文 趙岐", "全後漢文 何休",
]

for term in terms:
    params = {"action": "query", "list": "search", "srsearch": term,
              "format": "json", "srlimit": 8}
    for attempt in range(3):
        try:
            r = S.get(API, params=params, timeout=60)
            if r.status_code != 200:
                print("### HTTP", r.status_code, term)
                time.sleep(10)
                continue
            data = r.json()
            print("###", term)
            for item in data.get("query", {}).get("search", []):
                print("   ", item["title"])
            break
        except Exception as exc:
            print("### ERROR", term, repr(exc))
            time.sleep(10)
    time.sleep(3)
