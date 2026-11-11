# v3 結果與交付說明

v3 保留 v2 的資料、程式與結果，新增兩件事：
（1）W17〈關尹子書錄〉、W18〈子華子書錄〉移到「歸屬待核」，
（2）補收王褒、劉歆、趙岐、何休四位作者。
另外加做同文類（子書）與四種跨作者配對對照。

## 1. 最重要數字

- **主實驗 v3**：148/233（0.6352），多數類基準 127/233（0.5451）；macro F1 0.6161；〈超奇〉56/129 判東漢。
- **同文類對照**：同一批 82 句留出子書，全類訓練 acc 0.6220、子書訓練 acc 0.7195（基準 0.5000）；子書訓練的東漢 recall 0.732，全類訓練僅 0.390。
- **跨作者配對**：四組全部低於當組多數類基準；例如 P1（留出劉安＋王充）基準 0.8569，全類訓練 acc 0.1976、子書訓練 acc 0.2065。

## 2. 樣本構成

| 版本 | 全庫句數 | 西漢 | 東漢 | 篇數 | 作者數 | 主樣本 | 訓練 | 測試 | 測試西漢 | 測試東漢 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v2 | 1529 | 658 | 871 | 49 | 11 | 1009 | 807 | 202 | 112 | 90 |
| v3 label-only | 1500 | 629 | 871 | 47 | 11 | 1009 | 807 | 202 | 112 | 90 |
| v3 main | 1654 | 702 | 952 | 52 | 15 | 1163 | 930 | 233 | 127 | 106 |

測試集並非同一批：v2 與 v3 label-only 的測試集只重疊 177/202；v3 label-only 與 v3 main 只重疊 37（v3 main 測試 233）。因此跨版本成績只能描述性比較，不能當成配對檢定。

測試集來源：v2 取 `data/dataset_v2.csv` 的 `split=test`；v3 label-only 取 `data/v3/dataset_labelonly.csv` 的 `split=test`；v3 main 取 `data/v3/dataset_v3.csv` 的 `split=test`。

## 3. 標籤修正與新增材料

### 3.1 W17／W18 歸屬待核

| 篇名 | 舊題作者 | v2 分期 | v3 狀態 | 句數 | 理由 |
|---|---|---|---|---:|---|
| 關尹子書錄 | 劉向 | 西漢（v2） | 歸屬待核，不作訓練 | 13 | 舊題劉向；《關尹子》成書年代與劉向敘錄的歸屬有爭議，列「歸屬待核」，不納入訓練。保留原文與舊題作者。 |
| 子華子書錄 | 劉向 | 西漢（v2） | 歸屬待核，不作訓練 | 19 | 舊題劉向；《子華子》成書年代與劉向敘錄的歸屬有爭議，列「歸屬待核」，不納入訓練。保留原文與舊題作者。 |

W17/W18 共 32 句；其中 29 句原在可用全庫（2 句重複、1 句過短），移除後西漢全庫 658→629。v3 label-only 主樣本仍是 1,009 句，但組成與測試集已改變（與 v2 測試集重疊 177/202）。

### 3.2 新增作者與篇章

新增作者 **4** 位：王褒、劉歆、趙岐、何休；新增篇目 5 篇，全庫 154 句，主樣本實際納入 **154** 句（全部進入）；其中 121 句在訓練、33 句在測試（v3 main 測試 233 句的 14.2%）。

| 篇名 | 作者 | 分期 | 文類 | 底本 | 修訂號 | 全庫句數 | 主樣本句數 |
|---|---|---|---|---|---|---:|---:|
| 四子講德論（節選） | 王褒 | 西漢 | 論·詩歌功用 | 全漢文/卷四十二 | 2299588 | 34 | 34 |
| 移書讓太常博士（節選） | 劉歆 | 西漢 | 書信·經學論 | 全漢文/卷四十 | 2300175 | 39 | 39 |
| 孟子題辭 | 趙岐 | 東漢 | 經解序·孟子學 | 全後漢文/卷六十二 | 2584229 | 53 | 53 |
| 孟子篇敘 | 趙岐 | 東漢 | 經解序·孟子學 | 全後漢文/卷六十二 | 2584229 | 18 | 18 |
| 春秋公羊經傳解詁序 | 何休 | 東漢 | 經解序·春秋學 | 全後漢文/卷六十八 | 2584236 | 10 | 10 |

