# -*- coding: utf-8 -*-
"""Build a self-contained offline HTML for the exploration analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "output" / "exploration" / "data"
OUT = ROOT / "output" / "exploration" / "index.html"


def read_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def read_csv(name):
    return pd.read_csv(DATA / name, encoding="utf-8-sig").fillna("")


def records(df):
    return json.loads(df.to_json(orient="records", force_ascii=False))


def build_bundle():
    overview = read_json("corpus_overview.json")
    works = read_csv("works.csv")
    sentences = read_csv("sentences.csv")
    sentences = sentences.drop(columns=["cjk_text"], errors="ignore")

    original = sentences.groupby("work_id")["text_original"].apply(lambda x: "".join(x)).to_dict()
    works["original_text"] = works["work_id"].map(original)
    works_payload = records(works)

    sentences_payload = records(sentences)

    pca = {}
    loadings = {}
    coverage = {}
    warnings = {}
    explained_payload = {}
    for n in [100, 50]:
        coords = read_csv(f"pca_coordinates_{n}.csv")
        coords_payload = {
            row["work_id"]: {"PC1": float(row["PC1"]), "PC2": float(row["PC2"]),
                             "PC3": float(row["PC3"])}
            for _, row in coords.iterrows()
        }
        ev = read_json(f"explained_variance_{n}.json")
        ch = read_json(f"chaoyi_projection_{n}.json")
        pca[str(n)] = {
            "coords": coords_payload,
            "explained": ev["explained_variance_ratio"],
            "cumulative": ev["cumulative_explained"],
            "chaoyi": ch,
        }
        explained_payload[str(n)] = ev
        loadings[str(n)] = records(read_csv(f"pca_loadings_{n}.csv"))
        stats = read_csv(f"feature_stats_{n}.csv")
        total_tokens = sum(w["token_count"] for w in works_payload)
        coverage[str(n)] = {
            "feature_tokens": int(stats["total_count"].sum()),
            "total_tokens": int(total_tokens),
            "coverage": float(stats["total_count"].sum() / total_tokens),
        }
        fs = read_json(f"feature_selection_{n}.json")
        warnings[str(n)] = fs.get("warnings", [])

    word_evidence = {str(n): records(read_csv(f"pc_word_evidence_{n}.csv")) for n in [100, 50]}
    word_examples = {str(n): records(read_csv(f"pc_word_examples_{n}.csv")) for n in [100, 50]}

    similarity = {}
    neighbors = {}
    for n in [100, 50]:
        sim = pd.read_csv(DATA / f"similarity_{n}.csv", encoding="utf-8-sig", index_col=0)
        similarity[str(n)] = {"labels": sim.index.tolist(),
                              "matrix": sim.values.tolist()}
        nb = read_csv(f"neighbors_{n}.csv")
        grouped = {}
        for _, row in nb.iterrows():
            grouped.setdefault(row["source_work_id"], []).append({
                "rank": int(row["rank"]),
                "target_work_id": row["target_work_id"],
                "similarity": float(row["similarity"]),
                "target_title": row["target_title"],
                "target_author": row["target_author"],
                "target_period": row["target_period"],
            })
        neighbors[str(n)] = grouped

    chaoyi = {}
    for n in [100, 50]:
        proj = read_json(f"chaoyi_projection_{n}.json")
        nb = read_csv(f"chaoyi_neighbors_{n}.csv")
        shared = read_csv(f"chaoyi_shared_features_{n}.csv")
        shared_grouped = {}
        for _, row in shared.iterrows():
            shared_grouped.setdefault(row["neighbor_work_id"], []).append({
                "feature": row["feature"],
                "z_chaoyi": float(row["z_chaoyi"]),
                "z_neighbor": float(row["z_neighbor"]),
                "co_loading": float(row["co_loading"]),
                "total_count": int(row["total_count"]),
                "doc_count": int(row["doc_count"]),
                "author_count": int(row["author_count"]),
                "west_count": int(row["west_count"]),
                "east_count": int(row["east_count"]),
            })
        chaoyi[str(n)] = {
            "projection": proj,
            "neighbors": records(nb),
            "shared": shared_grouped,
        }

    stability = records(read_csv("neighbor_stability.csv"))

    pred = read_csv("predictions_formal.csv")
    predictions = {}
    for _, row in pred.iterrows():
        predictions[row["sent_id"]] = {
            "source": row["source"],
            "period_true": row["period_true"],
            "period_pred": row["period_pred"],
            "prob_east": float(row["prob_east"]),
            "prob_west": float(row["prob_west"]),
            "correct": bool(row["correct"]) if row["correct"] != "" else None,
            "text_original": row["text_original"],
        }
    chaoyi_pred = pred[pred["source"] == "v3 independent_predictions"].copy()
    chaoyi_pred = chaoyi_pred.merge(
        sentences[["sent_id", "sent_order"]], on="sent_id", how="left").sort_values("sent_order")
    chaoyi_predictions = records(chaoyi_pred.drop(columns=["sent_order"], errors="ignore"))

    exact = read_csv("reuse_exact.csv")
    approx = read_csv("reuse_approx.csv")
    special = read_json("reuse_special_check.json")
    for df in (exact, approx):
        df["cross_period"] = df["period_a"] != df["period_b"] if len(df) else False
    reuse = {
        "exact": records(exact),
        "approx": records(approx),
        "special": special,
        "rules": {
            "exact": "正規化（去除標點/空白）後完全相同；最少 8 個漢字；跨 work_id；去重後語料中無跨篇完全相同句。",
            "approx": "漢字 4-gram；containment >= 0.60；共享 4-gram >= 4；較短句 >= 8 漢字；跨 work_id；僅稱候選。",
            "short_sentences_excluded": int((sentences["cjk_len"] < 8).sum()),
        },
    }

    meta = {
        "title": "兩漢文論互動探索分析",
        "subtitle": "52 篇可建模全庫 · 1,654 句 · PCA 100/50 高頻詞 · 〈超奇〉獨立投影",
        "overview": overview,
        "feature_coverage": coverage,
        "warnings": warnings,
        "explained": {k: v for k, v in explained_payload.items()},
        "definitions": {
            "unit": "一篇或已界定的節選；不是一句。",
            "feature_selection": "每個特徵設定取語料庫總頻率最高的 N 個 unigram；cull=None、min_variance=None。",
            "frequency": "每篇的相對頻率 = 該詞次數 / 該篇總詞數（jieba 過濾標點後）。",
            "zscore": "z = (相對頻率 - 52 篇平均) / 52 篇標準差；總體標準差 ddof=0；std < 1e-10 設為 1。",
            "pca": "sklearn PCA(n_components=3, svd_solver='full')，只以 52 篇參照作品擬合。",
            "similarity": "在原始 N 維 z-score 向量上算 cosine similarity；不是 PC1/PC2 二維距離。",
            "projection": "〈超奇〉用已擬合詞表、mean、std 轉換，再 pca.transform；沒有重新擬合。",
        },
    }

    return {
        "meta": meta,
        "works": works_payload,
        "sentences": sentences_payload,
        "pca": pca,
        "loadings": loadings,
        "word_evidence": word_evidence,
        "word_examples": word_examples,
        "similarity": similarity,
        "neighbors": neighbors,
        "chaoyi": chaoyi,
        "neighbor_stability": stability,
        "predictions": predictions,
        "chaoyi_predictions": chaoyi_predictions,
        "reuse": reuse,
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{
  --bg:#f5f3ee; --panel:#fffdf8; --ink:#20242a; --muted:#65707c;
  --line:#d9d4c8; --accent:#8b3a2f; --accent2:#2f5d62; --gold:#b7791f;
  --west:#2b6cb0; --east:#c53030; --short:#b45309;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Noto Sans TC","Microsoft JhengHei","PingFang TC",sans-serif;
  line-height:1.55;font-size:14px}
h1,h2,h3{font-family:"Noto Serif TC","Songti TC","PMingLiU",serif;line-height:1.25}
h1{font-size:30px;margin:0 0 6px;letter-spacing:0.02em}
h2{font-size:21px;margin:0 0 12px;border-left:5px solid var(--accent);padding-left:10px}
h3{font-size:16px;margin:14px 0 8px}
a{color:var(--accent2);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1500px;margin:0 auto;padding:24px 22px 60px}
header.hero{background:linear-gradient(135deg,#1f2933,#3b2f2a 65%,#6b3f35);
  color:#fff;padding:30px 22px 24px;border-bottom:4px solid var(--gold)}
header.hero .inner{max-width:1500px;margin:0 auto}
header.hero p{margin:6px 0 0;color:#e9dfd0}
header.hero .note{margin-top:12px;font-size:13px;color:#f3d9a4}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:16px 18px;box-shadow:0 1px 2px rgba(0,0,0,.04);margin:14px 0}
.grid{display:grid;gap:14px}
.cards{grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.card{background:#fff;border:1px solid var(--line);border-radius:9px;padding:13px 14px}
.card .k{font-size:12px;color:var(--muted);letter-spacing:.04em}
.card .v{font-size:22px;font-weight:700;margin-top:3px}
.card .s{font-size:12px;color:var(--muted);margin-top:2px}
.note{background:#fff7e6;border:1px solid #f0d39b;border-radius:8px;padding:10px 12px;
  color:#6b4a0f;font-size:13px}
.warn{background:#fdf0ec;border:1px solid #efc0b3;color:#7b2d1c;border-radius:8px;
  padding:10px 12px;font-size:13px}
.ok{color:#276749}
.muted{color:var(--muted)}
.small{font-size:12px}
.tiny{font-size:11px}
.controls{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:end}
.control{display:flex;flex-direction:column;gap:4px;min-width:130px}
.control label{font-size:11px;color:var(--muted);letter-spacing:.04em}
select,input[type=text]{padding:7px 9px;border:1px solid var(--line);border-radius:7px;
  background:#fff;color:var(--ink);font-size:13px;min-width:130px}
button{border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:7px;
  padding:7px 11px;font-size:13px;cursor:pointer}
button:hover{background:#f3efe6}
button.active{background:var(--accent);border-color:var(--accent);color:#fff}
button.ghost{background:transparent}
.pill{display:inline-block;border-radius:999px;padding:1px 8px;font-size:11px;
  border:1px solid var(--line);background:#fff;color:var(--muted);margin-left:4px}
.pill.west{background:#e8f0fa;border-color:#b9d1ee;color:#1d4f86}
.pill.east{background:#fbe9e9;border-color:#eab8b8;color:#8f2626}
.pill.short{background:#fff3e0;border-color:#ecc58a;color:#8a4b0f}
.pill.cross{background:#e9f7ef;border-color:#a8d8bc;color:#1f6b43}
.plotbox{background:#fff;border:1px solid var(--line);border-radius:10px;padding:8px}
#pca2d,#pca3d{width:100%}
#pca2d{height:560px}
#pca3d{height:680px}
.legend{display:flex;flex-wrap:wrap;gap:8px 12px;margin-top:8px}
.chip{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted)}
.dot{width:11px;height:11px;border-radius:50%;display:inline-block;border:1px solid #fff;
  box-shadow:0 0 0 1px rgba(0,0,0,.15)}
.two-col{display:grid;grid-template-columns:1.05fr .95fr;gap:14px}
.three-col{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}
@media(max-width:1050px){.two-col,.three-col{grid-template-columns:1fr}}
.detail{min-height:220px}
.detail-head{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;justify-content:space-between}
.meta-table{width:100%;border-collapse:collapse;margin:8px 0}
.meta-table td{border-bottom:1px solid #eee7da;padding:4px 6px;vertical-align:top}
.meta-table td:first-child{width:88px;color:var(--muted);font-size:12px}
pre.original{white-space:pre-wrap;background:#fbf8f1;border:1px solid #e5ddcd;
  border-radius:8px;padding:10px 12px;max-height:260px;overflow:auto;font-size:13px;
  font-family:"Noto Serif TC","Songti TC",serif;line-height:1.65}
.scroll{max-height:340px;overflow:auto;border:1px solid #eee7da;border-radius:8px}
table.data{width:100%;border-collapse:collapse;font-size:12px}
table.data th,table.data td{border-bottom:1px solid #eee7da;padding:5px 6px;text-align:left;
  vertical-align:top}
table.data th{position:sticky;top:0;background:#faf6ee;z-index:1;font-weight:600}
table.data tr.clickable:hover{background:#f6f0e2;cursor:pointer}
table.data td.num{text-align:right;font-variant-numeric:tabular-nums}
.words{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.wordlist{display:flex;flex-wrap:wrap;gap:6px}
.word-btn{font-size:12px;padding:4px 8px;border-radius:6px;background:#f8f4ea;
  border:1px solid #e4dac6;color:#3d3427;cursor:pointer}
.word-btn:hover{background:#efe4ce}
.word-btn b{font-weight:700}
.evidence{background:#fbf8f1;border:1px solid #e5ddcd;border-radius:8px;padding:10px 12px}
.evidence .big{font-size:20px;font-weight:700}
.kv{display:grid;grid-template-columns:100px 1fr;gap:3px 8px;font-size:12px}
.kv .k{color:var(--muted)}
.example{border-top:1px dashed #e2d8c5;padding:7px 0;font-size:12px}
.example .text{font-family:"Noto Serif TC","Songti TC",serif;font-size:13px;margin:3px 0}
.badge{display:inline-block;border-radius:4px;padding:0 5px;font-size:10px;
  border:1px solid #ddd;color:#666;background:#fafafa}
.badge.west{background:#e8f0fa;border-color:#b9d1ee;color:#1d4f86}
.badge.east{background:#fbe9e9;border-color:#eab8b8;color:#8f2626}
.badge.short{background:#fff3e0;border-color:#ecc58a;color:#8a4b0f}
.badge.cross{background:#e9f7ef;border-color:#a8d8bc;color:#1f6b43}
.reuse-card{border:1px solid #e5ddcd;border-radius:8px;padding:10px 12px;background:#fcfaf5;margin:8px 0}
.reuse-card.special{border-color:#d6a84b;background:#fff8e8}
.reuse-pair{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:900px){.reuse-pair{grid-template-columns:1fr}}
.reuse-text{font-family:"Noto Serif TC","Songti TC",serif;font-size:13px;line-height:1.6}
.section-desc{color:var(--muted);font-size:13px;margin:-4px 0 10px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.footer{border-top:1px solid var(--line);margin-top:28px;padding-top:14px;color:var(--muted);font-size:12px}
details summary{cursor:pointer;color:var(--accent2)}
code{background:#f2ecdf;padding:1px 4px;border-radius:3px;font-size:12px}
</style>
</head>
<body>
<header class="hero">
  <div class="inner">
    <h1>__TITLE__</h1>
    <p>__SUBTITLE__</p>
    <p class="note">這是全庫探索（52 篇、1,654 句），不是 1,163 句主樣本的分類測試；圖上的位置不是「東漢概率」或「真偽概率」。</p>
  </div>
</header>
<div class="wrap">

<section class="panel">
  <h2>1. 語料概況與分析單位</h2>
  <p class="section-desc">每點是一篇或已界定的節選，不是一句。參照空間只含 52 篇可建模作品；〈論衡·超奇〉整篇留出，另作投影。</p>
  <div id="overviewCards" class="grid cards"></div>
  <div id="overviewNotes" class="grid" style="margin-top:12px"></div>
</section>

<section class="panel">
  <h2>2. 篇章 PCA：二維／三維</h2>
  <p class="section-desc">這張圖回答：52 篇作品在 100（或 50）個高頻詞的 z-score 空間中，前三個主成分如何排列？顏色與篩選只是標籤，不進入 PCA；切換只重繪，不重新擬合。</p>
  <div class="controls">
    <div class="control"><label>特徵設定</label>
      <select id="featureSelect"><option value="100">100 個高頻詞</option><option value="50">50 個高頻詞（敏感度）</option></select>
    </div>
    <div class="control"><label>視圖</label>
      <div><button id="view2d" class="active">2D</button> <button id="view3d">3D</button></div>
    </div>
    <div class="control"><label>著色</label>
      <select id="colorSelect"><option value="period">分期</option><option value="author">作者</option><option value="genre">文類</option></select>
    </div>
    <div class="control"><label>作者篩選</label><select id="authorSelect"></select></div>
    <div class="control"><label>文類篩選</label><select id="genreSelect"></select></div>
    <div class="control"><label>篇章篩選</label><select id="workSelect"></select></div>
    <div class="control"><label>其他</label>
      <div><label class="small"><input type="checkbox" id="showChaoyi" checked> 顯示〈超奇〉</label></div>
    </div>
    <div class="control"><label>&nbsp;</label><button id="resetBtn" class="ghost">重設篩選</button></div>
  </div>
  <div class="legend" id="legend"></div>
  <div class="grid two-col" style="margin-top:10px">
    <div class="plotbox"><div id="pca2d"></div><div id="pca3d" style="display:none"></div></div>
    <div class="detail panel" id="workDetail"><span class="muted">點選圖上的一點，或從下方篇章清單選擇。</span></div>
  </div>
  <div id="varianceNote" class="note" style="margin-top:10px"></div>
  <details style="margin-top:10px"><summary>52 篇清單（含實際長度與短篇提醒）</summary>
    <div class="scroll" style="margin-top:8px"><table class="data" id="workTable"></table></div>
  </details>
</section>

<section class="panel">
  <h2>3. 主成分重要詞與原句查詢</h2>
  <p class="section-desc">這裡是 PCA 成分負荷量（components_），不是邏輯迴歸係數。點詞看次數、篇章／作者分布、西漢／東漢頻率與原句；出現少或集中於單一作者時，不要據此概括時期文風。</p>
  <div class="tabs" id="pcTabs"><button data-pc="1" class="active">PC1</button><button data-pc="2">PC2</button><button data-pc="3">PC3</button></div>
  <div class="words" id="wordColumns"></div>
  <div class="grid two-col" style="margin-top:10px">
    <div id="wordEvidence" class="evidence"><span class="muted">點選左側詞語查看證據。</span></div>
    <div>
      <div class="control"><label>詞語／原句查詢</label><input type="text" id="searchInput" placeholder="例如：屈原、著述、詩"></div>
      <div id="searchResults" class="small" style="margin-top:8px"></div>
    </div>
  </div>
</section>

<section class="panel">
  <h2>4. 篇章相似度與鄰近篇章</h2>
  <p class="section-desc">相似度在原始 100／50 維 z-score 特徵向量上算 cosine similarity（不是 PC1/PC2 二維距離）。熱圖是 52×52 參照作品；點格子或下方按鈕可看該篇的近鄰。</p>
  <div class="grid two-col">
    <div class="plotbox"><div id="heatmap" style="height:860px"></div></div>
    <div>
      <div id="heatmapDetail" class="evidence"><span class="muted">點熱圖格子或選擇一篇，查看近鄰。</span></div>
      <div id="heatmapNeighbors" style="margin-top:10px"></div>
    </div>
  </div>
</section>

<section class="panel">
  <h2>5. 文字重用候選與對讀</h2>
  <p class="section-desc">先查正規化後完全相同的跨篇句；再用漢字 4-gram containment 找近似片段。所有結果只稱「候選」，不自動判定借用方向或年代先後。去重後語料沒有跨篇完全相同句；近似候選多為同作者套語，W06-015／E11-018 是已知的跨期重引例。</p>
  <div id="specialReuse"></div>
  <div class="tabs"><button id="reuseExactTab">完全相同（0）</button><button id="reuseApproxTab" class="active">4-gram 近似候選</button>
    <label class="small" style="display:flex;align-items:center;gap:5px;margin-left:8px"><input type="checkbox" id="crossOnly"> 只看跨期</label></div>
  <div id="reuseTableWrap" class="scroll" style="max-height:420px"></div>
  <div id="reuseDetail" style="margin-top:10px"></div>
</section>

<section class="panel">
  <h2>6. 〈論衡·超奇〉的獨立投影與逐句預測</h2>
  <p class="section-desc">〈超奇〉沒有參與 PCA 擬合。它使用參照語料的詞表、均值、標準差與 PCA 轉換投影；特徵覆蓋率偏低，PC2/PC3 在 50 與 100 特徵間會變號，位置應謹慎解讀。逐句預測來自既有 v3 正式保存結果，不是由 PCA 位置換算。</p>
  <div id="chaoyiCards" class="grid cards"></div>
  <div id="chaoyiMeta" style="margin-top:10px"></div>
  <div class="grid two-col" style="margin-top:12px">
    <div>
      <h3>投影與近鄰</h3>
      <div id="chaoyiNeighbors" class="small"></div>
      <h3 style="margin-top:14px">與近鄰的共同特徵</h3>
      <div id="chaoyiShared" class="small"></div>
    </div>
    <div>
      <h3>逐句預測</h3>
      <div class="controls" style="margin-bottom:6px">
        <label class="small"><input type="checkbox" id="chaoyiErrorsOnly"> 只顯示誤判</label>
        <span id="chaoyiPredSummary" class="small muted"></span>
      </div>
      <div class="scroll" style="max-height:520px"><table class="data" id="chaoyiPredTable"></table></div>
    </div>
  </div>
</section>

<section class="panel">
  <h2>7. 方法、核驗與檔案</h2>
  <div id="methodNotes"></div>
  <div class="footer">
    可重跑：<code>python scripts/exploration/build_exploration_data.py</code> →
    <code>python scripts/exploration/verify_exploration.py</code> →
    <code>python scripts/exploration/build_exploration_html.py</code>。
    資料與矩陣在 <code>output/exploration/data/</code>；本頁不依賴 CDN，可直接雙擊開啟。
  </div>
</section>

</div>
<script>__PLOTLY_JS__</script>
<script>
const DATA = __DATA_JSON__;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (x, d=2) => Number(x).toFixed(d);
const pct = (x, d=2) => (Number(x)*100).toFixed(d) + "%";
const state = {feature:100, view:"2d", colorBy:"period", author:"all", genre:"all", work:"all",
  showChaoyi:true, selectedWork:null, pc:1, search:"", reuseMode:"approx", crossOnly:false,
  chaoyiErrorsOnly:false};
const workById = Object.fromEntries(DATA.works.map(w => [w.work_id, w]));
const authorColors = {
  "劉安":"#1f77b4","司馬遷":"#ff7f0e","揚雄":"#2ca02c","劉向":"#d62728","司馬談":"#9467bd",
  "王褒":"#8c564b","劉歆":"#e377c2","王充":"#4d4d4d","班固":"#bcbd22","王逸":"#17becf",
  "桓譚":"#7fb3d5","鄭玄":"#f5b041","應劭":"#58d68d","趙岐":"#ec7063","何休":"#af7ac5"
};
const genreColors = {
  "子書":"#2b6cb0","史書":"#c53030","書錄/目錄":"#b7791f","書信":"#6b46c1",
  "學術評論":"#2f855a","序跋":"#c05621","論":"#4a5568"
};
const periodColors = {"西漢":"#2b6cb0","東漢":"#c53030"};
const COLOR_FALLBACK = "#718096";
const plotConfig = {responsive:true, displaylogo:false, scrollZoom:true};

function colorFor(w){
  if(state.colorBy === "period") return periodColors[w.period] || COLOR_FALLBACK;
  if(state.colorBy === "author") return authorColors[w.author] || COLOR_FALLBACK;
  return genreColors[w.genre_group] || COLOR_FALLBACK;
}
function filteredWorks(){
  return DATA.works.filter(w => {
    if(state.author !== "all" && w.author !== state.author) return false;
    if(state.genre !== "all" && w.genre_group !== state.genre) return false;
    if(state.work !== "all" && w.work_id !== state.work) return false;
    return true;
  });
}
function shortText(w){
  return w.short_flag ? `短篇：${w.token_count} 詞（<${DATA.meta.overview.short_threshold_tokens}），頻率估計可能不穩定` : `詞數 ${w.token_count}`;
}
function hoverText(w, n){
  const c = DATA.pca[String(n)].coords[w.work_id];
  const lines = [
    `${w.work_id}｜${w.work_title}`,
    `${w.author}｜${w.period}｜${w.genre_group}`,
    `句數 ${w.sentence_count}｜漢字 ${w.char_count}｜詞數 ${w.token_count}`,
    `PC1 ${fmt(c.PC1,3)}｜PC2 ${fmt(c.PC2,3)}｜PC3 ${fmt(c.PC3,3)}`
  ];
  if(w.short_flag) lines.push("⚠ 短篇：頻率估計可能不穩定");
  return lines.join("\n");
}
function makeReferenceTrace(is3d){
  const n = state.feature;
  const ws = filteredWorks();
  const trace = {type: is3d ? "scatter3d" : "scatter", mode:"markers",
    name:"參照篇章", x:[], y:[], z:[], text:[], customdata:[],
    marker:{size:[], color:[], symbol:"circle", line:{color:"#ffffff", width:1}},
    hoverinfo:"text", hovertemplate:null};
  ws.forEach(w => {
    const c = DATA.pca[String(n)].coords[w.work_id];
    trace.x.push(c.PC1); trace.y.push(c.PC2); trace.z.push(c.PC3);
    trace.text.push(hoverText(w, n));
    trace.customdata.push(w.work_id);
    trace.marker.color.push(colorFor(w));
    trace.marker.size.push(w.work_id === state.selectedWork ? 15 : (w.short_flag ? 7 : 9));
  });
  if(!is3d){ delete trace.z; }
  return trace;
}
function makeChaoyiTrace(is3d){
  const n = state.feature;
  const p = DATA.pca[String(n)].chaoyi;
  const trace = {type: is3d ? "scatter3d" : "scatter", mode:"markers",
    name:"〈超奇〉（留出投影）", x:[p.PC1], y:[p.PC2], z:[p.PC3],
    text:[`〈論衡·超奇〉（留出投影，未參與擬合）\n王充｜東漢｜129 句｜1,438 詞\nPC1 ${fmt(p.PC1,3)}｜PC2 ${fmt(p.PC2,3)}｜PC3 ${fmt(p.PC3,3)}\n特徵覆蓋 ${pct(p.feature_overlap_ratio,1)}`],
    customdata:["E01"],
    marker:{size:16, color:"#111111", symbol:is3d ? "diamond" : "star",
      line:{color:"#f6ad55", width:2}},
    hoverinfo:"text"};
  if(!is3d) delete trace.z;
  return trace;
}
function layout2d(n){
  const ev = DATA.pca[String(n)].explained;
  return {height:560, margin:{l:58,r:20,t:18,b:48},
    xaxis:{title:`PC1 (${pct(ev[0])})`, zeroline:true, zerolinecolor:"#cbd5e0", gridcolor:"#ece7dc"},
    yaxis:{title:`PC2 (${pct(ev[1])})`, zeroline:true, zerolinecolor:"#cbd5e0", gridcolor:"#ece7dc"},
    hovermode:"closest", showlegend:false, plot_bgcolor:"#fffdf8", paper_bgcolor:"#fffdf8"};
}
function layout3d(n){
  const ev = DATA.pca[String(n)].explained;
  return {height:680, margin:{l:0,r:0,t:18,b:0},
    scene:{xaxis:{title:`PC1 (${pct(ev[0])})`, gridcolor:"#ece7dc"},
      yaxis:{title:`PC2 (${pct(ev[1])})`, gridcolor:"#ece7dc"},
      zaxis:{title:`PC3 (${pct(ev[2])})`, gridcolor:"#ece7dc"},
      camera:{eye:{x:1.55,y:1.45,z:1.15}}},
    showlegend:false, paper_bgcolor:"#fffdf8"};
}
function renderPCA(){
  const n = state.feature;
  const ref2 = makeReferenceTrace(false);
  const ref3 = makeReferenceTrace(true);
  const traces2 = state.showChaoyi ? [ref2, makeChaoyiTrace(false)] : [ref2];
  const traces3 = state.showChaoyi ? [ref3, makeChaoyiTrace(true)] : [ref3];
  Plotly.react("pca2d", traces2, layout2d(n), plotConfig);
  Plotly.react("pca3d", traces3, layout3d(n), plotConfig);
  const ev = DATA.pca[String(n)].explained;
  const cum = DATA.pca[String(n)].cumulative;
  $("varianceNote").innerHTML = `特徵設定 <b>${n}</b>：PC1 ${pct(ev[0])}、PC2 ${pct(ev[1])}、PC3 ${pct(ev[2])}；
    前二累計 <b>${pct(cum[1])}</b>，前三累計 <b>${pct(cum[2])}</b>。
    ${n===100 ? "100 詞覆蓋全庫 " + pct(DATA.meta.feature_coverage["100"].coverage,1) + " 的詞次。" :
      "50 詞覆蓋全庫 " + pct(DATA.meta.feature_coverage["50"].coverage,1) + " 的詞次。"}`;
  renderLegend();
}
function renderLegend(){
  const values = state.colorBy === "period" ? ["西漢","東漢"] :
    state.colorBy === "author" ? [...new Set(DATA.works.map(w => w.author))] :
    [...new Set(DATA.works.map(w => w.genre_group))];
  const map = state.colorBy === "period" ? periodColors : state.colorBy === "author" ? authorColors : genreColors;
  $("legend").innerHTML = values.map(v => `<span class="chip"><span class="dot" style="background:${map[v]||COLOR_FALLBACK}"></span>${esc(v)}</span>`).join("");
}
function selectWork(workId){
  state.selectedWork = workId;
  renderPCA();
  renderDetail();
  renderHeatmapNeighbors();
}
function renderChaoyiDetail(){
  const n = state.feature;
  const p = DATA.pca[String(n)].chaoyi;
  const nb = DATA.chaoyi[String(n)].neighbors.slice(0,5);
  const text = DATA.chaoyi_predictions.map(x => x.text_original).join("");
  $("workDetail").innerHTML = `
    <div class="detail-head"><h3 style="margin:0">E01｜論衡·超奇</h3>
      <div><span class="badge east">東漢</span><span class="badge">王充</span><span class="badge">留出投影</span></div></div>
    <table class="meta-table">
      <tr><td>句數／詞數</td><td>129 句／1,438 詞</td></tr>
      <tr><td>收錄範圍</td><td>${esc(p.excerpt_range || "全篇")}</td></tr>
      <tr><td>底本</td><td>${esc(p.base_page || "論衡/39")}（修訂 ${esc(p.revision || "")}）</td></tr>
      <tr><td>來源</td><td><a href="${esc(p.base_url || "")}" target="_blank" rel="noopener">底本頁</a> ·
        <a href="${esc(p.fixed_url || "")}" target="_blank" rel="noopener">固定修訂網址</a></td></tr>
      <tr><td>投影座標</td><td>PC1 ${fmt(p.PC1,3)}｜PC2 ${fmt(p.PC2,3)}｜PC3 ${fmt(p.PC3,3)}</td></tr>
      <tr><td>特徵覆蓋</td><td>${p.feature_overlap_count} / ${p.token_count} 詞（${pct(p.feature_overlap_ratio,1)}）；未參與 52 篇擬合</td></tr>
    </table>
    <div class="warn">〈超奇〉不在 52 篇相似度熱圖中；它的投影與近鄰見下方第 6 節。PC 位置不是預測機率。</div>
    <h3>原文（129 句）</h3><pre class="original" id="chaoyiDetailText"></pre>
    <h3>投影近鄰（${n} 特徵）</h3>
    ${nb.map(x => `<button class="ghost" onclick="selectWork('${x.target_work_id}')">${x.rank}. ${x.target_work_id} ${esc(x.target_title)} <span class="muted">${fmt(x.similarity,3)}</span></button>`).join(" ")}
    <div class="note" style="margin-top:8px">完整 129 句預測表在第 6 節；此處不重複列出。</div>`;
  $("chaoyiDetailText").textContent = text;
}
function renderDetail(){
  if(state.selectedWork === "E01"){ renderChaoyiDetail(); return; }
  const work = workById[state.selectedWork];
  if(!work){ $("workDetail").innerHTML = '<span class="muted">點選圖上的一點，或從下方篇章清單選擇。</span>'; return; }
  const n = state.feature;
  const c = DATA.pca[String(n)].coords[work.work_id];
  const neighbors = (DATA.neighbors[String(n)][work.work_id] || []).slice(0,5);
  const sents = DATA.sentences.filter(s => s.work_id === work.work_id);
  const predRows = sents.map(s => ({s, p:DATA.predictions[s.sent_id]})).filter(x => x.p);
  const predHtml = predRows.length ? `<div class="scroll" style="max-height:240px"><table class="data"><thead><tr><th>句</th><th>預測</th><th>P(東漢)</th><th>結果</th></tr></thead><tbody>${predRows.map(({s,p}) => `<tr><td>${esc(s.text_original)}</td><td>${esc(p.period_pred)}</td><td class="num">${fmt(p.prob_east,3)}</td><td>${p.correct ? "✓" : "✗"}</td></tr>`).join("")}</tbody></table></div>` : '<div class="muted small">此篇沒有正式保存的逐句預測（僅〈超奇〉與 v3 測試集句子有）。</div>';
  $("workDetail").innerHTML = `
    <div class="detail-head"><h3 style="margin:0">${work.work_id}｜${esc(work.work_title)}</h3>
      <div><span class="badge ${work.period==='西漢'?'west':'east'}">${work.period}</span>
      <span class="badge">${esc(work.author)}</span><span class="badge">${esc(work.genre_group)}</span>
      ${work.short_flag?'<span class="badge short">短篇</span>':''}</div></div>
    <table class="meta-table">
      <tr><td>句數／字數</td><td>${work.sentence_count} 句／${work.char_count} 漢字／${work.token_count} 詞</td></tr>
      <tr><td>收錄範圍</td><td>${esc(work.excerpt_range)}</td></tr>
      <tr><td>底本</td><td>${esc(work.base_page)}（修訂 ${esc(work.revision)}）</td></tr>
      <tr><td>來源</td><td><a href="${esc(work.base_url)}" target="_blank" rel="noopener">底本頁</a> ·
        <a href="${esc(work.fixed_url)}" target="_blank" rel="noopener">固定修訂網址</a></td></tr>
      <tr><td>PC 座標</td><td>PC1 ${fmt(c.PC1,3)}｜PC2 ${fmt(c.PC2,3)}｜PC3 ${fmt(c.PC3,3)}</td></tr>
    </table>
    ${work.short_flag?`<div class="warn">短篇提醒：本篇只有 ${work.token_count} 詞（<${DATA.meta.overview.short_threshold_tokens}），相對頻率與 PCA 位置可能不穩定。</div>`:''}
    <h3>原文</h3><pre class="original" id="originalText"></pre>
    <h3>近鄰（${n} 特徵，cosine）</h3>
    ${neighbors.length?`<div>${neighbors.map(x => `<button class="ghost" onclick="selectWork('${x.target_work_id}')">${x.target_work_id} ${esc(x.target_title)} <span class="muted">${fmt(x.similarity,3)}</span></button>`).join(" ")}</div>`:'<span class="muted">無</span>'}
    <h3>逐句預測（僅正式保存的句子）</h3>${predHtml}
    <div class="note" style="margin-top:8px">PCA 位置不是預測機率；請勿把圖上距離或方向解讀為「東漢概率」。</div>`;
  $("originalText").textContent = work.original_text;
}
function renderWorkTable(){
  const rows = DATA.works.map(w => `<tr class="clickable" onclick="selectWork('${w.work_id}')">
    <td>${w.work_id}</td><td>${esc(w.work_title)}</td><td>${esc(w.author)}</td>
    <td><span class="badge ${w.period==='西漢'?'west':'east'}">${w.period}</span></td>
    <td>${esc(w.genre_group)}</td><td class="num">${w.sentence_count}</td>
    <td class="num">${w.token_count}</td><td>${w.short_flag?'<span class="badge short">短</span>':''}</td></tr>`).join("");
  $("workTable").innerHTML = `<thead><tr><th>ID</th><th>篇名</th><th>作者</th><th>分期</th><th>文類</th><th>句</th><th>詞</th><th></th></tr></thead><tbody>${rows}</tbody>`;
}
function renderPCWords(){
  const n = String(state.feature);
  const ev = DATA.word_evidence[n].filter(x => Number(x.pc) === state.pc);
  const pos = ev.filter(x => x.direction === "positive").sort((a,b) => Number(a.rank)-Number(b.rank)).slice(0,12);
  const neg = ev.filter(x => x.direction === "negative").sort((a,b) => Number(a.rank)-Number(b.rank)).slice(0,12);
  const btn = (x) => `<button class="word-btn" onclick="showWord('${esc(x.feature)}',${state.pc},'${x.direction}')">${esc(x.feature)} <b>${Number(x.loading)>=0?'+':''}${fmt(x.loading,3)}</b></button>`;
  $("wordColumns").innerHTML = `<div><h3>正向（PC${state.pc} 正端）</h3><div class="wordlist">${pos.map(btn).join("")}</div></div>
    <div><h3>負向（PC${state.pc} 負端）</h3><div class="wordlist">${neg.map(btn).join("")}</div></div>`;
}
function showWord(feature, pc, direction){
  const n = String(state.feature);
  const row = DATA.word_evidence[n].find(x => x.feature === feature && Number(x.pc) === pc && x.direction === direction);
  if(!row){ $("wordEvidence").innerHTML = '<span class="muted">找不到此詞。</span>'; return; }
  const ex = DATA.word_examples[n].filter(x => x.feature === feature && Number(x.pc) === pc && x.direction === direction);
  const exHtml = ex.length ? ex.map(x => `<div class="example"><div class="text">${esc(x.text_original)}</div>
    <div class="tiny"><a href="${esc(x.fixed_url)}" target="_blank" rel="noopener">${x.sent_id}｜${esc(x.work_title)}｜${esc(x.author)}｜${x.period}</a></div></div>`).join("") :
    '<div class="muted small">此詞沒有可顯示的原句例子。</div>';
  $("wordEvidence").innerHTML = `<div class="big">${esc(feature)} <span class="small muted">PC${pc} ${direction}｜loading ${fmt(row.loading,3)}</span></div>
    <div class="kv" style="margin-top:8px">
      <span class="k">全庫次數</span><span>${row.total_count}</span>
      <span class="k">出現篇章</span><span>${row.doc_count} 篇</span>
      <span class="k">出現作者</span><span>${row.author_count} 位</span>
      <span class="k">西漢</span><span>${row.west_count} / ${row.west_total_tokens} 詞（${pct(row.west_freq,3)}）</span>
      <span class="k">東漢</span><span>${row.east_count} / ${row.east_total_tokens} 詞（${pct(row.east_freq,3)}）</span>
      <span class="k">最大作者</span><span>${esc(row.top_author)} ${pct(row.max_author_share,1)}</span>
      <span class="k">最大篇章</span><span>${esc(row.top_work_id)} ${pct(row.max_work_share,1)}</span>
      <span class="k">證據</span><span>${esc(row.concentration)}</span>
    </div>
    ${row.concentration !== "分散" ? '<div class="warn" style="margin-top:8px">此詞的來源集中或次數偏少，不能據此概括某一時期的文風。</div>' : ''}
    <h3 style="margin-top:10px">原句</h3>${exHtml}`;
}
function renderSearch(){
  const q = state.search.trim();
  if(!q){ $("searchResults").innerHTML = '<span class="muted">輸入詞語或句子片段，查詢特徵詞與原句。</span>'; return; }
  const n = String(state.feature);
  const words = DATA.word_evidence[n].filter(x => String(x.feature).includes(q)).slice(0,20);
  const sents = DATA.sentences.filter(s => String(s.text_original).includes(q) || String(s.text_normalized).includes(q)).slice(0,30);
  const wordHtml = words.length ? `<div><b>特徵詞</b><div class="wordlist">${words.map(x => `<button class="word-btn" onclick="showWord('${esc(x.feature)}',${x.pc},'${x.direction}')">${esc(x.feature)} <span class="tiny">PC${x.pc} ${x.direction}</span></button>`).join("")}</div></div>` : "";
  const sentHtml = sents.length ? `<div style="margin-top:8px"><b>原句（${sents.length} 筆，最多 30）</b>${sents.map(s => `<div class="example"><div class="text">${esc(s.text_original)}</div><div class="tiny"><a href="${esc(s.fixed_url)}" target="_blank" rel="noopener">${s.sent_id}｜${esc(s.work_title)}｜${esc(s.author)}｜${s.period}</a> ${DATA.predictions[s.sent_id]?`<span class="badge">${esc(DATA.predictions[s.sent_id].period_pred)} P=${fmt(DATA.predictions[s.sent_id].prob_east,3)}</span>`:''}</div></div>`).join("")}</div>` : '<div class="muted small" style="margin-top:8px">沒有匹配原句。</div>';
  $("searchResults").innerHTML = wordHtml + sentHtml;
}
function renderHeatmap(){
  const n = String(state.feature);
  const sim = DATA.similarity[n];
  Plotly.newPlot("heatmap", [{z:sim.matrix, x:sim.labels, y:sim.labels, type:"heatmap",
    colorscale:"Viridis", hovertemplate:"%{y} × %{x}<br>cosine similarity %{z:.3f}<extra></extra>"}],
    {height:860, margin:{l:70,r:20,t:18,b:70}, paper_bgcolor:"#fffdf8", plot_bgcolor:"#fffdf8",
     xaxis:{tickfont:{size:8}, tickangle:-90}, yaxis:{tickfont:{size:8}, autorange:"reversed"}}, plotConfig);
  $("heatmap").on("plotly_click", (ev) => {
    const p = ev.points && ev.points[0]; if(p) selectWork(String(p.y));
  });
  renderHeatmapNeighbors();
}
function renderHeatmapNeighbors(){
  const work = workById[state.selectedWork];
  if(!work){ $("heatmapDetail").innerHTML = '<span class="muted">點熱圖格子或選擇一篇，查看近鄰。</span>'; $("heatmapNeighbors").innerHTML = ""; return; }
  const n = String(state.feature);
  const nb = DATA.neighbors[n][work.work_id] || [];
  $("heatmapDetail").innerHTML = `<div class="big">${work.work_id}｜${esc(work.work_title)}</div>
    <div class="small muted">${esc(work.author)}｜${work.period}｜${esc(work.genre_group)}</div>
    <div class="note" style="margin-top:8px">相似度 = 在 ${n} 維 z-score 特徵上的 cosine similarity；不是 PCA 二維距離。</div>`;
  $("heatmapNeighbors").innerHTML = `<h3>最近 5 篇</h3>${nb.map(x => `<button class="ghost" onclick="selectWork('${x.target_work_id}')">${x.target_work_id} ${esc(x.target_title)} <span class="muted">${fmt(x.similarity,3)}</span></button>`).join(" ")}`;
}
function renderSpecialReuse(){
  const s = DATA.reuse.special;
  $("specialReuse").innerHTML = `<div class="reuse-card special">
    <div><b>已知重引例回查：W06-015／E11-018</b>
      <span class="badge ${s.detected_by_approx?'cross':'short'}">${s.detected_by_approx?'近似方法檢出':'未檢出'}</span></div>
    <div class="small" style="margin-top:6px">完全相同：${s.exact_normalized_equal?'是':'否'}；4-gram 共享 ${s.shared_ngrams}；containment ${fmt(s.containment,3)}；Jaccard ${fmt(s.jaccard,3)}；最長共同片段 ${s.lcs_len} 字。</div>
    <div class="reuse-pair" style="margin-top:8px">
      <div><div class="tiny muted">W06-015｜法言·吾子｜西漢</div><div class="reuse-text">${esc(s.text_a)}</div><a class="tiny" href="${esc(s.url_a)}" target="_blank" rel="noopener">來源</a></div>
      <div><div class="tiny muted">E11-018｜漢書·藝文志｜東漢</div><div class="reuse-text">${esc(s.text_b)}</div><a class="tiny" href="${esc(s.url_b)}" target="_blank" rel="noopener">來源</a></div>
    </div>
    <div class="small muted" style="margin-top:6px">共同片段：${esc(s.lcs_text)}</div>
    <div class="small warn" style="margin-top:6px">僅為候選；不判定誰引用誰，也不判定年代先後。</div>
  </div>`;
}
function renderReuseTable(){
  const list = state.reuseMode === "exact" ? DATA.reuse.exact : DATA.reuse.approx;
  const filtered = state.crossOnly ? list.filter(x => x.cross_period) : list;
  if(!filtered.length){
    $("reuseTableWrap").innerHTML = `<div class="muted" style="padding:10px">${state.reuseMode==="exact"?"去重後語料沒有跨篇正規化完全相同句。":"目前沒有符合條件的近似候選。"}</div>`;
    return;
  }
  const rows = filtered.slice(0,100).map((x, i) => `<tr class="clickable" onclick="showReuse(${i})">
    <td>${state.reuseMode==="exact"?"完全相同":"4-gram"}</td>
    <td>${esc(x.work_id_a)}／${esc(x.work_id_b)} ${x.cross_period?'<span class="badge cross">跨期</span>':''}</td>
    <td>${esc(x.period_a)}／${esc(x.period_b)}</td>
    <td class="num">${fmt(x.similarity,3)}</td>
    <td class="num">${state.reuseMode==="exact"?"—":fmt(x.containment,3)}</td>
    <td class="num">${state.reuseMode==="exact"?"—":fmt(x.jaccard,3)}</td>
    <td class="num">${x.shared_ngrams}</td>
    <td>${esc((x.lcs_text||"").slice(0,24))}</td></tr>`).join("");
  $("reuseTableWrap").innerHTML = `<table class="data"><thead><tr><th>方法</th><th>篇章</th><th>分期</th><th>相似度</th><th>containment</th><th>Jaccard</th><th>共享 4-gram</th><th>共同片段</th></tr></thead><tbody>${rows}</tbody></table>`;
  window._reuseCurrent = filtered;
}
function showReuse(i){
  const x = (window._reuseCurrent || [])[i];
  if(!x) return;
  $("reuseDetail").innerHTML = `<div class="reuse-card">
    <div><b>${esc(x.sent_id_a)}／${esc(x.sent_id_b)}</b> <span class="small muted">${state.reuseMode==="exact"?"正規化完全相同":"4-gram containment"}</span></div>
    <div class="reuse-pair" style="margin-top:8px">
      <div><div class="tiny muted">${esc(x.work_id_a)}｜${esc(x.title_a)}｜${esc(x.author_a)}｜${esc(x.period_a)}</div><div class="reuse-text">${esc(x.text_a)}</div><a class="tiny" href="${esc(x.url_a)}" target="_blank" rel="noopener">來源</a></div>
      <div><div class="tiny muted">${esc(x.work_id_b)}｜${esc(x.title_b)}｜${esc(x.author_b)}｜${esc(x.period_b)}</div><div class="reuse-text">${esc(x.text_b)}</div><a class="tiny" href="${esc(x.url_b)}" target="_blank" rel="noopener">來源</a></div>
    </div>
    <div class="small" style="margin-top:6px">similarity ${fmt(x.similarity,3)}；containment ${fmt(x.containment,3)}；Jaccard ${fmt(x.jaccard,3)}；共享 4-gram ${x.shared_ngrams}；最長共同片段 ${x.lcs_len} 字。</div>
    <div class="small warn">僅為候選；不判定借用方向或年代先後。</div></div>`;
}
function renderChaoyi(){
  const n = String(state.feature);
  const p = DATA.pca[n].chaoyi;
  const c = DATA.chaoyi[n];
  const preds = DATA.chaoyi_predictions;
  const east = preds.filter(x => x.period_pred === "東漢").length;
  const meanP = preds.reduce((a,b) => a + Number(b.prob_east), 0) / Math.max(preds.length,1);
  $("chaoyiCards").innerHTML = `
    <div class="card"><div class="k">投影 PC1／PC2／PC3</div><div class="v">${fmt(p.PC1,2)}／${fmt(p.PC2,2)}／${fmt(p.PC3,2)}</div><div class="s">${n} 特徵；未參與擬合</div></div>
    <div class="card"><div class="k">特徵覆蓋</div><div class="v">${pct(p.feature_overlap_ratio,1)}</div><div class="s">${p.feature_overlap_count} / ${p.token_count} 詞</div></div>
    <div class="card"><div class="k">逐句預測</div><div class="v">${east}／${preds.length}</div><div class="s">判為東漢；平均 P(東漢) ${fmt(meanP,3)}</div></div>
    <div class="card"><div class="k">最近篇章</div><div class="v">${esc(c.neighbors[0]?.target_work_id || "")}</div><div class="s">${esc(c.neighbors[0]?.target_title || "")} ${c.neighbors[0]?fmt(c.neighbors[0].similarity,3):""}</div></div>`;
  $("chaoyiMeta").innerHTML = `<div class="note">來源：<a href="${esc(p.base_url || "")}" target="_blank" rel="noopener">${esc(p.base_page || "論衡/39")}</a>（修訂 ${esc(p.revision || "")}）｜收錄：${esc(p.excerpt_range || "全篇")}｜特徵覆蓋 ${p.feature_overlap_count}/${p.token_count}（${pct(p.feature_overlap_ratio,1)}）。</div>
    <details style="margin-top:6px"><summary>〈超奇〉原文（129 句）</summary><pre class="original" id="chaoyiFullText"></pre></details>`;
  $("chaoyiFullText").textContent = DATA.chaoyi_predictions.map(x => x.text_original).join("");
  $("chaoyiNeighbors").innerHTML = c.neighbors.map(x => `<button class="ghost" onclick="selectWork('${x.target_work_id}')">${x.rank}. ${x.target_work_id} ${esc(x.target_title)} <span class="muted">${fmt(x.similarity,3)}</span></button>`).join(" ");
  const top3 = c.neighbors.slice(0,3);
  $("chaoyiShared").innerHTML = top3.map(nb => {
    const rows = (c.shared[nb.target_work_id] || []).slice(0,8);
    return `<div class="reuse-card"><b>${nb.target_work_id} ${esc(nb.target_title)}</b>
      <div class="small muted">${esc(nb.target_author)}｜${nb.target_period}｜similarity ${fmt(nb.similarity,3)}</div>
      <table class="data" style="margin-top:5px"><thead><tr><th>詞</th><th>z 超奇</th><th>z 對方</th><th>全庫次數</th><th>篇</th><th>作者</th></tr></thead>
      <tbody>${rows.map(r => `<tr><td>${esc(r.feature)}</td><td class="num">${fmt(r.z_chaoyi,2)}</td><td class="num">${fmt(r.z_neighbor,2)}</td><td class="num">${r.total_count}</td><td class="num">${r.doc_count}</td><td class="num">${r.author_count}</td></tr>`).join("")}</tbody></table></div>`;
  }).join("");
  $("chaoyiPredSummary").textContent = `${east}/${preds.length} 判為東漢；平均 P(東漢)=${fmt(meanP,3)}`;
  renderChaoyiPredictions();
}
function renderChaoyiPredictions(){
  const preds = DATA.chaoyi_predictions.filter(x => !state.chaoyiErrorsOnly || x.period_pred !== "東漢");
  const rows = preds.map(x => `<tr><td>${esc(x.text_original)}</td><td>${esc(x.period_pred)}</td><td class="num">${fmt(x.prob_east,3)}</td><td>${x.correct?"✓":"✗"}</td></tr>`).join("");
  $("chaoyiPredTable").innerHTML = `<thead><tr><th>句</th><th>預測</th><th>P(東漢)</th><th>結果</th></tr></thead><tbody>${rows}</tbody>`;
}
function renderOverview(){
  const ov = DATA.meta.overview;
  const e100 = DATA.pca["100"].explained, c100 = DATA.pca["100"].cumulative;
  const e50 = DATA.pca["50"].explained, c50 = DATA.pca["50"].cumulative;
  $("overviewCards").innerHTML = `
    <div class="card"><div class="k">參照篇章</div><div class="v">${ov.n_works}</div><div class="s">篇／節選；非句子</div></div>
    <div class="card"><div class="k">可建模句</div><div class="v">${ov.n_sentences}</div><div class="s">西漢 ${ov.period_sentence_counts["西漢"]}／東漢 ${ov.period_sentence_counts["東漢"]}</div></div>
    <div class="card"><div class="k">全庫詞數</div><div class="v">${(ov.period_token_counts["西漢"]+ov.period_token_counts["東漢"]).toLocaleString()}</div><div class="s">西漢 ${ov.period_token_counts["西漢"].toLocaleString()}／東漢 ${ov.period_token_counts["東漢"].toLocaleString()}</div></div>
    <div class="card"><div class="k">100 特徵 PCA</div><div class="v">${pct(c100[2])}</div><div class="s">PC1 ${pct(e100[0])}·PC2 ${pct(e100[1])}·PC3 ${pct(e100[2])}</div></div>
    <div class="card"><div class="k">50 特徵 PCA</div><div class="v">${pct(c50[2])}</div><div class="s">PC1 ${pct(e50[0])}·PC2 ${pct(e50[1])}·PC3 ${pct(e50[2])}</div></div>
    <div class="card"><div class="k">特徵覆蓋</div><div class="v">${pct(DATA.meta.feature_coverage["100"].coverage,1)}</div><div class="s">100 詞；50 詞 ${pct(DATA.meta.feature_coverage["50"].coverage,1)}</div></div>`;
  const shortsByTokens = [...ov.short_works].sort((a,b) => a.tokens - b.tokens);
  const shortest = shortsByTokens[0], longestShort = shortsByTokens[shortsByTokens.length-1];
  const warnings = (DATA.meta.warnings && DATA.meta.warnings["100"]) || [];
  $("overviewNotes").innerHTML = `<div class="note">短篇提醒：${ov.short_works.length}／${ov.n_works} 篇少於 ${ov.short_threshold_tokens} 詞；最短 ${shortest.work_id} 只有 ${shortest.tokens} 詞，最長的短篇 ${longestShort.work_id} 有 ${longestShort.tokens} 詞。${warnings.length?'<br>qhchina 警告：'+esc(warnings[0]):''}</div>
    <div class="warn">100 詞只覆蓋全庫 ${pct(DATA.meta.feature_coverage["100"].coverage,1)} 的詞次；50 詞只覆蓋 ${pct(DATA.meta.feature_coverage["50"].coverage,1)}。PCA 與相似度是「高頻詞風格」的近似，不是完整詞彙。</div>
    <div class="note">圖上的位置不是分類機率；〈超奇〉是留出投影，不是測試集準確率。主樣本分類結果見 output/v3/。</div>`;
}
function renderMethodNotes(){
  const d = DATA.meta.definitions;
  $("methodNotes").innerHTML = `<div class="kv">
    <span class="k">分析單位</span><span>${esc(d.unit)}</span>
    <span class="k">特徵選取</span><span>${esc(d.feature_selection)}</span>
    <span class="k">頻率</span><span>${esc(d.frequency)}</span>
    <span class="k">標準化</span><span>${esc(d.zscore)}</span>
    <span class="k">PCA</span><span>${esc(d.pca)}</span>
    <span class="k">相似度</span><span>${esc(d.similarity)}</span>
    <span class="k">投影</span><span>${esc(d.projection)}</span>
    <span class="k">重引規則</span><span>${esc(DATA.reuse.rules.exact)} ${esc(DATA.reuse.rules.approx)} 短句排除 ${DATA.reuse.rules.short_sentences_excluded} 句（<8 漢字）。</span>
  </div>
  <div class="ok" style="margin-top:10px">核驗：52 篇／1,654 句（702 西漢、952 東漢）；特徵矩陣不含分期／作者／文類；2D／3D 共用 PC1、PC2；〈超奇〉不參與擬合；相似度矩陣對稱、對角 1、無缺失。</div>`;
}
function populateSelects(){
  const authors = [...new Set(DATA.works.map(w => w.author))].sort();
  const genres = [...new Set(DATA.works.map(w => w.genre_group))].sort();
  $("authorSelect").innerHTML = '<option value="all">全部作者</option>' + authors.map(a => `<option value="${esc(a)}">${esc(a)}</option>`).join("");
  $("genreSelect").innerHTML = '<option value="all">全部文類</option>' + genres.map(g => `<option value="${esc(g)}">${esc(g)}</option>`).join("");
  const works = [...DATA.works].sort((a,b) => a.work_id.localeCompare(b.work_id));
  $("workSelect").innerHTML = '<option value="all">全部篇章</option><option value="E01">E01｜論衡·超奇（留出投影）</option>' + works.map(w => `<option value="${esc(w.work_id)}">${w.work_id}｜${esc(w.work_title)}</option>`).join("");
}
function resetState(){
  state.feature = 100; state.view = "2d"; state.colorBy = "period";
  state.author = "all"; state.genre = "all"; state.work = "all";
  state.showChaoyi = true; state.pc = 1; state.crossOnly = false; state.chaoyiErrorsOnly = false;
  $("featureSelect").value = "100"; $("colorSelect").value = "period";
  $("authorSelect").value = "all"; $("genreSelect").value = "all"; $("workSelect").value = "all";
  $("showChaoyi").checked = true; $("crossOnly").checked = false; $("chaoyiErrorsOnly").checked = false;
  $("view2d").classList.add("active"); $("view3d").classList.remove("active");
  $("pca2d").style.display = "block"; $("pca3d").style.display = "none";
  document.querySelectorAll("#pcTabs button").forEach(b => b.classList.toggle("active", b.dataset.pc === "1"));
  state.selectedWork = DATA.works[0].work_id;
  renderAll();
}
function renderAll(){
  renderPCA(); renderDetail(); renderPCWords(); renderSearch();
  renderHeatmap(); renderSpecialReuse(); renderReuseTable(); renderChaoyi();
  renderWorkTable();
}
function init(){
  populateSelects(); renderOverview(); renderMethodNotes();
  $("featureSelect").onchange = (e) => { state.feature = Number(e.target.value); renderAll(); };
  $("colorSelect").onchange = (e) => { state.colorBy = e.target.value; renderPCA(); };
  $("authorSelect").onchange = (e) => { state.author = e.target.value; renderPCA(); };
  $("genreSelect").onchange = (e) => { state.genre = e.target.value; renderPCA(); };
  $("workSelect").onchange = (e) => { state.work = e.target.value; if(e.target.value !== "all") selectWork(e.target.value); else renderPCA(); };
  $("showChaoyi").onchange = (e) => { state.showChaoyi = e.target.checked; renderPCA(); };
  $("view2d").onclick = () => { state.view = "2d"; $("pca2d").style.display = "block"; $("pca3d").style.display = "none"; $("view2d").classList.add("active"); $("view3d").classList.remove("active"); Plotly.Plots.resize($("pca2d")); };
  $("view3d").onclick = () => { state.view = "3d"; $("pca2d").style.display = "none"; $("pca3d").style.display = "block"; $("view3d").classList.add("active"); $("view2d").classList.remove("active"); Plotly.Plots.resize($("pca3d")); };
  $("resetBtn").onclick = resetState;
  $("pcTabs").onclick = (e) => { const b = e.target.closest("button"); if(!b) return; state.pc = Number(b.dataset.pc); document.querySelectorAll("#pcTabs button").forEach(x => x.classList.toggle("active", x === b)); renderPCWords(); };
  $("searchInput").oninput = (e) => { state.search = e.target.value; renderSearch(); };
  $("reuseExactTab").onclick = () => { state.reuseMode = "exact"; $("reuseExactTab").classList.add("active"); $("reuseApproxTab").classList.remove("active"); renderReuseTable(); };
  $("reuseApproxTab").onclick = () => { state.reuseMode = "approx"; $("reuseApproxTab").classList.add("active"); $("reuseExactTab").classList.remove("active"); renderReuseTable(); };
  $("crossOnly").onchange = (e) => { state.crossOnly = e.target.checked; renderReuseTable(); };
  $("chaoyiErrorsOnly").onchange = (e) => { state.chaoyiErrorsOnly = e.target.checked; renderChaoyiPredictions(); };
  state.selectedWork = "W01";
  renderAll();
  $("pca2d").on("plotly_click", (ev) => { const p = ev.points && ev.points[0]; if(p) selectWork(String(p.customdata)); });
  $("pca3d").on("plotly_click", (ev) => { const p = ev.points && ev.points[0]; if(p) selectWork(String(p.customdata)); });
  Plotly.Plots.resize($("pca2d"));
}
window.addEventListener("DOMContentLoaded", init);
</script>
</body>
</html>
"""


def main():
    bundle = build_bundle()
    data_json = json.dumps(bundle, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = HTML_TEMPLATE.replace("__TITLE__", bundle["meta"]["title"])
    html = html.replace("__SUBTITLE__", bundle["meta"]["subtitle"])
    html = html.replace("__PLOTLY_JS__", get_plotlyjs())
    html = html.replace("__DATA_JSON__", data_json)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    print(f"bundle: {len(bundle['works'])} works, {len(bundle['sentences'])} sentences, "
          f"{len(bundle['reuse']['approx'])} approx reuse rows")


if __name__ == "__main__":
    main()
