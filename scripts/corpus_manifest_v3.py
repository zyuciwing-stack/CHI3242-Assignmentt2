# -*- coding: utf-8 -*-
"""v3 選篇清單：保留 v2，修正 W17/W18 標籤，補收四位新作者。"""

from copy import deepcopy

from corpus_manifest import WORKS as V2_WORKS

WORKS_V3 = deepcopy(V2_WORKS)

# ---------------- 1. 只修正標籤：W17/W18 移到「歸屬待核」 ----------------
for work in WORKS_V3:
    if work["work_id"] == "W17":
        work["period"] = "歸屬待核"
        work["status"] = "uncertain_attribution"
        work["notes"] = (
            "舊題劉向；《關尹子》成書年代與劉向敘錄的歸屬有爭議，"
            "列「歸屬待核」，不納入訓練。保留原文與舊題作者。"
        )
        work["dating_basis"] = (
            "舊題劉向校書敘錄；《關尹子》成書年代與敘錄歸屬有爭議，待核。"
        )
    elif work["work_id"] == "W18":
        work["period"] = "歸屬待核"
        work["status"] = "uncertain_attribution"
        work["notes"] = (
            "舊題劉向；《子華子》成書年代與劉向敘錄的歸屬有爭議，"
            "列「歸屬待核」，不納入訓練。保留原文與舊題作者。"
        )
        work["dating_basis"] = (
            "舊題劉向校書敘錄；《子華子》成書年代與敘錄歸屬有爭議，待核。"
        )