節選：王褒取序文與論詩歌賦頌的連續段落（paragraphs 0、2）；劉歆、趙岐〈孟子題辭〉〈孟子篇敘〉、何休序全篇納入。〈超奇〉仍整篇留出；《毛詩序》仍歸屬未定。

## 4. 主實驗成績

| 版本 | 測試句數 | 西漢 | 東漢 | 多數類基準 | 命中 | accuracy | macro F1 | 混淆矩陣 | 西漢 recall | 東漢 recall |
|---|---:|---:|---:|---|---:|---:|---:|---|---:|---:|
| v2（對照） | 202 | 112 | 90 | 西漢 0.5545 | 127/202 | 0.6287 | 0.6034 | [[89, 23], [52, 38]] | 0.795 | 0.422 |
| v3 label-only | 202 | 112 | 90 | 西漢 0.5545 | 126/202 | 0.6238 | 0.5874 | [[93, 19], [57, 33]] | 0.830 | 0.367 |
| v3 main | 233 | 127 | 106 | 西漢 0.5451 | 148/233 | 0.6352 | 0.6161 | [[100, 27], [58, 48]] | 0.787 | 0.453 |
| v3 grouped | 238 | 122 | 116 | 西漢 0.5126 | 136/238 | 0.5714 | 0.5645 | [[83, 39], [63, 53]] | 0.680 | 0.457 |

逐類指標：

| 版本 | 類別 | 精確率 | 召回率 | F1 | 支持數 |
|---|---|---:|---:|---:|---:|
| v2 | 西漢 | 0.631 | 0.795 | 0.704 | 112 |
| v2 | 東漢 | 0.623 | 0.422 | 0.503 | 90 |
| v3 label-only | 西漢 | 0.620 | 0.830 | 0.710 | 112 |
| v3 label-only | 東漢 | 0.635 | 0.367 | 0.465 | 90 |
| v3 main | 西漢 | 0.633 | 0.787 | 0.702 | 127 |
| v3 main | 東漢 | 0.640 | 0.453 | 0.530 | 106 |

〈超奇〉（同作者留出篇章，129 句）：v2 49/129、v3 label-only 49/129、v3 main 56/129、v3 grouped 68/129、v3 no-repeat 56/129 判為東漢。

## 5. 同文類對照（留出子書句）

取自 v3 主樣本 `data/v3/dataset_v3.csv` 的測試集，同一批 82 句子書（西漢 41／東漢 41，基準 0.5000）：

| 訓練 | 訓練句數 | 訓練西漢 | 訓練東漢 | accuracy | macro F1 | 東漢 recall | 混淆矩陣 |
|---|---:|---:|---:|---:|---:|---:|---|
| 全類訓練 | 930 | 505 | 425 | 0.6220 | 0.6005 | 0.390 | [[35, 6], [25, 16]] |
| 子書訓練 | 338 | 157 | 181 | 0.7195 | 0.7195 | 0.732 | [[29, 12], [11, 30]] |

子書訓練在同一批留出子書上明顯較好，且東漢 recall 由 0.390 升至 0.732；這與文類匹配有關，但全類訓練同時改變了文類組成與類別比例，現有設計難以分離兩者。

## 6. 四種子書跨作者配對

