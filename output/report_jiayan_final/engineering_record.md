# 報告定稿與要求核對

## 本次範圍

按使用者最後指示，report.md 與 report.pdf 以 Jiayan WordNgramTokenizer 流程的既有結果為主要分類結果，Jieba 僅為相同切分的對照。未重新訓練、未重新切分、未新增實驗。保留原稿及原 PDF 於 backup_before_update/。根目錄 Word、HTML、README 及既有資料、模型、探索輸出未改。

此為研究呈現的選擇，不能把選後測試成績視為全新盲測；亦不表示已證實 Jiayan 在其他作者或語料上普遍優於 Jieba。先前 comparison_summary.md 所載「先不寫入論文」屬當時工作指示，本次由使用者明確變更；相關方法限制仍保留。

## 最終證據對應

| 正文內容 | 既存證據 |
|---|---|
| 1,163 句、930/233 切分 | data/v3/dataset_v3.csv；output/tokenizer_comparison/jiayan/metrics.json |
| Jiayan 167/233、矩陣 [[100,27],[39,67]]、兩類 P/R/F1 | output/tokenizer_comparison/paired_predictions.csv；jiayan/metrics.json |
| 45 句改善、26 句退步 | output/tokenizer_comparison/paired_predictions.csv |
| 藝文志兩條誤判 | 同上 E11-014、E11-010；第二例正文只引句首，分數屬完整原句 |
| 管子書錄誤判 | 同上 W11-027 |
| 超奇 90/129 判東漢；兩個原文例句 | output/tokenizer_comparison/independent_comparison.csv，E01-011、E01-047 |
| 全庫、PCA、重引候選 | output/exploration/research_findings.md、data/ 及既有核驗；仍屬原 Jieba 探索 |
| 疑難文本三篇 | 原報告及 output/report_support/；沿用既有 Jieba 試判，未冒稱 Jiayan 結果 |
| 完整語料選目及實際底本 | output/report_support/corpus_appendix.md；corpus_catalogue.csv |

本次從既存逐句預測重算計數和指標，並核對引句判向。這屬輸出核驗，不是重跑實驗。完整報告逐段比對 PDF 文字，三頁已目視檢查。verification.json 記錄 24/24 項通過；不得把此數目解作教師要求全部驗收，或作者本人完成校勘。

## 分詞與方法限制

Jiayan 0.0.21 使用 WordNgramTokenizer 內建詞典，不是 CharHMMTokenizer；未下載或使用 jiayan.klm。原環境 KenLM 建置失敗，import 相容 stub 不提供語言模型功能；詳見 output/tokenizer_comparison/engineering_record.md 及既有程式。

Jiayan 組先以 OpenCC t2s 處理，Jieba 組另有 35 個自訂詞目，故不是只變更分詞演算法的完全等條件實驗。舊簡體控制亦不能視作對等詞典控制。分類較高不等於分詞準確率較高。未將單句視作彼此獨立樣本作顯著性論證。

原跨作者、同文類、分組對照與近鄰細項仍留於既有工程檔，未將它們改稱 Jiayan 驗證。以固定同批測試結果選擇 Jiayan 後，本文如實說明選擇偏差及尚無選後獨立測試。

## 字數與排版

正文 2,051 個可見非空白字元；連同題名 2,075；全篇含參考書目、配套說明及 AI 說明共 2,494。計入中英文字符、數字、標點、表格與標題；不計 Markdown 符號、連結目標及空白。這是 character 口徑，不是純漢字數或英文單詞數。老師頁面未另定字數軟件及參考書目是否計入，因此同時控制正文和全部可見內容在指定區間內。

PDF 依第一次作業 Report.docx 的段落、字體、頁面幾何與頁碼設定製作，三頁，兩張真正表格，正文五節。PDF 不嵌入完整篇目附錄。參考書目的短連結標籤在 PDF 顯示為文字；完整連結在 Markdown 及配套文件。原作業作者資料與舊註腳未繼承。

## 來源與完整書目

