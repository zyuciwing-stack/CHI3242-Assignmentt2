# 詞語與兩漢文論的時期歸屬

本作業考察兩漢文論的詞彙能否協助辨識文獻歸屬，以及這種比較對文獻考辨的用途與限度。西漢／東漢是載錄篇章的分期標籤，並不預設兩漢文風二元對立。

## 閱讀入口

- [報告 Markdown](report.md)、[Word](report.docx)、[報告網頁](report.html)。正文已修訂至2,318字元；PDF待作者審閱後補交，本次尚未上傳。
- [配套材料索引](materials.html)：完整篇目、底本、分類結果及工程文件。
- [完整語料附錄](output/report_support/corpus_appendix.html)：70 筆來源記錄，各筆列作者、篇名、選段、維基文庫底本與修訂號、句數及用途。實際可建模52篇，另有超奇與3筆疑難材料；70筆不等於70篇作品。
- [互動探索](output/exploration/index.html)：離線 PCA 二維／三維圖、篇章近鄰與重引候選。該部分沿用 Jieba。

## 標籤、來源與切分

分析單位是一句，按底本句號、問號、感嘆號切分。西漢為0，東漢為1；引文隨載錄篇章歸類，《法言》採傳統西漢口徑，《漢書》列東漢。以曹順慶《兩漢文論譯注》線上目錄和嚴可均《全漢文》《全後漢文》作選材線索，實際輸入一律採維基文庫固定修訂本，以條目、網址及修訂號定位，不以紙本頁碼為引用依據。

全庫15位作者、52篇、1654句（西漢702／東漢952）。限額取樣後1163句（632／531），固定種子42、80/20分層切分：訓練930（505／425），測試233（127／106）。資料及 split 欄保存在 [dataset_v3.csv](data/v3/dataset_v3.csv)，完整切句在 [sentences_all.csv](data/v3/sentences_all.csv)。超奇129句整篇留出；疑難材料不回填訓練標籤。

## 最終方法與結果

Jiayan 0.0.21 WordNgramTokenizer＋OpenCC t2s＋詞語 TF-IDF＋LogisticRegression。僅用訓練資料擬合詞表及模型。TF-IDF：min_df=2、max_df=0.9、sublinear_tf=True、單詞特徵；邏輯迴歸：C=1、lbfgs、max_iter=2000、random_state=42、class_weight=None。判東漢閾值0.5。

|項目|結果|
|---|---|
|準確率|167/233＝71.67%|
|多數類基準|127/233＝54.51%|
|macro F1|0.7109|
|混淆矩陣（真實列／預測欄，西漢、東漢）|[[100,27],[39,67]]|
|西漢 P/R/F1|0.7194／0.7874／0.7519|
|東漢 P/R/F1|0.7128／0.6321／0.6700|
|超奇|90/129判東漢，同作者留出|

Jieba同切分對照148/233、macro F1 0.6161；45句改善、26句退步。Jiayan在本次比較後選定，233句不是選後新盲測。所有測試作者均見於訓練集，不能據此證明跨作者斷代能力。PCA與疑難文本結果仍是Jieba探索，沒有改稱Jiayan驗證。

## 程式入口與重現

本輪交付沒有重新分詞或訓練。以下列出既有流程；重跑會覆寫相應結果，請在副本操作。

1. 資料準備與分層切分：scripts/prepare_v3_raw.py、scripts/build_corpus_v3.py；篇目規則見 scripts/corpus_manifest_v3.py。本次重現應直接使用已固定的 data/v3/dataset_v3.csv 的 split 欄。
2. Jieba 分詞：python scripts/tokenizer_comparison/prepare_tokens_jieba.py
3. Jiayan 分詞：在工程記錄指定的 Jiayan 環境執行 python scripts/tokenizer_comparison/prepare_tokens_jiayan.py
4. 從已保存的兩組 tokens 訓練、評估並應用於超奇：python scripts/tokenizer_comparison/run_comparison.py
5. 核驗對照：python scripts/tokenizer_comparison/verify_comparison.py

依賴版本見 requirements.txt 與 [分詞環境記錄](output/tokenizer_comparison/engineering_record.md)。Jiayan另需jiayan==0.0.21、python-crfsuite==0.9.12、opencc-python-reimplemented==0.1.7。原Windows環境未成功安裝KenLM；此處只用WordNgramTokenizer。保留 output/tokenizer_comparison/vendor_stub/kenlm.py 供套件import相容，不提供語言模型，不能用於CharHMM。既有tokens已附，重現分類可從第4步開始。

正式結果目錄為 output/tokenizer_comparison/jiayan/，包括 metrics.json、test_predictions.csv、獨立篇章預測及tokens；兩組配對表在 output/tokenizer_comparison/。以 [配套材料](materials.html) 的實際連結定位。

## 工程與提交

歷次版本的細節留在 output/ 下工程文件；舊README保存在 output/takeover_final/README_before_takeover.md。正文不敘述版本演進。AI參與編程、核對、草擬與排版，作者審閱及實際完成的抽查分開記錄。

老師要求在Moodle提交報告PDF與公開GitHub倉庫網址。本倉庫為本次作業材料。PDF依作者指示暫未上傳，待審閱後補入；Moodle提交由作者完成。