以下配對使用 v3 全庫（`data/v3/sentences_all.csv`，去重後可訓練句，不設篇／作者上限），以確保每組有足夠訓練句；這與第 4 節主樣本的上限不同。每組訓練與測試作者不重疊；測試作者在四組中重複使用，分開報告。測試不含〈超奇〉（E01 仍整篇留出）。

| pair | 西漢測試作者 | 東漢測試作者 | 測試句數 | 西漢 | 東漢 | 當組基準 | 全類 n | 子書 n | 全類 acc | 全類 macro F1 | 子書 acc | 子書 macro F1 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P1_liuan_wangchong | 劉安 | 王充 | 678 | 97 | 581 | 東漢 0.8569 | 976 | 180 | 0.1976 | 0.1956 | 0.2065 | 0.2058 |
| P2_liuan_huantan | 劉安 | 桓譚 | 159 | 97 | 62 | 西漢 0.6101 | 1495 | 699 | 0.4465 | 0.4301 | 0.3899 | 0.2886 |
| P3_yangxiong_wangchong | 揚雄 | 王充 | 699 | 118 | 581 | 東漢 0.8312 | 955 | 159 | 0.2403 | 0.2385 | 0.2690 | 0.2684 |
| P4_yangxiong_huantan | 揚雄 | 桓譚 | 180 | 118 | 62 | 西漢 0.6556 | 1474 | 678 | 0.3667 | 0.3338 | 0.3500 | 0.2718 |

四組都低於當組多數類基準。P1/P3 的訓練集缺王充且西漢較多，模型偏向西漢，王充的東漢 recall 只有 0.086/0.115；P2/P4 的訓練集含王充且東漢較多，模型偏向東漢，劉安/揚雄的西漢 recall 只有 0.227/0.110。子書訓練只在 P1/P3 略升，在 P2/P4 反而更差；這說明類別比例與作者詞彙共同作用，不能把任何單一訓練策略當成萬靈丹。

各組混淆矩陣與 recall：

| pair | 全類混淆 | 子書混淆 | 全類西漢 recall | 全類東漢 recall | 子書西漢 recall | 子書東漢 recall |
|---|---|---|---:|---:|---:|---:|
| P1_liuan_wangchong | [[84, 13], [531, 50]] | [[80, 17], [521, 60]] | 0.866 | 0.086 | 0.825 | 0.103 |
| P2_liuan_huantan | [[22, 75], [13, 49]] | [[1, 96], [1, 61]] | 0.227 | 0.790 | 0.010 | 0.984 |
| P3_yangxiong_wangchong | [[101, 17], [514, 67]] | [[84, 34], [477, 104]] | 0.856 | 0.115 | 0.712 | 0.179 |
| P4_yangxiong_huantan | [[13, 105], [9, 53]] | [[2, 116], [1, 61]] | 0.110 | 0.855 | 0.017 | 0.984 |
## 7. 重引例 W06-015／E11-018

共享引文：「詩人之賦麗以則，辭人之賦麗以淫」。

| split | sent_id | 位置 |
|---|---|---|
| v2_main | W06-015 | test |
| v2_main | E11-018 | test |
| v2_grouped | W06-015 | train |
| v2_grouped | E11-018 | test |
| v3_labelonly | W06-015 | test |
| v3_labelonly | E11-018 | test |
| v3_main | W06-015 | train |
| v3_main | E11-018 | train |
| v3_grouped | W06-015 | train |
| v3_grouped | E11-018 | train |
| v3_genre_experiment | W06-015 | train（子書 held-out 以此 split 為準） |
| v3_genre_experiment | E11-018 | not in 子書 test（史書） |
| v3_P1_liuan_wangchong | W06-015 | train |
| v3_P1_liuan_wangchong | E11-018 | train |
| v3_P2_liuan_huantan | W06-015 | train |
| v3_P2_liuan_huantan | E11-018 | train |
| v3_P3_yangxiong_wangchong | W06-015 | test |
| v3_P3_yangxiong_wangchong | E11-018 | train |
| v3_P4_yangxiong_huantan | W06-015 | test |
| v3_P4_yangxiong_huantan | E11-018 | train |

