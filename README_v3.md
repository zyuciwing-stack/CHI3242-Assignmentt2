# v3 修訂（保留 v2）

v3 保留 v2 的資料、程式與結果，只新增：

1. W17〈關尹子書錄〉、W18〈子華子書錄〉移到「歸屬待核」，不進入訓練；原文、舊題作者與文獻理由保留。
2. 補收王褒〈四子講德論〉、劉歆〈移書讓太常博士〉、趙岐〈孟子題辭〉／〈孟子篇敘〉、何休〈春秋公羊經傳解詁序〉。
3. 加做同文類（子書）與四種子書西漢／東漢跨作者配對對照。

完整結果、樣本構成、逐句預測與重跑指令見 [`output/v3/v3_results.md`](output/v3/v3_results.md)；人工抽查清單見 [`output/v3/v3_checklist.md`](output/v3/v3_checklist.md)。

## 最重要數字

- **v3 主實驗**：148/233（0.6352）；多數類基準 127/233（0.5451）；macro F1 0.6161；〈超奇〉56/129 判東漢。
- **同文類對照**：同一批 82 句留出子書，全類訓練 0.6220，子書訓練 0.7195（基準 0.5000）；東漢 recall 0.390→0.732。
- **跨作者配對**：四組都低於當組多數類基準；P1（劉安＋王充）基準 0.8569，全類 0.1976，子書 0.2065。

## 資料與輸出

- `data/v3/dataset_labelonly.csv`：只修正 W17/W18 標籤的樣本。
- `data/v3/dataset_v3.csv`：修正標籤＋補收新作者的樣本。
- `data/v3/sentences_all.csv`：v3 全部候選句與狀態。
- `data/v3/new_materials.csv`：新增篇名、作者、底本、修訂號、全庫／主樣本句數。
- `data/v3/label_fix.csv`：W17/W18 的舊題作者、理由、句數。
- `output/v3/labelonly/`：只修正標籤的對照結果。
- `output/v3/`：v3 主實驗（metrics、test_predictions、independent_predictions、誤判例）。
- `output/v3/genre_experiment/`：留出子書句的全類 vs 子書訓練。
- `output/v3/author_pairings/`：四種跨作者配對。
- `output/v3/norepeat/`：排除 W06-015／E11-018 的對照。
- `output/v3/repeat_quote_positions.csv`：重引例在各切分的位置。

## 最值得寫進論文的三個數字（原文見 v3_results.md 第 8 節）

1. 子書訓練 0.7195 vs 全類訓練 0.6220（82 句留出子書，基準 0.5）；對應 E05-001「世谷所患，患言事增其實；著文垂辭，辭出溢其真……」。
2. P1 跨作者配對基準 0.8569 vs 全類 0.1976；對應 E04-124「然則通人造書，文無暇穢。」
3. v3 主實驗 148/233 vs 多數類 127/233；〈超奇〉56/129；對應 E01-011「夫通覽者，世間比有；著文者，歷世希然。」

`report.md`／`report.pdf` 仍由作者依 `report_outline_v3.md`（v3 數字）與 `report_outline.md`（v2 架構）修訂。
