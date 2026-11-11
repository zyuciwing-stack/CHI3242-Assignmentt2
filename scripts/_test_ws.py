import requests

url = "https://zh.wikisource.org/w/api.php"
params = {"action": "query", "list": "search", "srsearch": "淮南子 要略",
          "format": "json", "srlimit": 5}
for headers in [
    None,
    {"User-Agent": "CHI3242-course-project/1.0 (educational use)"},
]:
    try:
        r = requests.get(url, params=params, timeout=30, headers=headers)
        print("status", r.status_code, "encoding", r.encoding, "len", len(r.content))
        print(r.text[:500])
    except Exception as exc:
        print("ERROR", repr(exc))