# ---------------- 2. 補收新作者 ----------------
WORKS_V3 += [
    {
        "work_id": "W24",
        "work_title": "四子講德論（節選）",
        "author": "王褒",
        "period": "西漢",
        "genre": "論·詩歌功用",
        "genre_group": "論",
        "carrier": "全漢文/文選",
        "cao_section": "Ⅷ 兩漢文藝理論資料匯輯·十三 王褒",
        "cao_pages": "515–516",
        "cao_status": "資料匯輯（待核原書）",
        "quanwen_check": "《全漢文》卷四十二〈四子講德論〉",
        "base_id": "quanhan_042",
        "base_page": "全漢文/卷四十二",
        "base_revision": 2299588,
        "base_url": "https://zh.wikisource.org/wiki/全漢文/卷四十二",
        "extract_mode": "section_paragraphs",
        "extract_spec": {"section": "四子講德論〈并序〉", "indices": [0, 2]},
        "dating_basis": "王褒，宣帝時待詔；〈四子講德論〉作於宣帝時，西漢中期。",
        "status": "included",
        "version_added": 3,
        "notes": (
            "取序文與論詩歌、賦頌功用的連續段落（paragraphs 0、2）；"
            "略去後半講德辯論。"
        ),
    },
    {
        "work_id": "W25",
        "work_title": "移書讓太常博士（節選）",
        "author": "劉歆",
        "period": "西漢",
        "genre": "書信·經學論",
        "genre_group": "書信",
        "carrier": "全漢文/漢書/文選",
        "cao_section": "Ⅷ 兩漢文藝理論資料匯輯·十 劉歆",
        "cao_pages": "508–509",
        "cao_status": "資料匯輯（待核原書）",
        "quanwen_check": "《全漢文》卷四十〈移書讓太常博士〉",
        "base_id": "quanhan_040",
        "base_page": "全漢文/卷四十",
        "base_revision": 2300175,
        "base_url": "https://zh.wikisource.org/wiki/全漢文/卷四十",
        "extract_mode": "section",
        "extract_spec": {"section": "移書讓太常博士〈并序〉"},
        "dating_basis": "劉歆（約前50–23）於哀帝時移書讓太常博士，西漢晚期。",
        "status": "included",
        "version_added": 3,
        "notes": (
            "全篇為爭立《左氏春秋》《毛詩》《逸禮》《古文尚書》的移書，"
            "直接論雅頌、易書春秋與經傳詮釋；全篇納入。"
        ),
    },
    {
        "work_id": "E37",
        "work_title": "孟子題辭",
        "author": "趙岐",
        "period": "東漢",
        "genre": "經解序·孟子學",
        "genre_group": "序跋",
        "carrier": "全後漢文/孟子章句",
        "cao_section": "Ⅷ 兩漢文藝理論資料匯輯·二十八 趙岐",
        "cao_pages": "539–540",
        "cao_status": "資料匯輯（待核原書）",
        "quanwen_check": "《全後漢文》卷六十二〈孟子題辭〉",
        "base_id": "quanhouhan_062",
        "base_page": "全後漢文/卷六十二",
        "base_revision": 2584229,
        "base_url": "https://zh.wikisource.org/wiki/全後漢文/卷六十二",
        "extract_mode": "section",
        "extract_spec": {"section": "孟子題辭"},
        "dating_basis": "趙岐（約108–201）撰《孟子章句》；〈孟子題辭〉為其晚年整理《孟子》所作，東漢晚期。",
        "status": "included",
        "version_added": 3,
        "notes": "全篇論《孟子》書名、作者、篇目與文辭；全篇納入。",
    },
    {
        "work_id": "E38",
        "work_title": "孟子篇敘",
        "author": "趙岐",
        "period": "東漢",
        "genre": "經解序·孟子學",
        "genre_group": "序跋",
        "carrier": "全後漢文/孟子章句",
        "cao_section": "Ⅷ 兩漢文藝理論資料匯輯·二十八 趙岐",
        "cao_pages": "539–540",
        "cao_status": "資料匯輯（待核原書）",
        "quanwen_check": "《全後漢文》卷六十二〈孟子篇敘〉",
        "base_id": "quanhouhan_062",
        "base_page": "全後漢文/卷六十二",
        "base_revision": 2584229,
        "base_url": "https://zh.wikisource.org/wiki/全後漢文/卷六十二",
        "extract_mode": "section",
        "extract_spec": {"section": "孟子篇敘"},
        "dating_basis": "趙岐撰；與〈孟子題辭〉同時，東漢晚期。",
        "status": "included",
        "version_added": 3,
        "notes": "〈孟子題辭〉同卷附篇，說明七篇次序；與題辭合觀，全篇納入。",
    },
    {
        "work_id": "E39",
        "work_title": "春秋公羊經傳解詁序",
        "author": "何休",
        "period": "東漢",
        "genre": "經解序·春秋學",
        "genre_group": "序跋",
        "carrier": "全後漢文/春秋公羊解詁",
        "cao_section": "Ⅷ 兩漢文藝理論資料匯輯·二十九 何休",
        "cao_pages": "541–542",
        "cao_status": "資料匯輯（待核原書）",
        "quanwen_check": "《全後漢文》卷六十八〈春秋公羊經傳解詁序〉",
        "base_id": "quanhouhan_068",
        "base_page": "全後漢文/卷六十八",
        "base_revision": 2584236,
        "base_url": "https://zh.wikisource.org/wiki/全後漢文/卷六十八",
        "extract_mode": "section",
        "extract_spec": {"section": "春秋公羊經傳解詁序"},
        "dating_basis": "何休（129–182）撰《春秋公羊經傳解詁》；序作於東漢晚期。",
        "status": "included",
        "version_added": 3,
        "notes": "全篇論《春秋》與公羊傳的詮釋；全篇納入。",
    },
]

STATUS_LABELS_V3 = {
    "included": "納入主訓練",
    "included_secondary": "納入全庫，主訓練列次要",
    "reserved": "預留獨立分析",
    "uncertain": "歸屬未定，不作訓練",
    "uncertain_attribution": "歸屬待核，不作訓練",
    "excluded": "已核，未收",
    "pending": "已定位，待核／未收",
}
