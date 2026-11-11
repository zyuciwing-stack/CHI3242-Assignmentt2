import time

import requests

S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
API = "https://zh.wikisource.org/w/api.php"

terms = [
    "漢書 藝文志 詩賦略", "漢書/卷三十", "漢書/卷030",
    "鄭玄 詩譜序", "詩譜序 鄭玄", "毛詩正義 序",
    "楚辭章句 卷一", "楚辭章句/卷一", "王逸 離騷經序",
    "論衡 目録 四部叢刊", "論衡 卷十三 超奇",
    "法言 吾子 四部叢刊", "法言/吾子",
    "文選 兩都賦序", "班固 兩都賦序",
]

for term in terms:
    params = {"action": "query", "list": "search", "srsearch": term,
              "format": "json", "srlimit": 8}
    for attempt in range(3):
        try:
            r = S.get(API, params=params, timeout=60)
            if r.status_code != 200:
                print("### HTTP", r.status_code, term)
                time.sleep(5)
                continue
            data = r.json()
            print("###", term)
            for item in data.get("query", {}).get("search", []):
                print("   ", item["title"])
            break
        except Exception as exc:
            print("### ERROR", term, repr(exc))
            time.sleep(5)
    time.sleep(2)
