# -*- coding: utf-8 -*-
"""Generate v3 results, checklist, and README from the run outputs."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "v3"
OUT = ROOT / "output" / "v3"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fmt_pct(x):
    return f"{x*100:.1f}%"


def cm_table(cm):
    return (f"[[{cm[0][0]}, {cm[0][1]}], "
            f"[{cm[1][0]}, {cm[1][1]}]]")


def metrics_row(name, m, n_test_override=None):
    n = n_test_override if n_test_override else sum(m["support"].values())
    acc_hits = round(m["accuracy"] * n)
    return (f"| {name} | {n} | {m['support'].get('西漢', 0)} | "
            f"{m['support'].get('東漢', 0)} | {m['majority_class']} "
            f"{m['majority_baseline']:.4f} | {acc_hits}/{n} | {m['accuracy']:.4f} | "
            f"{m['macro_f1']:.4f} | {m['confusion_matrix']} | "
            f"{m['recall']['西漢']:.3f} | {m['recall']['東漢']:.3f} |")


def main():
    v2 = load_json(ROOT / "output" / "metrics.json")
    v2["majority_baseline"] = 112 / 202
    v2["majority_class"] = "西漢"
    v2["support"] = {"西漢": 112, "東漢": 90}
    label = load_json(OUT / "labelonly" / "metrics.json")
    mainm = load_json(OUT / "metrics.json")
    grouped = load_json(OUT / "grouped" / "metrics.json")
    norep = load_json(OUT / "norepeat" / "metrics.json")

    v2_chao = round(load_json(ROOT / "output" / "independent_summary.json")["accuracy"] * 129)
    label_chao = round(load_json(OUT / "labelonly" / "independent_summary.json")["accuracy"] * 129)
    main_chao = round(load_json(OUT / "independent_summary.json")["accuracy"] * 129)
    grouped_chao = round(load_json(OUT / "grouped" / "independent_summary.json")["accuracy"] * 129)
    norep_chao = round(load_json(OUT / "norepeat" / "independent_summary.json")["accuracy"] * 129)

    new = pd.read_csv(DATA / "new_materials.csv", encoding="utf-8-sig")
    fix = pd.read_csv(DATA / "label_fix.csv", encoding="utf-8-sig")
    v3df = pd.read_csv(DATA / "dataset_v3.csv", encoding="utf-8-sig")
    new_ids = new["work_id"].tolist()
    new_train = int(((v3df["work_id"].isin(new_ids)) & (v3df["split"] == "train")).sum())
    new_test = int(((v3df["work_id"].isin(new_ids)) & (v3df["split"] == "test")).sum())
    genre_full = load_json(OUT / "genre_experiment" / "metrics_full_class.json")
    genre_zip = load_json(OUT / "genre_experiment" / "metrics_zip_only.json")
    pairs = pd.read_csv(OUT / "author_pairings" / "summary.csv", encoding="utf-8-sig")
    quote_pos = pd.read_csv(OUT / "repeat_quote_positions.csv", encoding="utf-8-sig")

    lines = [
        "# v3 結果與交付說明",
        "",
        "v3 保留 v2 的資料、程式與結果，新增兩件事：",
        "（1）W17〈關尹子書錄〉、W18〈子華子書錄〉移到「歸屬待核」，",
        "（2）補收王褒、劉歆、趙岐、何休四位作者。",
        "另外加做同文類（子書）與四種跨作者配對對照。",
        "",
        "## 1. 最重要數字",
        "",
        f"- **主實驗 v3**：{round(mainm['accuracy']*sum(mainm['support'].values()))}/"
        f"{sum(mainm['support'].values())}（{mainm['accuracy']:.4f}），"
        f"多數類基準 {mainm['support'][mainm['majority_class']]}/"
        f"{sum(mainm['support'].values())}（{mainm['majority_baseline']:.4f}）；"
        f"macro F1 {mainm['macro_f1']:.4f}；〈超奇〉{main_chao}/129 判東漢。",
        f"- **同文類對照**：同一批 82 句留出子書，全類訓練 acc {genre_full['accuracy']:.4f}、"
        f"子書訓練 acc {genre_zip['accuracy']:.4f}（基準 0.5000）；"
        f"子書訓練的東漢 recall {genre_zip['recall']['東漢']:.3f}，全類訓練僅 "
        f"{genre_full['recall']['東漢']:.3f}。",
        f"- **跨作者配對**：四組全部低於當組多數類基準；例如 P1（留出劉安＋王充）"
        f"基準 {pairs.iloc[0]['baseline']:.4f}，全類訓練 acc {pairs.iloc[0]['full_acc']:.4f}、"
        f"子書訓練 acc {pairs.iloc[0]['zip_acc']:.4f}。",
        "",
        "## 2. 樣本構成",
        "",
        "| 版本 | 全庫句數 | 西漢 | 東漢 | 篇數 | 作者數 | 主樣本 | 訓練 | 測試 | 測試西漢 | 測試東漢 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, summary_file, sample_file in [
        ("v2", ROOT / "output" / "corpus_summary_v2.json", ROOT / "data" / "dataset_v2.csv"),
        ("v3 label-only", OUT / "corpus_summary_labelonly.json", DATA / "dataset_labelonly.csv"),
        ("v3 main", OUT / "corpus_summary_v3.json", DATA / "dataset_v3.csv"),
    ]:
        s = load_json(summary_file)
        sample = pd.read_csv(sample_file, encoding="utf-8-sig")
        ms = s["main_sample"]
        test = sample[sample["split"] == "test"]
        lines.append(
            f"| {name} | {s['total']} | {s['by_period']['西漢']['sentences']} | "
            f"{s['by_period']['東漢']['sentences']} | {ms['works']} | {ms['authors']} | "
            f"{ms['total']} | {ms['by_split'].get('train', 0)} | {ms['by_split'].get('test', 0)} | "
            f"{(test['period'] == '西漢').sum()} | {(test['period'] == '東漢').sum()} |")
    lines += [
        "",
        "測試集並非同一批：v2 與 v3 label-only 的測試集只重疊 177/202；"
        "v3 label-only 與 v3 main 只重疊 37（v3 main 測試 233）。"
        "因此跨版本成績只能描述性比較，不能當成配對檢定。",
        "",
        "測試集來源：v2 取 `data/dataset_v2.csv` 的 `split=test`；"
        "v3 label-only 取 `data/v3/dataset_labelonly.csv` 的 `split=test`；"
        "v3 main 取 `data/v3/dataset_v3.csv` 的 `split=test`。",
        "",
        "## 3. 標籤修正與新增材料",
        "",
        "### 3.1 W17／W18 歸屬待核",
        "",
        "| 篇名 | 舊題作者 | v2 分期 | v3 狀態 | 句數 | 理由 |",
        "|---|---|---|---|---:|---|",
    ]
    for _, row in fix.iterrows():
        lines.append(
            f"| {row['work_title']} | {row['author_old']} | {row['period_old']} | "
            f"{row['status_v3']} | {row['sentences']} | {row['reason']} |")
    lines += [
        "",
        "W17/W18 共 32 句；其中 29 句原在可用全庫（2 句重複、1 句過短），"
        "移除後西漢全庫 658→629。v3 label-only 主樣本仍是 1,009 句，"
        "但組成與測試集已改變（與 v2 測試集重疊 177/202）。",
        "",
        "### 3.2 新增作者與篇章",
        "",
        f"新增作者 **{new['author'].nunique()}** 位：{'、'.join(new['author'].drop_duplicates())}；"
        f"新增篇目 {len(new)} 篇，全庫 {int(new['full_sentences'].sum())} 句，"
        f"主樣本實際納入 **{int(new['main_sample_sentences'].sum())}** 句（全部進入）；"
        f"其中 {new_train} 句在訓練、{new_test} 句在測試（v3 main 測試 233 句的 {new_test/233:.1%}）。",
        "",
        "| 篇名 | 作者 | 分期 | 文類 | 底本 | 修訂號 | 全庫句數 | 主樣本句數 |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for _, row in new.iterrows():
        lines.append(
            f"| {row['work_title']} | {row['author']} | {row['period']} | {row['genre']} | "
            f"{row['base_page']} | {row['base_revision']} | {row['full_sentences']} | "
            f"{row['main_sample_sentences']} |")
    lines += [
        "",
        "節選：王褒取序文與論詩歌賦頌的連續段落（paragraphs 0、2）；"
        "劉歆、趙岐〈孟子題辭〉〈孟子篇敘〉、何休序全篇納入。"
        "〈超奇〉仍整篇留出；《毛詩序》仍歸屬未定。",
        "",
        "## 4. 主實驗成績",
        "",
        "| 版本 | 測試句數 | 西漢 | 東漢 | 多數類基準 | 命中 | accuracy | macro F1 | 混淆矩陣 | 西漢 recall | 東漢 recall |",
        "|---|---:|---:|---:|---|---:|---:|---:|---|---:|---:|",
        metrics_row("v2（對照）", v2),
        metrics_row("v3 label-only", label),
        metrics_row("v3 main", mainm),
        metrics_row("v3 grouped", grouped),
        "",
        "逐類指標：",
        "",
        "| 版本 | 類別 | 精確率 | 召回率 | F1 | 支持數 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for version_name, m in [("v2", v2), ("v3 label-only", label), ("v3 main", mainm)]:
        for name in ["西漢", "東漢"]:
            lines.append(
                f"| {version_name} | {name} | {m['precision'][name]:.3f} | "
                f"{m['recall'][name]:.3f} | {m['f1'][name]:.3f} | {m['support'][name]} |")
    lines += [
        "",
        f"〈超奇〉（同作者留出篇章，129 句）：v2 {v2_chao}/129、"
        f"v3 label-only {label_chao}/129、v3 main {main_chao}/129、"
        f"v3 grouped {grouped_chao}/129、v3 no-repeat {norep_chao}/129 判為東漢。",
        "",
        "## 5. 同文類對照（留出子書句）",
        "",
        "取自 v3 主樣本 `data/v3/dataset_v3.csv` 的測試集，"
        "同一批 82 句子書（西漢 41／東漢 41，基準 0.5000）：",
        "",
        "| 訓練 | 訓練句數 | 訓練西漢 | 訓練東漢 | accuracy | macro F1 | 東漢 recall | 混淆矩陣 |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name, m in [("全類訓練", genre_full), ("子書訓練", genre_zip)]:
        lines.append(
            f"| {name} | {m['n_train']} | {m['train_period'].get('西漢', 0)} | "
            f"{m['train_period'].get('東漢', 0)} | {m['accuracy']:.4f} | {m['macro_f1']:.4f} | "
            f"{m['recall']['東漢']:.3f} | {m['confusion_matrix']} |")
    lines += [
        "",
        "子書訓練在同一批留出子書上明顯較好，且東漢 recall 由 0.390 升至 0.732；"
        "這與文類匹配有關，但全類訓練同時改變了文類組成與類別比例，"
        "現有設計難以分離兩者。",
        "",
        "## 6. 四種子書跨作者配對",
        "",
        "以下配對使用 v3 全庫（`data/v3/sentences_all.csv`，去重後可訓練句，"
        "不設篇／作者上限），以確保每組有足夠訓練句；這與第 4 節主樣本的上限不同。"
        "每組訓練與測試作者不重疊；測試作者在四組中重複使用，分開報告。"
        "測試不含〈超奇〉（E01 仍整篇留出）。",
        "",
        "| pair | 西漢測試作者 | 東漢測試作者 | 測試句數 | 西漢 | 東漢 | 當組基準 | 全類 n | 子書 n | 全類 acc | 全類 macro F1 | 子書 acc | 子書 macro F1 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in pairs.iterrows():
        lines.append(
            f"| {row['pair']} | {row['west_author']} | {row['east_author']} | "
            f"{row['test_sentences']} | {row['test_west']} | {row['test_east']} | "
            f"{row['baseline_class']} {row['baseline']:.4f} | {row['train_full']} | "
            f"{row['train_zip']} | {row['full_acc']:.4f} | {row['full_macro_f1']:.4f} | "
            f"{row['zip_acc']:.4f} | {row['zip_macro_f1']:.4f} |")
    lines += [
        "",
        "四組都低於當組多數類基準。P1/P3 的訓練集缺王充且西漢較多，模型偏向西漢，"
        "王充的東漢 recall 只有 0.086/0.115；P2/P4 的訓練集含王充且東漢較多，模型偏向東漢，"
        "劉安/揚雄的西漢 recall 只有 0.227/0.110。子書訓練只在 P1/P3 略升，"
        "在 P2/P4 反而更差；這說明類別比例與作者詞彙共同作用，"
        "不能把任何單一訓練策略當成萬靈丹。",
        "",
        "各組混淆矩陣與 recall：",
        "",
        "| pair | 全類混淆 | 子書混淆 | 全類西漢 recall | 全類東漢 recall | 子書西漢 recall | 子書東漢 recall |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for _, row in pairs.iterrows():
        full = load_json(OUT / "author_pairings" / row["pair"] / "metrics_full_class.json")
        zipm = load_json(OUT / "author_pairings" / row["pair"] / "metrics_zip_only.json")
        lines.append(
            f"| {row['pair']} | {full['confusion_matrix']} | {zipm['confusion_matrix']} | "
            f"{full['recall']['西漢']:.3f} | {full['recall']['東漢']:.3f} | "
            f"{zipm['recall']['西漢']:.3f} | {zipm['recall']['東漢']:.3f} |")
    lines += [
        "## 7. 重引例 W06-015／E11-018",
        "",
        "共享引文：「詩人之賦麗以則，辭人之賦麗以淫」。",
        "",
        "| split | sent_id | 位置 |",
        "|---|---|---|",
    ]
    for _, row in quote_pos.iterrows():
        lines.append(f"| {row['split']} | {row['sent_id']} | {row['position']} |")
    lines += [
        "",
        "v2 grouped 是 W06 在訓練、E11 在測試，才是重引跨切分的實例；"
        "v3 main 與 v3 grouped 兩者都在訓練，v2 main 與 v3 label-only 兩者都在測試。",
        "",
        "排除重引對照：規則為刪除 `W06-015`、`E11-018` 兩句（都在 v3 main 訓練集，"
        "測試集不變 233 句）；acc {:.4f}→{:.4f}，macro F1 {:.4f}→{:.4f}，"
        "東漢 recall {:.3f}→{:.3f}。差異很小，重引不是主要因素。".format(
            mainm["accuracy"], norep["accuracy"],
            mainm["macro_f1"], norep["macro_f1"],
            mainm["recall"]["東漢"], norep["recall"]["東漢"]),
        "",
        "## 8. 最值得寫進論文的數字與原文",
        "",
        "### 8.1 子書訓練 vs 全類訓練（同文類對照）",
        "",
        f"同一批 82 句子書：全類訓練 {genre_full['accuracy']:.4f}，子書訓練 "
        f"{genre_zip['accuracy']:.4f}；東漢 recall {genre_full['recall']['東漢']:.3f}→"
        f"{genre_zip['recall']['東漢']:.3f}。",
        "",
        "對應原文（E05-001，論衡·藝增，東漢；全類訓練判西漢 P(東漢)=0.410，"
        "子書訓練判東漢 P=0.526）：",
        "",
        "> 世谷所患，患言事增其實；著文垂辭，辭出溢其真，稱美過其善，進惡沒其罪。",
        "",
        "### 8.2 跨作者配對 P1（留出劉安＋王充）",
        "",
        f"當組基準 {pairs.iloc[0]['baseline']:.4f}（全判東漢），全類訓練 "
        f"{pairs.iloc[0]['full_acc']:.4f}，子書訓練 {pairs.iloc[0]['zip_acc']:.4f}。",
        "",
        "對應原文（E04-124，論衡·自紀，東漢；P1 全類訓練判西漢 P(東漢)=0.142）：",
        "",
        "> 然則通人造書，文無暇穢。",
        "",
        "### 8.3 主實驗 v3 與〈超奇〉",
        "",
        f"v3 main {round(mainm['accuracy']*233)}/233（{mainm['accuracy']:.4f}），"
        f"多數類基準 127/233（{mainm['majority_baseline']:.4f}），只多 "
        f"{round(mainm['accuracy']*233)-127} 句；〈超奇〉{main_chao}/129 判東漢。",
        "",
        "對應原文（E01-011，論衡·超奇，東漢；主模型判西漢 P(東漢)=0.294）：",
        "",
        "> 夫通覽者，世間比有；著文者，歷世希然。",
        "",
        "## 9. 可引用檔案",
        "",
        "- v3 資料：`data/v3/sentences_all.csv`、`data/v3/dataset_labelonly.csv`、`data/v3/dataset_v3.csv`、`data/v3/train.csv`、`data/v3/test.csv`。",
        "- 標籤修正：`data/v3/label_fix.csv`、`data/v3/uncertain_attribution.csv`。",
        "- 新增材料：`data/v3/new_materials.csv`、`output/v3/new_materials_summary.md`。",
        "- 主實驗：`output/v3/metrics.json`、`output/v3/test_predictions.csv`、`output/v3/independent_predictions.csv`、`output/v3/misclassified_examples.csv`／`.md`。",
        "- label-only：`output/v3/labelonly/`。",
        "- 同文類：`output/v3/genre_experiment/`。",
        "- 跨作者：`output/v3/author_pairings/`。",
        "- 重引位置：`output/v3/repeat_quote_positions.csv`／`.md`。",
        "- 無重引對照：`output/v3/norepeat/`。",
        "- 分組切分：`output/v3/grouped/`。",
        "",
        "## 10. 重跑指令",
        "",
        "```powershell",
        "python scripts/prepare_v3_raw.py",
        "python scripts/build_corpus_v3.py",
        "python scripts/train_model.py --dataset data/v3/dataset_labelonly.csv --sentences-path data/v3/sentences_all.csv --output-dir output/v3/labelonly --run-name v3_labelonly",
        "python scripts/train_model.py --dataset data/v3/dataset_v3.csv --sentences-path data/v3/sentences_all.csv --output-dir output/v3 --run-name v3_main",
        "python scripts/train_model.py --dataset data/v3/dataset_v3.csv --sentences-path data/v3/sentences_all.csv --grouped --output-dir output/v3/grouped --run-name v3_grouped",
        "python scripts/v3_genre_experiment.py",
        "python scripts/v3_author_pairings.py",
        "python scripts/v3_repeat_quote.py",
        "python scripts/v3_make_norepeat.py",
        "python scripts/train_model.py --dataset data/v3/dataset_v3_norepeat.csv --sentences-path data/v3/sentences_all.csv --output-dir output/v3/norepeat --run-name v3_norepeat",
        "python scripts/v3_make_results.py",
        "```",
        "",
    ]
    (OUT / "v3_results.md").write_text("\n".join(lines), encoding="utf-8")

    # checklist
    checklist = [
        "# v3 人工抽查清單",
        "",
        "## A. 兩篇待核書錄",
        "",
        "- [ ] W17〈關尹子書錄〉：舊題劉向、原文 13 句；確認仍保留原文，但 `period=歸屬待核`、`status=uncertain_attribution`。",
        "- [ ] W18〈子華子書錄〉：舊題劉向、原文 19 句；確認仍保留原文，但 `period=歸屬待核`、`status=uncertain_attribution`。",
        "- [ ] 抽查 `data/v3/uncertain_attribution.csv` 的句子是否與 `data/raw/quanhan_037.txt` 一致。",
        "",
        "## B. 新增篇章",
        "",
        "- [ ] 王褒〈四子講德論〉：`全漢文/卷四十二`，節選 paragraphs 0、2；34 句。",
        "- [ ] 劉歆〈移書讓太常博士〉：`全漢文/卷四十`，全篇；39 句。",
        "- [ ] 趙岐〈孟子題辭〉：`全後漢文/卷六十二`；53 句。",
        "- [ ] 趙岐〈孟子篇敘〉：同卷；18 句。",
        "- [ ] 何休〈春秋公羊經傳解詁序〉：`全後漢文/卷六十八`；10 句。",
        "- [ ] 抽查 `data/v3/new_materials.csv` 的底本頁面、修訂號、節選範圍與句數。",
        "",
        "## C. 句界與引號",
        "",
        "- [ ] 抽查王褒段落中的長對話，確認句號切分沒有把「曰：」片段切得太碎。",
        "- [ ] 抽查趙岐〈孟子題辭〉的長段落，確認句號、問號、感嘆號切分。",
        "- [ ] 抽查何休序的「〈唐石經本。〉」已刪除，未進入句子。",
        "- [ ] 抽查`text_normalized` 只統一異體字、移除引號，沒有改動原句。",
        "",
        "## D. 重引例",
        "",
        "- [ ] 確認 `W06-015` 與 `E11-018` 共享「詩人之賦麗以則，辭人之賦麗以淫」。",
        "- [ ] 檢查 `output/v3/repeat_quote_positions.csv`：v2 grouped 是 W06 訓練／E11 測試；v3 main 兩者都在訓練。",
        "- [ ] 檢查無重引對照：只刪 2 句（都在訓練），測試 233 句不變。",
        "",
        "## E. 切分與上限",
        "",
        "- [ ] `data/v3/dataset_v3.csv`：每篇 ≤80 句、每作者 ≤160 句，種子 42，80/20 分層。",
        "- [ ] `data/v3/dataset_labelonly.csv`：W17/W18 不在訓練，其他與 v2 規則相同。",
        "- [ ] `output/v3/author_pairings/P*/split_info.json`：訓練與測試作者不重疊。",
        "",
    ]
    (OUT / "v3_checklist.md").write_text("\n".join(checklist), encoding="utf-8")

    # README index
    readme = [
        "# v3 輸出索引",
        "",
        "主結果：`v3_results.md`。人工抽查：`v3_checklist.md`。",
        "",
        "- `metrics.json`／`test_predictions.csv`／`independent_predictions.csv`：v3 主實驗。",
        "- `labelonly/`：只修正 W17/W18 標籤的對照。",
        "- `grouped/`：v3 同篇不跨切分的對照。",
        "- `genre_experiment/`：留出子書句，全類訓練 vs 子書訓練。",
        "- `author_pairings/`：四種子書西漢／東漢留出配對。",
        "- `norepeat/`：排除 W06-015／E11-018 的對照。",
        "- `new_materials_summary.md`：新增材料與標籤修正摘要。",
        "- `repeat_quote_positions.csv`／`.md`：重引例在各切分的位置。",
        "",
        "重跑指令見 `v3_results.md` 第 10 節。",
        "",
    ]
    (OUT / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print("wrote v3_results.md, v3_checklist.md, output/v3/README.md")


if __name__ == "__main__":
    main()
