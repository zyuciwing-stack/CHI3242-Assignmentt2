import time

import requests

S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
API = "https://zh.wikisource.org/w/api.php"

terms = ["詩譜序", "鄭玄 詩譜", "全後漢文 鄭玄", "詩譜 序 鄭氏",
         "毛詩譜", "鄭康成 詩譜"]

for term in terms:
    params = {"action": "query", "list": "search", "srsearch": term,
              "format": "json", "srlimit": 10}
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
