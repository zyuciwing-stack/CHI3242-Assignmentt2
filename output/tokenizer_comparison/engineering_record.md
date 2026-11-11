# 分詞對照工程記錄

日期：2026-11-11
專案：`C:\CHI3242文本發掘\第二次作業`
範圍：只做 Jieba／Jiayan 分詞對照；`report.md`、`report.pdf`、`report.docx`、`report.html`、`data/v3/`、`output/v3/`、`output/exploration/` 均未修改。

## 一、固定比較條件

直接使用 `data/v3/dataset_v3.csv` 的 1,163 句及原 `split` 欄位，不重新隨機切分：

- 訓練 930：西漢 505、東漢 425。
- 測試 233：西漢 127、東漢 106。
- 訓練與測試 `sent_id` 無交集，句序沿用資料檔。
- 兩組都只用訓練集擬合 TF-IDF，再 transform 測試集。
- 相同 TF-IDF：`token_pattern=(?u)\b\w+\b`、`min_df=2`、`max_df=0.9`、`sublinear_tf=True`、`ngram_range=(1,1)`。
- 相同邏輯迴歸：`max_iter=2000`、`random_state=42`、`class_weight=None`、`C=1.0`、`solver=lbfgs`。
- 相同標籤順序：西漢 0、東漢 1；閾值 0.5。
- Jieba 組保留原有 35 個文論補充詞目；Jiayan 組使用官方 `WordNgramTokenizer` 內建詞典，沒有臨時加入自訂詞目。

## 二、環境與來源

實際分類環境（原專案 venv）：

- Python 3.12.10
- scikit-learn 1.9.1
- pandas 3.0.6
- numpy 2.5.3
- jieba 0.42.1

Jiayan token 環境（專案內隔離 venv：`output/tokenizer_comparison/venv`）：

- Python 3.12.10
- jiayan 0.0.21（PyPI；官方專案 `https://github.com/jiaeyan/Jiayan`）
- python-crfsuite 0.9.12
- opencc-python-reimplemented 0.1.7
- scikit-learn 1.9.1、pandas 3.0.6、numpy 2.5.3、jieba 0.42.1（與分類環境同版）
- 官方 jiayan 套件 tar 檔：`output/tokenizer_comparison/packages/jiayan-0.0.21.tar.gz`，SHA-256 `C061077866D02E0BCB9B25CDA65F34859E304EEC94AD2E26D9E42088319D677B`
- 內建詞典 `jiayan/data/dict.txt`：SHA-256 `a21d687570b1c39a153ed7d7624b74003f9ca191019eba16603b63e6d88acd30`
- 未下載官方 728M 模型檔；本輪不使用 KenLM。

官方說明要求 `pip install jiayan`、`pip install kenlm`，並下載 `jiayan.klm` 使用推薦的 `CharHMMTokenizer`。本機沒有可用 C/C++ 編譯器；`pip install kenlm` 以 NMake CMake generator/platform error 失敗。為避免用其他工具冒充 Jiayan，也未自行以假 LM 執行 CharHMM。本輪改用同一官方套件的 `WordNgramTokenizer`；它不需要 `jiayan.klm`，但不是 Jiayan 官方最推薦的 HMM 分詞。此限制會直接影響外推。

Jiayan 官方說明其模型以簡體訓練，因此 Jiayan 組先以 OpenCC `t2s` 轉換既有 `text_normalized`。Jieba 組保留原始繁體文字。另做 `exploratory_jieba_simplified/`：對同一簡體文字跑 Jieba，只在摘要中作控制，不取代主 Jieba 基準。

## 三、執行步驟

