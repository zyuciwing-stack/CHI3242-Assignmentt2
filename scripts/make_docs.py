# -*- coding: utf-8 -*-
"""Generate the selection-basis table, sufficiency check, and version log."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"

sources = pd.read_csv(DATA / "sources.csv", encoding="utf-8-sig")
sources = sources.fillna("")


def fmt_rev(value):
    text = str(value).strip()
    if text in {"", "nan", "None"}:
        return ""
    try:
        return str(int(float(text)))
    except Exception:
        return text


sources["base_revision"] = sources["base_revision"].apply(fmt_rev)

# ---------------- selection basis ----------------
lines = [
    "# 選篇依據與實際底本",
    "",
    "本表分開記錄「據哪部書選入」與「實際擷取的原文版本」。",
    "",
    "- 選篇核心清單：曹順慶主編《兩漢文論譯注》（北京：北京出版社，1988）。",
    "  頁碼據豆瓣所載目錄（https://www.douban.com/subject/36127385/）；",
    "  書葵網另載一組略有出入的頁碼（https://www.shukui.net/book/3668495.html）。",
    "  曹本頁碼一律標「待核原書」，因本輪未見紙本。",
    "- 核查與補收：嚴可均校輯《全上古三代秦漢三國六朝文》之《全漢文》《全後漢文》",
    "  （中華書局本；本輪所據為維基文庫轉錄，卷次、修訂號、網址見表二）。",
    "  中華書局影印本頁碼未見原書，暫記卷次，待核。",
    "- 同一篇在曹本與《全漢文》／《全後漢文》都有，只算一篇；表一並列兩處依據。",
    "- 模型資料只取古文正文；曹本的題解、今譯、注釋未進入模型。",
    "",
    "## 表一　選篇依據",
    "",
    "| ID | 篇名 | 作者 | 分期 | 曹本部位 | 曹本頁碼 | 曹本狀態 | 《全漢文》／《全後漢文》核查 | 本輪狀態 | 首見版本 |",
    "|---|---|---|---|---|---|---|---|---|---|",
]
for _, row in sources.iterrows():
    version = f"v{int(row['version_added'])}" if int(row["version_added"]) > 0 else "—"
    lines.append(
        f"| {row['work_id']} | {row['work_title']} | {row['author']} | {row['period']} | "
        f"{row['cao_section']} | {row['cao_pages']} | {row['cao_status']} | "
        f"{row['quanwen_check']} | {row['status_label']} | {version} |")
lines += [
    "",
    "## 表二　實際底本",
    "",
    "| ID | 篇名 | 底本頁面 | 修訂號 | 網址 | 擷取方式 | 擷取範圍 |",
    "|---|---|---|---|---|---|---|",
]
for _, row in sources.iterrows():
    if not str(row["base_page"]).strip():
        continue
    spec = str(row["extract_spec"])
    lines.append(
        f"| {row['work_id']} | {row['work_title']} | {row['base_page']} | "
        f"{row['base_revision']} | {row['base_url']} | {row['extract_mode']} | {spec} |")
lines += [
    "",
    "## 表三　狀態統計",
    "",
]
status_counts = sources["status_label"].value_counts()
for label, count in status_counts.items():
    lines.append(f"- {label}: {count}")
lines += [
    "",
    "## 已定位但待核／未收篇目",
    "",
    "| ID | 篇名 | 作者 | 分期 | 曹本頁碼 | 說明 |",
    "|---|---|---|---|---|---|",
]
for _, row in sources[sources["status"].isin(["pending", "excluded", "uncertain"])].iterrows():
    lines.append(
        f"| {row['work_id']} | {row['work_title']} | {row['author']} | {row['period']} | "
        f"{row['cao_pages']} | {row['notes']} |")

lines += [
    "",
    "### 曹本資料匯輯其餘作者（已定位，待補）",
    "",
    "以下作者見曹本目錄「Ⅷ、兩漢文藝理論資料匯輯」，本輪未逐篇取得可核正文，列待補；",
    "頁碼據豆瓣目錄，待核原書。",
    "",
    "| 作者 | 曹本頁碼 | 本輪狀態 |",
    "|---|---:|---|",
]
PENDING_AUTHORS = [
    ("陸賈", "433"), ("賈誼", "438"), ("枚乘", "443"), ("司馬相如", "444"),
    ("董仲舒", "445"), ("韓嬰", "458"), ("劉歆", "508"), ("桓寬", "509"),
    ("漢宣帝", "514"), ("王褒", "515"), ("翼奉", "517"), ("班彪", "523"),
    ("漢明帝", "524"), ("張奮", "525"), ("傅毅", "526"), ("王符", "527"),
    ("崔駰", "531"), ("張衡", "532"), ("馬融", "535"), ("王延壽", "536"),
    ("李固", "538"), ("劉梁", "542"), ("侯瑾", "543"), ("劉熙", "548"),
    ("蔡邕", "551"), ("趙壹", "551"), ("穎容", "554"), ("荀悅", "555"),
    ("仲長統", "559"), ("高誘", "561"),
]
for author, pages in PENDING_AUTHORS:
    lines.append(f"| {author} | {pages} | 待核／未收 |")
lines += [
    "",
    "## 斷代與跨期說明",
    "",
    "- 西漢：劉安、司馬談、司馬遷、劉向、揚雄。",
    "- 《法言》採用傳統西漢歸類的操作口徑（成於西漢末年或新莽初年）。",
    "- 東漢：班固、王充、王逸、桓譚、鄭玄、應劭。",
    "- 桓譚（約前43–28）歷西漢末、新莽、東漢初；《新論》定稿於東漢初，按成書歸東漢，",
    "  另在結果中作「排除桓譚」敏感度檢查。",
    "- 《漢書·藝文志》為班固東漢編定，但詩賦略本劉歆《七略》，屬層累文本；",
    "  正文歸東漢，分析時說明其西漢來源。",
    "- 《毛詩序》作者與成篇年代有爭議（舊題毛亨，或以為衛宏），列「歸屬未定」，",
    "  不進入訓練，只作獨立探針。",
    "",
]
(DATA / "selection_basis.md").write_text("\n".join(lines), encoding="utf-8")

# ---------------- sufficiency check ----------------
v1 = json.loads((OUTPUT / "corpus_summary_v1.json").read_text(encoding="utf-8"))
v2 = json.loads((OUTPUT / "corpus_summary_v2.json").read_text(encoding="utf-8"))
lines = [
    "# 句數與達標檢查",
    "",
    "切句規則：按底本句號、問號、感嘆號切句；保留原句與句序。",
    "預留〈論衡·超奇〉整篇作獨立分析；去重（精確與近重）後計算。",
    "",
    "## 全庫（未設篇／作者上限）",
    "",
    "| 版本 | 分期 | 句數 | 篇數 | 作者數 | 最大篇目佔比 | 最大作者佔比 |",
    "|---|---|---:|---:|---:|---|---|",
]
for label, data in [("v1", v1), ("v2", v2)]:
    for period, info in data["by_period"].items():
        lines.append(
            f"| {label} | {period} | {info['sentences']} | {info['works']} | "
            f"{info['authors']} | {info['max_work']} ({info['max_work_share']:.1%}) | "
            f"{info['max_author']} ({info['max_author_share']:.1%}) |")
lines += [
    "",
    "## 正式訓練取樣（主樣本）",
    "",
    "取樣規則：每篇最多 80 句、每作者最多 160 句；若兩期句數比超過 1.25，",
    "再對較多的一期隨機下採樣至與較少一期相同；隨機種子 42。",
    "分層 80% 訓練、20% 測試，種子 42。",
    "",
    "| 版本 | 西漢句數 | 東漢句數 | 訓練 | 測試 | 篇數 | 作者數 | 最大篇目佔比 | 最大作者佔比 |",
    "|---|---:|---:|---:|---:|---:|---:|---|---|",
]
for label, data in [("v1", v1), ("v2", v2)]:
    ms = data["main_sample"]
    lines.append(
        f"| {label} | {ms['by_period'].get('西漢', 0)} | {ms['by_period'].get('東漢', 0)} | "
        f"{ms['by_split'].get('train', 0)} | {ms['by_split'].get('test', 0)} | "
        f"{ms['works']} | {ms['authors']} | {ms['max_work']} ({ms['max_work_share']:.1%}) | "
        f"{ms['max_author']} ({ms['max_author_share']:.1%}) |")
lines += [
    "",
    "## 文類分布（v2）",
    "",
    "| 分期 | 文類 | 全庫句數 | 主樣本句數 |",
    "|---|---|---:|---:|",
]
v2_df = pd.read_csv(DATA / "dataset_v2.csv", encoding="utf-8-sig")
for period in ["西漢", "東漢"]:
    full_genres = v2["by_period"][period]["genres"]
    sample_genres = v2_df[v2_df["period"] == period]["genre_group"].value_counts().to_dict()
    for genre in sorted(set(full_genres) | set(sample_genres)):
        lines.append(f"| {period} | {genre} | {full_genres.get(genre, 0)} | "
                     f"{sample_genres.get(genre, 0)} |")
lines += [
    "",
    "## 達標結論",
    "",
    "- v1 主樣本：西漢 433 句、東漢 371 句；兩類均 ≥ 200，無差額。",
    "- v2 主樣本：西漢 559 句、東漢 450 句；兩類均 ≥ 200，無差額。",
    "- 預留〈超奇〉129 句（不計入訓練／測試）；去重後仍達標。",
    "- 全庫最大作者佔比偏高（v2 東漢王充 66.7%），故正式訓練採篇／作者上限；",
    "  全庫結果另作敏感度對照，不作為主結果。",
    "",
]
(OUTPUT / "sufficiency_check.md").write_text("\n".join(lines), encoding="utf-8")

# ---------------- version log ----------------
RUNS = [
    ("v1", "v1_main", "第一版：核心篇目；未加入《全漢文》／《全後漢文》補收"),
    ("v2", "v2_main", "第二版：加入劉向全敘錄、別錄節選、司馬談、王逸補收、應劭"),
    ("full", "v2_full", "全庫不設篇／作者上限；王充佔東漢 66.7%"),
    ("grouped", "v2_grouped", "同篇不跨訓練／測試；822/187（81.5%／18.5%），測試 187 句（西漢 94／東漢 93）"),
    ("variants/balanced", "v2_balanced", "class_weight=balanced"),
    ("variants/mindf1", "v2_mindf1", "min_df=1"),
    ("variants/bigram", "v2_bigram", "詞語 1–2-gram"),
    ("variants/stopwords", "v2_stopwords", "qhchina 0.2.7 zh_cl_tr 停用詞"),
    ("variants/bigram_mindf1", "v2_bigram_mindf1", "1–2-gram + min_df=1"),
    ("variants/balanced_mindf1", "v2_balanced_mindf1", "balanced + min_df=1"),
    ("leave_author_out_wangchong", "leave_author_out_wangchong",
     "留一作者：訓練不含王充，測試全部王充篇章"),
    ("leave_author_out_wangchong_balanced", "leave_author_out_wangchong_balanced",
     "留一作者＋class_weight=balanced；訓練不含王充"),
    ("leave_author_out_huantan", "leave_author_out_huantan",
     "留一作者：訓練不含桓譚，測試全部桓譚篇章；測試全為東漢"),
    ("leave_author_out_huantan_balanced", "leave_author_out_huantan_balanced",
     "留一作者＋class_weight=balanced；訓練不含桓譚；測試全為東漢"),
]
rows = []
for rel, name, note in RUNS:
    d = OUTPUT / rel
    meta_path = d / "run_metadata.json"
    indep_path = d / "independent_summary.json"
    if not meta_path.exists():
        continue
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    indep = json.loads(indep_path.read_text(encoding="utf-8")) if indep_path.exists() else {}
    m = meta["metrics"]
    rows.append({
        "run": name,
        "n_train": meta["n_train"],
        "n_test": meta["n_test"],
        "accuracy": m["accuracy"],
        "macro_f1": m["macro_f1"],
        "east_recall": m["recall"]["東漢"],
        "west_recall": m["recall"]["西漢"],
        "chaoqi_acc": indep.get("accuracy", ""),
        "chaoqi_hits": round(indep.get("accuracy", 0) * 129) if indep else "",
        "note": note,
    })
log = pd.DataFrame(rows)
log.to_csv(OUTPUT / "version_log.csv", index=False, encoding="utf-8-sig")
lines = [
    "# 版本紀錄",
    "",
    "所有版本使用同一套切句與去重規則；差異在資料版本、取樣規則、特徵或切分方式。",
    "",
    "| run | n train | n test | accuracy | macro F1 | 東漢 recall | 西漢 recall | 〈超奇〉東漢/129 | 說明 |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---|",
]
for _, row in log.iterrows():
    chao = f"{row['chaoqi_hits']}/129" if row["chaoqi_hits"] != "" else ""
    lines.append(
        f"| {row['run']} | {row['n_train']} | {row['n_test']} | {row['accuracy']:.4f} | "
        f"{row['macro_f1']:.4f} | {row['east_recall']:.4f} | {row['west_recall']:.4f} | "
        f"{chao} | {row['note']} |")
lines += [
    "",
    "> `leave_author_out_wangchong`、`leave_author_out_wangchong_balanced`、`leave_author_out_huantan`、`leave_author_out_huantan_balanced` 的測試全為單一作者（東漢），故西漢 recall 不適用；accuracy 即東漢 recall。",
    "",
    "## 主要觀察",
    "",
    "- v1 與 v2 的隨機句級測試準確率相近（約 0.63–0.64），但 v2 資料更完整、來源更廣。",
    "- v2_main 命中 127/202，只比多數類基準 112/202 多 15 句。",
    "- 全庫不設上限時準確率升至 0.7451，〈超奇〉亦升至 108/129；但這是王充其他篇章",
    "  主導東漢類的結果，不能當作一般化證據。",
    "- 按篇／作者上限後，〈超奇〉降至 49/129；留一作者（訓練不含王充）時，",
    "  王充全部篇章僅 9/710 被判為東漢，〈超奇〉僅 2/129。",
    "- 對照：留一作者抽走桓譚時，62 句桓譚仍有 38/62 判為東漢（61.3%）；",
    "  跨作者泛化因作者而異，不能把王充的 1.27% 當成所有東漢作者的普遍情況。",
    "- 平衡版對照：王充留出 9/710 → 176/710；桓譚留出 38/62 → 28/62。",
    "  方向取決於訓練集類別比例：王充留出時東漢是少數（290/948），balance 提高東漢命中；",
    "  桓譚留出時東漢是多數（809/1467），balance 反而降低東漢命中。",
    "- 因此結果會受作者、文類、來源與類別比例影響，現有設計難以分離各自的作用。",
    "- 同篇不跨訓練／測試的分組切分準確率 0.6684，與隨機切分相近；",
    "  但《漢書·藝文志》20 句錯 17 句（85%），說明層累／文類混淆；",
    "  且 W06-015（法言·吾子）與 E11-018（漢書·藝文志）仍共享「詩人之賦麗以則，辭人之賦麗以淫」的引文。",
    "",
]
(OUTPUT / "version_log.md").write_text("\n".join(lines), encoding="utf-8")

# ---------------- leave-author-out counts ----------------
LO_RUNS = [
    ("王充 原版", "leave_author_out_wangchong"),
    ("王充 平衡版", "leave_author_out_wangchong_balanced"),
    ("桓譚 原版", "leave_author_out_huantan"),
    ("桓譚 平衡版", "leave_author_out_huantan_balanced"),
]
lo_rows = []
for label, rel in LO_RUNS:
    path = OUTPUT / rel / "run_metadata.json"
    if not path.exists():
        continue
    meta = json.loads(path.read_text(encoding="utf-8"))
    cm = meta["metrics"]["confusion_matrix"]
    east_hits = cm[1][1]
    n_test = cm[0][0] + cm[0][1] + cm[1][0] + cm[1][1]
    lo_rows.append({
        "run": label,
        "train_west": meta["train_period"].get("西漢", 0),
        "train_east": meta["train_period"].get("東漢", 0),
        "n_train": meta["n_train"],
        "n_test": n_test,
        "east_hits": east_hits,
        "accuracy": meta["metrics"]["accuracy"],
    })
lo = pd.DataFrame(lo_rows)
lo.to_csv(OUTPUT / "leave_author_out_counts.csv", index=False, encoding="utf-8-sig")
lines = [
    "# 留一作者：原版與平衡版",
    "",
    "測試集全為單一作者的東漢篇章；accuracy 即東漢命中率。",
    "",
    "| run | 訓練西漢 | 訓練東漢 | 訓練合計 | 測試東漢 | 東漢命中 | accuracy |",
    "|---|---:|---:|---:|---:|---:|---:|",
]
for _, row in lo.iterrows():
    lines.append(
        f"| {row['run']} | {row['train_west']} | {row['train_east']} | {row['n_train']} | "
        f"{row['n_test']} | {row['east_hits']} | {row['accuracy']:.4f} |")
lines += [
    "",
    "## 解讀",
    "",
    "- 王充留出：訓練集東漢 290／948（少數），`class_weight=balanced` 提高東漢命中，",
    "  由 9/710 升至 176/710。",
    "- 桓譚留出：訓練集東漢 809／1467（多數），`class_weight=balanced` 下調東漢權重，",
    "  東漢命中由 38/62 降至 28/62。",
    "- 兩個方向相反，說明類別比例會改變模型的決策邊界；結果受作者、文類、來源與類別比例影響，",
    "  現有設計難以分離各自的作用。",
    "",
]
(OUTPUT / "leave_author_out_counts.md").write_text("\n".join(lines), encoding="utf-8")
print("wrote selection_basis.md, sufficiency_check.md, version_log.md")
