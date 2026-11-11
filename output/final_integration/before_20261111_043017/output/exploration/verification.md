# Exploration verification

Passed: 45 / 45

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
- [x] HTML exists — C:\CHI3242文本發掘\第二次作業\output\exploration\index.html
- [x] HTML has no external script src — no <script src=...>
- [x] HTML has no external script/link resources — []
- [x] 2D/3D share the same coordinate source — both views read DATA.pca[String(n)].coords; no second fit
- [x] HTML placeholders replaced — placeholders absent
- [x] HTML contains Plotly and data — size=6,201,587 chars
- [x] HTML contains 超奇 projection — E01/超奇 present

Protected file hashes are in `protected_hashes.json`; the exploration scripts only read these files.
