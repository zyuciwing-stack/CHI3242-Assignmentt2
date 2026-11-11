# output/ 索引

主結果為 v2 主樣本（`data/dataset_v2.csv`）的隨機分層 80/20 切分；主模型 127/202（0.6287），多數類基準 112/202。下列頂層檔案是 `output/v2/` 的副本，方便批改：

- `metrics.json`：準確率、混淆矩陣、兩類精確率／召回率／F1。
- `classification_report.csv`：逐類指標。
- `test_predictions.csv`：202 句測試集的逐句預測與機率。
- `independent_predictions.csv`：〈論衡·超奇〉（同作者留出篇章）129 句的逐句預測。
- `independent_summary.json`：〈超奇〉摘要（主模型 49/129 判為東漢，0.380）。
- `probe_maoshi_predictions.csv`：《毛詩序》27 句的逐句探針預測。
- `probe_maoshi_summary.json`：《毛詩序》探針摘要（40.7% 判為東漢）。
- `misclassified_examples.csv`／`.md`：可回讀的誤判例與相關詞。
- `top_features.csv`：兩類權重最高的 30 個特徵。
- `figures/confusion_matrix.png`、`figures/top_features.png`。
- `model.joblib`：向量器與邏輯迴歸模型。
- `run_metadata.json`：本次 run 的設定、句數與指標。

其他對照：

- `v1/`：第一版核心篇目。
- `full/`：全庫不設篇／作者上限（王充主導，僅作敏感度對照）。
- `grouped/`：同篇不跨訓練／測試；`group_split.csv` 列實際分組。
- `variants/`：balanced、min_df=1、1–2-gram、停用詞等變體。
- `leave_author_out_wangchong/`：訓練不含王充，測試全部王充篇章。
- `leave_author_out_wangchong_balanced/`：同上，加 `class_weight=balanced`；東漢命中 176/710。
- `leave_author_out_huantan/`：訓練不含桓譚，測試全部桓譚篇章（對照）。
- `leave_author_out_huantan_balanced/`：同上，加 `class_weight=balanced`；東漢命中 28/62。
- `leave_author_out_counts.md`／`.csv`：原版與平衡版的訓練兩期句數、測試命中。
- `version_log.md`：所有 run 的資料與結果摘要。
- `sufficiency_check.md`：句數、篇數、來源佔比與達標檢查。
- `error_analysis.md`：按文類、作者、篇章的錯誤率。
- `corpus_summary.md`：v1／v2 語料摘要；`corpus_summary_v1.json`／`corpus_summary_v2.json` 為機器可讀版。
- `reserved_overlap.csv`：〈超奇〉與訓練／測試材料的重文檢查。
