# 瀏覽器核驗紀錄

日期：2026-11-11。以 Microsoft Edge／Google Chrome headless 直接開啟 `file:///.../output/exploration/index.html`，不經伺服器、不載入 CDN。

## 已核驗

- 2D PCA 與 3D PCA 均成功渲染；截圖見 `preview_2d.png`、`preview_3d.png`。
- 作者篩選「王充」：圖上參照點為 4 篇（E02、E03、E04、E05）。
- 文類篩選「序跋」：圖上參照點為 23 篇。
- 篇章篩選「W09」：圖上參照點為 1 篇。
- 篇章下拉選「E01｜論衡·超奇（留出投影）」：右側詳情顯示 E01 投影、來源、原文與近鄰。
- 搜尋「屈原」：特徵詞與原句結果均出現。
- 重用面板：完全相同頁顯示「沒有跨篇」訊息；4-gram 頁顯示候選表。
- 點擊熱圖格子 W06：右側詳情切換到 W06。
- 切到 3D 後點擊資料點 W15：右側詳情切換到 W15。
- 原文、底本頁與固定修訂網址連結均存在（`https://zh.wikisource.org/...`）。
- 3D 圖為 Plotly WebGL 場景；headless 截圖已渲染。實際滑鼠旋轉／縮放由 Plotly 內建 `orbit` 與 `scrollZoom` 提供，需在一般瀏覽器中操作。

## 注意

- Headless 測試只驗證靜態載入、篩選、事件與渲染；沒有模擬真實滑鼠拖曳軌跡。
- 若瀏覽器禁用 WebGL，3D 圖可能退化或顯示警告；2D 圖仍可用。
