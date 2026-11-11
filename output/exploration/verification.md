# Exploration verification

Total: 80 / 80 passed

## 程式檢查

Passed: 61 / 61

- [x] 52 reference works — catalogue=52, works.csv=52
- [x] 1654 sentences — rows=1654
- [x] period sentence counts 702/952 — {'東漢': 952, '西漢': 702}
- [x] per-work sentence counts match catalogue — []
- [x] 100 features available — features=100
- [x] 100 feature matrix shape — (52, 100)
- [x] 100 feature matrix has no label columns — no period/author/genre columns
- [x] 100 z-score matrix has no NaN — NaN=0
- [x] 100 PCA coordinates shape — (52, 4), columns=['work_id', 'PC1', 'PC2', 'PC3']
- [x] 100 PCA has three components — n_components=3
- [x] 100 explained variance finite — [0.08419915546477165, 0.06410291350308325, 0.05238621513483109]
- [x] 100 similarity shape — (52, 52)
- [x] 100 similarity symmetric — max asym=0.00e+00
- [x] 100 similarity diagonal 1 — diag range=1.000000-1.000000
- [x] 100 similarity no missing — NaN=0
- [x] 100 fit has 52 documents — n_fit=52
- [x] 100 超奇 excluded from fit — E01 not in document_ids
- [x] 100 超奇 projection-only — fit_work_count=52, overlap=0.257
- [x] 100 超奇 not in works.csv — E01 absent from 52-work table
- [x] 50 features available — features=50
- [x] 50 feature matrix shape — (52, 50)
- [x] 50 feature matrix has no label columns — no period/author/genre columns
- [x] 50 z-score matrix has no NaN — NaN=0
- [x] 50 PCA coordinates shape — (52, 4), columns=['work_id', 'PC1', 'PC2', 'PC3']
- [x] 50 PCA has three components — n_components=3
- [x] 50 explained variance finite — [0.11533775652380444, 0.07806203483220789, 0.07007254286978701]
- [x] 50 similarity shape — (52, 52)
- [x] 50 similarity symmetric — max asym=0.00e+00
- [x] 50 similarity diagonal 1 — diag range=1.000000-1.000000
- [x] 50 similarity no missing — NaN=0
- [x] 50 fit has 52 documents — n_fit=52
- [x] 50 超奇 excluded from fit — E01 not in document_ids
- [x] 50 超奇 projection-only — fit_work_count=52, overlap=0.226
- [x] 50 超奇 not in works.csv — E01 absent from 52-work table
- [x] exact cross-work matches — rows=0 (deduped corpus; duplicates logged in data/v3/excluded.csv)
- [x] approximate candidates present — rows=30
- [x] W06/E11 special check detected — containment=1.000, shared=10, LCS=15
- [x] special check exact equality is false — exact_normalized_equal=false; approximate method is the one that catches it
- [x] 100 complete signed contribution sums — each top-10 neighbor has all N features; sum equals cosine
- [x] 100 contributions independently recomputed — saved z vectors and scalar cosine formula
- [x] 100 z_product independently recomputed — z_product = z_chaoyi * z_neighbor
- [x] 100 neighbor raw counts — compared with raw count matrix
- [x] 100 both-present filter — zero-count words never labelled both-present
- [x] 100 contribution categories — both above, both below, or opposite/zero
- [x] 100 saved contribution-check JSON — 10 neighbors; all-feature sum equals cosine
- [x] E02 contribution-check counts — 55 both-present; 23 both-high; 52 both-low; 25 other
- [x] 50 complete signed contribution sums — each top-10 neighbor has all N features; sum equals cosine
- [x] 50 contributions independently recomputed — saved z vectors and scalar cosine formula
- [x] 50 z_product independently recomputed — z_product = z_chaoyi * z_neighbor
- [x] 50 neighbor raw counts — compared with raw count matrix
- [x] 50 both-present filter — zero-count words never labelled both-present
- [x] 50 contribution categories — both above, both below, or opposite/zero
- [x] 50 saved contribution-check JSON — 10 neighbors; all-feature sum equals cosine
- [x] 超奇 top-5 overlap — 3/5
- [x] 超奇 top-10 overlap — 8/10
- [x] 超奇 nearest E02 in both settings — 論衡·佚文
- [x] 超奇 E05 and E03 in both top-10 — E05/E03 present in both top-10 lists
- [x] 超奇 overlap JSON computed from neighbours — {"top5_100": ["E02", "E04", "E34", "W02", "W14"], "top5_50": ["E02", "E04", "E05", "E34", "W11"], "top5_overlap": ["E02", "E04", "E34"], "top5_overlap_count": 3, "top5_only_100": ["W02", "W14"], "top5_only_50": ["E05", "W11"], "top10_100": ["E02", "E03", "E04", "E05", "E33", "E34", "W02", "W03", "W14", "W25"], "top10_50": ["E02", "E03", "E04", "E05", "E11", "E34", "W02", "W11", "W14", "W25"], "top10_overlap": ["E02", "E03", "E04", "E05", "E34", "W02", "W14", "W25"], "top10_overlap_count": 8, "top10_only_100": ["E33", "W03"], "top10_only_50": ["E11", "W11"], "e02_rank_100": 1, "e02_rank_50": 1, "e05_top10_100": true, "e05_top10_50": true, "e03_top10_100": true, "e03_top10_50": true}
- [x] 31/52 works have >=3/5 stable neighbours — 31/52
- [x] reuse author and period composition — 30 pairs: 29 same-author, 29 same-period, one cross-period
- [x] protected data/models and authorized catalogue citation revision — []