1. `scripts/tokenizer_comparison/prepare_tokens_jieba.py`（原 venv）→ `jieba/tokens_main.csv`、`tokens_chaoyi.csv`。
2. `scripts/tokenizer_comparison/prepare_tokens_jiayan.py`（隔離 venv，`vendor_stub/kenlm.py` 只為讓官方 `WordNgramTokenizer` 可 import；不提供語言模型）→ `jiayan/tokens_main.csv`、`tokens_chaoyi.csv`。
3. `scripts/tokenizer_comparison/run_comparison.py`（原 venv）→ 兩組 TF-IDF／邏輯迴歸、逐句預測、指標、配對表、〈超奇〉表。
4. `scripts/tokenizer_comparison/prepare_tokens_jieba_simplified.py`、`run_control_jieba_simplified.py`（原 venv）→ 簡體控制。
5. `scripts/tokenizer_comparison/make_segmentation_review.py` → 20 句固定抽查、5 改善 + 5 退步例證、詞例。
6. `scripts/tokenizer_comparison/verify_comparison.py` → `verification.json`。

## 四、基準重現

Jieba 重跑與 `output/v3/test_predictions.csv`：

- 233 句預測標籤差異 **0**。
- 最大 `prob_east` 絕對差 **8.33e-17**。
- 148/233；混淆矩陣 `[[100,27],[58,48]]`；macro F1 `0.616070563148202`。
- 〈超奇〉重現 **56/129** 判東漢，最大機率差 0。
- 零有效特徵 7 句、僅一項 20 句。

## 五、主結果

| 指標 | Jieba | Jiayan WordNgram | 差異 |
|---|---:|---:|---:|
| 判對／233 | 148 | 167 | +19 |
| accuracy | 0.635193 | 0.716738 | +0.081545 |
| balanced accuracy | 0.620116 | 0.709739 | +0.089623 |
| macro F1 | 0.616071 | 0.710940 | +0.094869 |
| 東漢 recall | 0.452830 | 0.632075 | +0.179245 |
| 西漢 recall | 0.787402 | 0.787402 | 0 |
| 零有效特徵 | 7 | 1 | -6 |
| 僅一項有效特徵 | 20 | 0 | -20 |
| 詞表大小 | 1,125 | 1,294 | +169 |
| 主樣本 token 數 | 19,531 | 27,313 | +7,782 |

配對：兩者皆對 122、兩者皆錯 40、Jieba 錯 Jiayan 對 45、Jieba 對 Jiayan 錯 26。45 − 26 = +19。McNemar 精確 p ≈ 0.0319，僅探索；同篇句子不獨立。

簡體控制（Jieba＋OpenCC）：148/233、accuracy 0.6352、macro F1 0.6111、東漢 recall 0.4245、〈超奇〉63/129。可見只做簡體轉換不會產生 Jiayan 的 +19；但仍不能把差異純粹歸給算法，因為 Jiayan 使用不同詞典／切分粒度且沒有相同自訂詞目。

〈超奇〉：Jieba 56/129，Jiayan 90/129；轉換為兩者皆東漢 41、Jieba 西漢→Jiayan 東漢 49、Jieba 東漢→Jiayan 西漢 15、兩者皆西漢 24。此為同作者留出、且早已分析，不是跨作者盲測。

## 六、限制

- 不是 Jiayan 最佳設定：官方推薦 CharHMM + KenLM，本輪建置失敗，只能使用 WordNgramTokenizer。
- 兩組文字不同：Jiayan 需要 OpenCC 簡體；Jieba 保留繁體。
- 詞目不同：Jieba 有 35 個文論補充詞目；Jiayan 用內建詞典，沒有事後加詞或調頻。
- 單一固定切分、單一語料版本；沒有重複交叉驗證。
- 切詞抽查由 AI 輔助，不是人工 gold；改善／退步例證按結果選出，不能當整體分詞準確率。
- 不可把本輪結果寫入論文或宣稱 Jiayan 已普遍優於 Jieba；只能作為這批材料上的探索訊號。

## 七、產物與保護

主要產物：`output/tokenizer_comparison/` 下的 `comparison_summary.md`、`comparison_metrics.csv`、`paired_predictions.csv`、`segmentation_review.md`、`independent_comparison.csv`、`verification.json`。

`verification.json` 檢查原 `report.md`、`report.pdf`、`report.docx`、`report.html`、`data/v3/`、`output/v3/`、`output/exploration/` 與同步前快照；除 Word/HTML 同步任務已改的 `report.docx`、`report.html` 外，其餘均未變。`report.md`／PDF／Word／HTML 在本輪沒有再修改。
