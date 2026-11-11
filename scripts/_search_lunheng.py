import time

import requests

S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
API = "https://zh.wikisource.org/w/api.php"

terms = ["論衡 藝增", "論衡 語增", "論衡 儒增", "論衡 案書", "論衡 謝短",
         "論衡 別通", "論衡 書虛", "管子 劉向 書錄", "晏子 劉向 敘錄",
         "說苑 敘錄 劉向", "孟子章句 題辭", "春秋公羊解詁 序", "風俗通義 序"]

for term in terms:
    params = {"action": "query", "list": "search", "srsearch": term,
              "format": "json", "srlimit": 8}
    for attempt in range(4):
        try:
            r = S.get(API, params=params, timeout=60)
            if r.status_code != 200:
                print("### HTTP", r.status_code, term)
                time.sleep(15)
                continue
            data = r.json()
            print("###", term)
            for item in data.get("query", {}).get("search", []):
                print("   ", item["title"])
            break
        except Exception as exc:
            print("### ERROR", term, repr(exc))
            time.sleep(15)
    time.sleep(3)
