import requests
import time

S = requests.Session()
S.headers.update({"User-Agent": "CHI3242-course-project/1.0 (educational use; contact: student)"})
API = "https://zh.wikisource.org/w/api.php"

configs = [
    {"action": "query", "prop": "revisions", "titles": "淮南子/要略",
     "rvprop": "ids|timestamp|content", "format": "json", "formatversion": 2},
    {"action": "query", "prop": "extracts", "titles": "淮南子/要略",
     "explaintext": 1, "format": "json", "formatversion": 2},
    {"action": "parse", "page": "淮南子/要略", "prop": "wikitext",
     "format": "json", "formatversion": 2},
]
for c in configs:
    r = S.get(API, params=c, timeout=60)
    print("STATUS", r.status_code, "URL", r.url[:200])
    print(r.text[:300])
    time.sleep(1)