- 作業要求（本次已實際下載閱讀，快照 assignment_2_requirements.html）：https://mcjkurz.github.io/teaching/courses/2026-2027/CHI3242/assignments/assignment-2/
- 曹順慶主編《兩漢文論譯注》目錄：https://www.douban.com/subject/36127385/；https://www.shukui.net/book/3668495.html。僅用作選篇線索，不宣稱校核紙本或紙本頁碼。
- 揚雄《法言》〈吾子〉（修訂2269064）；班固《漢書》卷三十（7908197）；王充《論衡》〈超奇〉（2326276）。完整網址及其餘篇目見 corpus_catalogue.csv 與 corpus_appendix.md。
- Lukáš Zádrapa, “A Report on Stylometric Experiments with Pre-Modern Chinese Texts,” Archiv orientální 92, no. 1 (2024): 109–127. https://doi.org/10.47979/aror.j.92.1.109-127
- Donald Sturgeon, “Unsupervised Identification of Text Reuse in Early Chinese Literature,” Digital Scholarship in the Humanities 33, no. 3 (2018): 670–684. https://doi.org/10.1093/llc/fqx024
- Jiayan：https://github.com/jiaeyan/Jiayan；本次使用版本與環境見分詞工程記錄。

## 老師要求對照及未完成項

| 要求 | 本次核對結果 |
|---|---|
| 二元問題、清楚標籤、一致單位 | 正文第一、二節已說明文獻歸屬、0/1、按底本標點切句，明示引語隨載錄篇章 |
| 每類至少200、盡量平衡 | 主樣本西漢632、東漢531；訓練505/425；達到數量要求 |
| 80/20、分層、固定種子 | 沿用 seed42 的930/233指派；兩流程同批樣本 |
| LogisticRegression、特徵說明 | 正文說明TF-IDF與邏輯迴歸；僅在訓練集擬合；參數見既有metrics及程式 |
| accuracy、confusion matrix、precision、recall、F1 | 正文數字與表二全部具備，已由逐句預測交叉核算 |
| 另一文本預測及分析 | 〈超奇〉整篇129句，90東漢/39西漢，兩個帶分數原文例句；明示同作者留出限制 |
| 錯誤解釋、限制及改進 | 三條實際主模型誤判；引語、古人舊事、短句的解釋保留假設性；未見作者測試、資料多樣性及對等分詞控制列為改進 |
| 2000–2500字、非Markdown裸匯出 | 正文2051、全文2494可見字元，PDF3頁已逐頁檢視 |
| 本人抽樣核查AI標註 | 未核實完成；output/v3/v3_checklist.md 仍有未勾選項。不能以AI抽查或程式核驗冒充本人核查 |
| 報告為作者自己的分析 | 保留使用者提出的文獻考辨問題、才具及文實初讀；本次文字仍有AI草擬。作者需本人審閱、修訂並能說明，不能保證這一要求已滿足 |
| README與重跑說明 | 根目錄README仍以Jieba及舊資料版本為主，且稱未代寫正文，須交VS Code按最新report.md更新。Jiayan相關程式和輸出已存在，需將入口與環境說明連入README |
| 公開GitHub完整倉庫，無姓名學號 | 尚未核實公開網址；本機第二次作業目錄不是git工作樹。不能據此斷言使用者沒有別處公開倉庫，也不能聲稱已發布。公開前須排除本地環境、快取、私人或機器路徑紀錄 |
| Moodle提交倉庫URL及PDF | 未執行亦未核實；須由作者確認提交 |
| Word/HTML、互動頁 | 按分工未改；舊Word/HTML不含本次Jiayan定稿，不能作同內容交付；互動頁為可選補充且仍顯示原探索流程 |

老師允許AI協助編程或寫作，但明定報告須是本人分析，完全由AI生成的報告為零分。本記錄不對分數或完全合規作保證。

## 交予 VS Code 的最後同步工作（不跑實驗）

以根目錄最新 report.md 為唯一正文來源，更新 report.docx、report.html；不要覆寫已定稿 report.md/report.pdf。更新 README 的研究主流程為 Jiayan WordNgramTokenizer＋OpenCC＋TF-IDF＋LogisticRegression，167/233、71.67%、macro F1 0.7109、〈超奇〉90/129；Jieba 為對照，PCA與疑難文本仍標原Jieba。把既有 scripts/tokenizer_comparison/ 的準備、訓練、評估與應用入口及相應環境記錄連入README，不能只保留舊命令；逐項檢查相對路徑。不訓練、不改資料，不虛構已完成本人抽查。舊版本敘述留工程文件；完整語料附錄維持外置。檢查實際公開GitHub內容是否含最終PDF、MD、數據及程式；若尚無公開倉庫，回報事實，不冒稱已發布。提交前核查匿名性及Moodle需交公開URL與PDF。
