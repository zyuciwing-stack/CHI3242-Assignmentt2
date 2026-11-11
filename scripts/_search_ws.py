import requests

terms = [
    "淮南子 要略", "太史公自序", "報任安書", "兩都賦序", "漢書 藝文志",
    "論衡 超奇", "論衡 佚文", "論衡 對作", "論衡 自紀", "論衡 藝增",
    "楚辭章句 離騷", "詩譜序", "法言 吾子", "新論 道賦", "新論 正經",
    "戰國策書錄", "管子書錄", "晏子書錄", "荀子書錄", "列子書錄",
    "說苑敘錄", "全漢文", "全後漢文", "毛詩序", "楚辭 九歌序",
]

url = "https://zh.wikisource.org/w/api.php"
for term in terms:
    params = {"action": "query", "list": "search", "srsearch": term,
              "format": "json", "srlimit": 8}
    try:
        r = requests.get(url, params=params, timeout=30,
                         headers={"User-Agent": "CHI3242-course-project/1.0 (educational use)"})
        data = r.json()
        print("###", term)
        for item in data.get("query", {}).get("search", []):
            print("   ", item["title"])
    except Exception as exc:
        print("###", term, "ERROR", repr(exc))