## 瀏覽器檢查

Passed: 9 / 9

- [x] HTML exists — C:\CHI3242文本發掘\第二次作業\output\exploration\index.html
- [x] HTML has no external script src — no <script src=...>
- [x] HTML has no external script/link resources — []
- [x] 2D/3D share the same coordinate source — both views read DATA.pca[String(n)].coords; no second fit
- [x] HTML placeholders replaced — placeholders absent
- [x] HTML contains Plotly and data — size=6,726,531 chars
- [x] HTML contains 超奇 projection — E01/超奇 present
- [x] HTML contribution controls and all-feature table — neighbor selector, category/sort filters, z_product and contribution
- [x] HTML all-feature summary not top-8 only — summary uses all features; filtered rows are not the sum

## 研究解釋檢查

Passed: 10 / 10

- [x] HTML corrected sign-flip caveat — no co_loading; no claim that sign flip proves instability
- [x] findings avoids '壓過' causal claim — author/genre labels describe visible structure; no causal 'override' claim
- [x] findings avoids '前30名' wording — reuse described as all 30 qualifying pairs, not a top-30 ranking
- [x] findings avoids stale top-8/1,000-column wording — table/findings describe all features, not a top-8 list
- [x] findings W09 retained-material caveat — 14 words are this excerpt, not the full original
- [x] findings 200-word threshold caveat — 200 words is a reminder threshold, not a validated boundary
- [x] findings exact-match caveat — 0 exact pairs under dedupe + minimum 8 CJK characters
- [x] findings W06/E11 only cross-period pair — all 30 approximate candidates; one cross-period
- [x] findings E05/E03 in both top-10 — E05/E03 in both 100- and 50-feature top-10
- [x] findings E02 contribution check — all-feature sum and both-present count reported

## Notes

- Only one 3-component PCA was fitted per feature setting; the 2D view is the PC1/PC2 subset of the same coordinates.
- The HTML uses the same DATA.pca coordinates for the 2D and 3D plots; toggling visibility does not refit.
- Exact cross-work duplicates are 0 because the build_corpus_v3 dedupe kept only the first occurrence; duplicates are logged in data/v3/excluded.csv.
- 相似度矩陣在原始 z-score 特徵上計算，不是 PCA 二維距離。
- Browser checks here are static/offline HTML checks; mouse rotation/zoom was not simulated. See browser_check.md.
- Research interpretation checks verify wording against computed data; they do not establish causal claims.

Protected file hashes are in `protected_hashes.json`; the exploration scripts only read these files.