v2 grouped 是 W06 在訓練、E11 在測試，才是重引跨切分的實例；v3 main 與 v3 grouped 兩者都在訓練，v2 main 與 v3 label-only 兩者都在測試。

排除重引對照：規則為刪除 `W06-015`、`E11-018` 兩句（都在 v3 main 訓練集，測試集不變 233 句）；acc 0.6352→0.6395，macro F1 0.6161→0.6213，東漢 recall 0.453→0.462。差異很小，重引不是主要因素。

## 8. 最值得寫進論文的數字與原文

### 8.1 子書訓練 vs 全類訓練（同文類對照）

同一批 82 句子書：全類訓練 0.6220，子書訓練 0.7195；東漢 recall 0.390→0.732。

對應原文（E05-001，論衡·藝增，東漢；全類訓練判西漢 P(東漢)=0.410，子書訓練判東漢 P=0.526）：

> 世谷所患，患言事增其實；著文垂辭，辭出溢其真，稱美過其善，進惡沒其罪。

### 8.2 跨作者配對 P1（留出劉安＋王充）

當組基準 0.8569（全判東漢），全類訓練 0.1976，子書訓練 0.2065。

對應原文（E04-124，論衡·自紀，東漢；P1 全類訓練判西漢 P(東漢)=0.142）：

> 然則通人造書，文無暇穢。

### 8.3 主實驗 v3 與〈超奇〉

v3 main 148/233（0.6352），多數類基準 127/233（0.5451），只多 21 句；〈超奇〉56/129 判東漢。

對應原文（E01-011，論衡·超奇，東漢；主模型判西漢 P(東漢)=0.294）：

> 夫通覽者，世間比有；著文者，歷世希然。

## 9. 可引用檔案

- v3 資料：`data/v3/sentences_all.csv`、`data/v3/dataset_labelonly.csv`、`data/v3/dataset_v3.csv`、`data/v3/train.csv`、`data/v3/test.csv`。
- 標籤修正：`data/v3/label_fix.csv`、`data/v3/uncertain_attribution.csv`。
- 新增材料：`data/v3/new_materials.csv`、`output/v3/new_materials_summary.md`。
- 主實驗：`output/v3/metrics.json`、`output/v3/test_predictions.csv`、`output/v3/independent_predictions.csv`、`output/v3/misclassified_examples.csv`／`.md`。
- label-only：`output/v3/labelonly/`。
- 同文類：`output/v3/genre_experiment/`。
- 跨作者：`output/v3/author_pairings/`。
- 重引位置：`output/v3/repeat_quote_positions.csv`／`.md`。
- 無重引對照：`output/v3/norepeat/`。
- 分組切分：`output/v3/grouped/`。

## 10. 重跑指令

```powershell
python scripts/prepare_v3_raw.py
python scripts/build_corpus_v3.py
python scripts/train_model.py --dataset data/v3/dataset_labelonly.csv --sentences-path data/v3/sentences_all.csv --output-dir output/v3/labelonly --run-name v3_labelonly
python scripts/train_model.py --dataset data/v3/dataset_v3.csv --sentences-path data/v3/sentences_all.csv --output-dir output/v3 --run-name v3_main
python scripts/train_model.py --dataset data/v3/dataset_v3.csv --sentences-path data/v3/sentences_all.csv --grouped --output-dir output/v3/grouped --run-name v3_grouped
python scripts/v3_genre_experiment.py
python scripts/v3_author_pairings.py
python scripts/v3_repeat_quote.py
python scripts/v3_make_norepeat.py
python scripts/train_model.py --dataset data/v3/dataset_v3_norepeat.csv --sentences-path data/v3/sentences_all.csv --output-dir output/v3/norepeat --run-name v3_norepeat
python scripts/v3_make_results.py
```
