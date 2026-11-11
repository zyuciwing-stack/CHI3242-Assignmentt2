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
- 25／52 篇少於 200 詞；最短 W09 只有 14 詞（本次保留材料，不是原篇全文），最長 E04 有 1,991 詞（142.2×）。200 詞只是提醒門檻，不是已驗證的可靠性界線；短篇的頻率與位置可能不穩定。
- 去重後語料沒有跨篇正規化完全相同句；4-gram 近似候選只有 30 對，多為同作者套語。30對是全部符合門檻的候選，W06-015／E11-018 是唯一跨期候選，但仍只是「候選」，不判定借用方向或年代先後。

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
  - `chaoyi_projection_100.json`、`chaoyi_neighbors_100.csv`、`chaoyi_shared_features_100.csv`、`chaoyi_contribution_checks_100.json`、`chaoyi_zscores_100.csv`
  - 50 特徵同名檔案；`chaoyi_neighbor_overlap.json`
  - `reuse_exact.csv`、`reuse_approx.csv`、`reuse_special_check.json`
  - `predictions_formal.csv`

## 重跑

```powershell
python scripts/exploration/build_exploration_data.py
python scripts/exploration/build_exploration_html.py
python scripts/exploration/verify_exploration.py
```

腳本只讀取 `data/v3/`、`output/v3/`、`corpus_catalogue.csv`，不修改原有語料、模型或評估檔案。論文檔案由後續整合作業更新，並非這三個探索腳本的輸出。

## 本次修訂與核驗範圍

近鄰貢獻表已保存全部特徵及實際詞次，提供「只看兩篇皆出現」篩選、近鄰選擇、類型篩選與排序；近鄰穩定性採前五3/5、前十8/10重合，不用PCA變號推論。完整數值核驗為80/80（程式61、瀏覽器9、研究解釋10）；新的獨立計算見 `../final_integration/exploration_audit.json`。

`preview_2d.png`、`preview_3d.png`已由本次頁面以 headless Chrome 重新截圖；新版貢獻表的鄰居選擇、兩篇皆出現篩選、類型篩選與排序已用注入測試確認 DOM 更新。實際滑鼠拖曳、滾輪縮放與一般桌面瀏覽器視覺驗收仍未模擬。

實際重跑環境見 `../final_integration/exploration_environment.json` 和 `requirements.exploration.txt`。本次沿用現有課程環境，未安裝套件；它與專案根目錄舊 `requirements.txt` 版本不同，應按實際環境重跑探索。原有分類模型不重新訓練，83個語料與模型評估檔案逐一比對修改前雜湊；語料目錄的引用欄位已依用戶指示改用維基文庫，核驗依據另見source_revision.json。
