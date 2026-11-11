# v3 輸出索引

主結果：`v3_results.md`。人工抽查：`v3_checklist.md`。

- `metrics.json`／`test_predictions.csv`／`independent_predictions.csv`：v3 主實驗。
- `labelonly/`：只修正 W17/W18 標籤的對照。
- `grouped/`：v3 同篇不跨切分的對照。
- `genre_experiment/`：留出子書句，全類訓練 vs 子書訓練。
- `author_pairings/`：四種子書西漢／東漢留出配對。
- `norepeat/`：排除 W06-015／E11-018 的對照。
- `new_materials_summary.md`：新增材料與標籤修正摘要。
- `repeat_quote_positions.csv`／`.md`：重引例在各切分的位置。

重跑指令見 `v3_results.md` 第 10 節。
