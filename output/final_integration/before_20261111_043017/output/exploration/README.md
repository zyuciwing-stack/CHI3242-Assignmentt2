# 兩漢文論互動探索分析

入口：`output/exploration/index.html`。單一 HTML，內嵌 Plotly 與資料，可直接雙擊、離線開啟，不依賴 CDN。

## 這是什麼

以 v3 可建模全庫的 **52 篇作品／節選**（1,654 句；西漢 702、東漢 952）為參照，建立篇章層級的高頻詞表示：

- 100 個與 50 個高頻 unigram（qhchina `Stylometry`，`transform='zscore'`、`distance='cosine'`、`mode='instance'`）。
- 相對頻率 = 該詞次數／該篇總詞數；z-score 以 52 篇的 mean／std（ddof=0）標準化。
- 3 個主成分的 PCA（sklearn，`svd_solver='full'`），二維與三維共用同一組 PC1／PC2／PC3。
- 相似度在原始 100／50 維 z-score 向量上算 cosine similarity，不是 PCA 二維距離。
- 〈論衡·超奇〉不參與擬合；用已擬合的詞表、mean、std 與 PCA 轉換投影。

## 重要限制

- 這是全庫探索，不是 1,163 句主樣本的分類測試；PCA 位置不是預測機率。
- 100 詞只覆蓋全庫 **28.1%** 的詞次；50 詞只覆蓋 **22.4%**。
- 前三主成分只解釋 **20.07%**（100）／**26.35%**（50）；二維更只有 14.83%／19.34%。
- 25／52 篇少於 200 詞；最短 W09 只有 14 詞，最長 E04 有 1,991 詞（142.2×）。短篇的頻率與位置可能不穩定。
- 去重後語料沒有跨篇正規化完全相同句；4-gram 近似候選只有 30 對，多為同作者套語。W06-015／E11-018 是唯一進入前 30 的跨期候選，但仍只是「候選」，不判定借用方向或年代先後。

## 檔案

- `index.html`：互動介面（PCA 2D/3D、著色/篩選、原文與近鄰、主成分詞、相似度熱圖、重引候選、超奇投影與逐句預測）。
- `research_findings.md`：研究發現與可引用數字。
- `verification.md`／`verification.json`：核驗結果與受保護檔案雜湊。
- `browser_check.md`、`preview_2d.png`、`preview_3d.png`：headless 瀏覽器載入與互動核驗紀錄。
- `data/`：
  - `corpus_overview.json`、`works.csv`、`sentences.csv`
  - `features_100.csv`、`feature_counts_100.csv`、`feature_relative_100.csv`、`feature_zscores_100.csv`、`feature_stats_100.csv`
  - `pca_coordinates_100.csv`、`pca_loadings_100.csv`、`explained_variance_100.json`
  - `similarity_100.csv`、`neighbors_100.csv`、`neighbor_stability.csv`
  - `pc_word_evidence_100.csv`、`pc_word_examples_100.csv`
  - `chaoyi_projection_100.json`、`chaoyi_neighbors_100.csv`、`chaoyi_shared_features_100.csv`、`chaoyi_zscores_100.csv`
  - 50 特徵同名檔案
  - `reuse_exact.csv`、`reuse_approx.csv`、`reuse_special_check.json`
  - `predictions_formal.csv`

## 重跑

```powershell
python scripts/exploration/build_exploration_data.py
python scripts/exploration/verify_exploration.py
python scripts/exploration/build_exploration_html.py
```

腳本只讀取 `data/v3/`、`output/v3/`、`corpus_catalogue.csv`，不修改原有語料、模型或評估檔案；`report.html` 沒有被覆寫。
