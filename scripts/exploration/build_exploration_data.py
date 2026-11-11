# -*- coding: utf-8 -*-
"""Build the chapter-level exploration data for the CHI3242 v3 corpus.

The 52 modelable works are the reference space. <論衡·超奇> is excluded
from fitting and projected with the fitted vocabulary/means/stds/PCA.
"""

from __future__ import annotations

import json
import re
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import jieba
import numpy as np
import pandas as pd
from qhchina.analytics.stylometry import Stylometry
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import train_model as tm  # noqa: E402  (adds the existing jieba user words)

OUT = ROOT / "output" / "exploration"
DATA_OUT = OUT / "data"
DATA_OUT.mkdir(parents=True, exist_ok=True)

TOKEN_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9]+")
CJK_RE = re.compile(r"[\u3400-\u9fff]")
FEATURE_SETTINGS = [100, 50]
SHORT_TOKEN_THRESHOLD = 200
EXACT_MIN_CJK = 8
NGRAM_N = 4
CONTAINMENT_THRESHOLD = 0.60
MIN_SHARED_NGRAMS = 4
APPROX_MIN_CJK = 8


def tokenize(text: str) -> list[str]:
    return [t for t in jieba.lcut(str(text)) if TOKEN_RE.fullmatch(t.strip())]


def cjk_only(text: str) -> str:
    return re.sub(r"[^\u3400-\u9fff]", "", str(text))


def norm_key(text: str) -> str:
    return re.sub(r"[^\u3400-\u9fffA-Za-z0-9]", "", str(text))


def load_corpus():
    catalogue = pd.read_csv(ROOT / "corpus_catalogue.csv", encoding="utf-8-sig")
    ref = catalogue[catalogue["用途"] == "主樣本"].copy()
    work_ids = ref["編號"].tolist()
    if len(work_ids) != 52:
        raise ValueError(f"Expected 52 reference works, got {len(work_ids)}")

    sa = pd.read_csv(ROOT / "data" / "v3" / "sentences_all.csv", encoding="utf-8-sig")
    sa = sa[sa["work_id"].isin(work_ids) & sa["trainable"] & sa["include_full"]].copy()
    counts = sa.groupby("period").size().to_dict()
    if len(sa) != 1654 or counts.get("西漢") != 702 or counts.get("東漢") != 952:
        raise ValueError(f"Unexpected corpus counts: total={len(sa)}, periods={counts}")

    # Verify each work count against the catalogue.
    per_work = sa.groupby("work_id").size().to_dict()
    mismatches = []
    for _, row in ref.iterrows():
        wid = row["編號"]
        expected = int(row["可建模全庫句"])
        actual = int(per_work.get(wid, 0))
        if expected != actual:
            mismatches.append((wid, expected, actual))
    if mismatches:
        raise ValueError(f"Per-work count mismatches: {mismatches}")

    return catalogue, ref, sa


def build_works(ref, sa):
    works = []
    for _, row in ref.iterrows():
        wid = row["編號"]
        sub = sa[sa["work_id"] == wid].sort_values("sent_order").copy()
        if sub.empty:
            raise ValueError(f"No modelable sentences for {wid}")
        tokens = []
        for text in sub["text_normalized"]:
            tokens.extend(tokenize(text))
        if not tokens:
            raise ValueError(f"No tokens for {wid}")
        original_text = "".join(sub["text_original"].astype(str).tolist())
        works.append({
            "work_id": wid,
            "work_title": row["篇名"],
            "author": row["作者"],
            "period": row["分期"],
            "genre": sub["genre"].iloc[0],
            "genre_group": sub["genre_group"].iloc[0],
            "excerpt_range": row["收錄範圍"],
            "sentence_count": int(len(sub)),
            "char_count": int(sub["char_len"].sum()),
            "token_count": int(len(tokens)),
            "short_flag": bool(len(tokens) < SHORT_TOKEN_THRESHOLD),
            "base_page": row["底本"],
            "base_url": row["底本網址"],
            "fixed_url": row["固定修訂網址"],
            "revision": str(row["修訂號"]),
            "original_text": original_text,
            "tokens": tokens,
        })
    return works, sa


def build_sentence_table(sa, works):
    meta = {w["work_id"]: w for w in works}
    rows = []
    for _, row in sa.sort_values(["work_id", "sent_order"]).iterrows():
        w = meta[row["work_id"]]
        text = str(row["text_original"])
        cjk = cjk_only(row["text_normalized"])
        rows.append({
            "sent_id": row["sent_id"],
            "work_id": row["work_id"],
            "work_title": w["work_title"],
            "author": w["author"],
            "period": w["period"],
            "genre": w["genre"],
            "genre_group": w["genre_group"],
            "sent_order": int(row["sent_order"]),
            "text_original": text,
            "text_normalized": str(row["text_normalized"]),
            "cjk_text": cjk,
            "cjk_len": len(cjk),
            "char_len": int(row["char_len"]),
            "base_url": w["base_url"],
            "fixed_url": w["fixed_url"],
            "revision": w["revision"],
        })
    return pd.DataFrame(rows)


def fit_feature_space(works, n_features):
    work_ids = [w["work_id"] for w in works]
    corpus = {w["work_id"]: [w["tokens"]] for w in works}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        stylo = Stylometry(
            n_features=n_features,
            ngram_range=(1, 1),
            transform="zscore",
            distance="cosine",
            classifier="delta",
            cull=None,
            min_variance=None,
            mode="instance",
        )
        stylo.fit_transform(corpus)
    warning_messages = [str(w.message) for w in caught]

    if stylo.document_ids != work_ids:
        raise ValueError("Stylometry document order does not match work order")
    features = list(stylo.features)
    vectors = np.vstack(stylo.document_vectors)
    means = np.asarray(stylo.feature_means, dtype=float)
    stds = np.asarray(stylo.feature_stds, dtype=float)

    raw = np.zeros((len(works), len(features)), dtype=int)
    for i, w in enumerate(works):
        counter = Counter(w["tokens"])
        for j, f in enumerate(features):
            raw[i, j] = counter.get(f, 0)
    relative = raw / np.array([w["token_count"] for w in works], dtype=float)[:, None]
    zscores = (relative - means) / stds
    if not np.allclose(zscores, vectors, atol=1e-10):
        raise ValueError("Recomputed z-scores do not match Stylometry document_vectors")

    pca = PCA(n_components=3, svd_solver="full")
    coords = pca.fit_transform(vectors)
    explained = pca.explained_variance_ratio_.tolist()
    cumulative = np.cumsum(explained).tolist()

    # Feature tables
    pd.DataFrame({"rank": range(1, len(features) + 1), "feature": features}).to_csv(
        DATA_OUT / f"features_{n_features}.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(raw, index=work_ids, columns=features).to_csv(
        DATA_OUT / f"feature_counts_{n_features}.csv", encoding="utf-8-sig")
    pd.DataFrame(relative, index=work_ids, columns=features).to_csv(
        DATA_OUT / f"feature_relative_{n_features}.csv", encoding="utf-8-sig")
    pd.DataFrame(zscores, index=work_ids, columns=features).to_csv(
        DATA_OUT / f"feature_zscores_{n_features}.csv", encoding="utf-8-sig")

    stats_rows = []
    for j, f in enumerate(features):
        col = raw[:, j]
        west = int(col[[i for i, w in enumerate(works) if w["period"] == "西漢"]].sum())
        east = int(col[[i for i, w in enumerate(works) if w["period"] == "東漢"]].sum())
        stats_rows.append({
            "feature": f, "total_count": int(col.sum()),
            "doc_count": int((col > 0).sum()),
            "author_count": int(len({works[i]["author"] for i in range(len(works)) if col[i] > 0})),
            "west_count": west, "east_count": east,
            "mean_across_works": float(means[j]), "std_across_works": float(stds[j]),
        })
    pd.DataFrame(stats_rows).to_csv(
        DATA_OUT / f"feature_stats_{n_features}.csv", index=False, encoding="utf-8-sig")

    coords_df = pd.DataFrame({"work_id": work_ids, "PC1": coords[:, 0],
                              "PC2": coords[:, 1], "PC3": coords[:, 2]})
    coords_df.to_csv(DATA_OUT / f"pca_coordinates_{n_features}.csv",
                     index=False, encoding="utf-8-sig")
    loadings_df = pd.DataFrame({"feature": features,
                                "PC1": pca.components_[0],
                                "PC2": pca.components_[1],
                                "PC3": pca.components_[2]})
    loadings_df.to_csv(DATA_OUT / f"pca_loadings_{n_features}.csv",
                       index=False, encoding="utf-8-sig")

    explained_payload = {
        "n_features": n_features,
        "n_components": 3,
        "explained_variance_ratio": explained,
        "cumulative_explained": cumulative,
        "pca_svd_solver": "full",
    }
    (DATA_OUT / f"explained_variance_{n_features}.json").write_text(
        json.dumps(explained_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    selection_payload = {
        "n_features_requested": n_features,
        "n_features_available": len(features),
        "feature_selection": "top N unigrams by corpus-wide total frequency (Counter.most_common); cull=None; min_variance=None",
        "ngram_range": [1, 1],
        "transform": "zscore",
        "distance": "cosine",
        "mode": "instance",
        "frequency_definition": "relative frequency = count / total unigrams (tokens) in the work",
        "zscore_definition": "z = (relative_frequency - mean_across_52_works) / std_across_52_works; population std (ddof=0); std < 1e-10 set to 1",
        "distance_definition": "cosine distance = 1 - cosine similarity; similarity = 1 - distance",
        "pca": "sklearn PCA(n_components=3, svd_solver='full') fitted on the 52 x n_features z-score matrix",
        "projection": "超奇 is transformed with the fitted features, feature_means and feature_stds, then pca.transform; it is not in the fit",
        "warnings": warning_messages,
        "document_ids": work_ids,
        "n_fit_documents": len(work_ids),
    }
    (DATA_OUT / f"feature_selection_{n_features}.json").write_text(
        json.dumps(selection_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "stylo": stylo, "features": features, "vectors": vectors,
        "means": means, "stds": stds, "raw": raw, "relative": relative,
        "zscores": zscores, "pca": pca, "coords": coords,
        "explained": explained, "cumulative": cumulative,
        "work_ids": work_ids, "warnings": warning_messages,
    }


def project_chaoyi(space, n_features):
    sa_all = pd.read_csv(ROOT / "data" / "v3" / "sentences_all.csv", encoding="utf-8-sig")
    e01 = sa_all[(sa_all["work_id"] == "E01") & (sa_all["include_full"])].sort_values("sent_order")
    if len(e01) != 129:
        raise ValueError(f"Expected 129 超奇 sentences, got {len(e01)}")
    tokens = []
    for text in e01["text_normalized"]:
        tokens.extend(tokenize(text))
    vec = space["stylo"].transform(tokens, warn_oov=False)
    coords = space["pca"].transform(vec.reshape(1, -1))[0]
    feature_set = set(space["features"])
    known = sum(1 for t in tokens if t in feature_set)
    overlap = known / len(tokens) if tokens else 0.0
    cat = pd.read_csv(ROOT / "corpus_catalogue.csv", encoding="utf-8-sig")
    meta = cat[cat["編號"] == "E01"].iloc[0]
    payload = {
        "work_id": "E01",
        "work_title": "論衡·超奇",
        "author": "王充",
        "period": "東漢",
        "sentence_count": int(len(e01)),
        "token_count": int(len(tokens)),
        "n_features": n_features,
        "feature_overlap_count": int(known),
        "feature_overlap_ratio": float(overlap),
        "PC1": float(coords[0]), "PC2": float(coords[1]), "PC3": float(coords[2]),
        "excluded_from_fit": True,
        "fit_work_count": len(space["work_ids"]),
        "base_page": meta["底本"],
        "base_url": meta["底本網址"],
        "fixed_url": meta["固定修訂網址"],
        "revision": str(meta["修訂號"]),
        "excerpt_range": meta["收錄範圍"],
    }
    (DATA_OUT / f"chaoyi_projection_{n_features}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    pd.DataFrame({"feature": space["features"], "z_chaoyi": vec}).to_csv(
        DATA_OUT / f"chaoyi_zscores_{n_features}.csv", index=False, encoding="utf-8-sig")
    sims = cosine_similarity(vec.reshape(1, -1), space["vectors"])[0]
    order = np.argsort(sims)[::-1][:10]
    # Need works metadata for target labels
    return payload, sims, order, vec, Counter(tokens), len(tokens)


def word_evidence(works, sentences, space, n_features):
    features = space["features"]
    raw = space["raw"]
    loadings = space["pca"].components_
    west_idx = [i for i, w in enumerate(works) if w["period"] == "西漢"]
    east_idx = [i for i, w in enumerate(works) if w["period"] == "東漢"]
    west_tokens = sum(works[i]["token_count"] for i in west_idx)
    east_tokens = sum(works[i]["token_count"] for i in east_idx)
    sentence_tokens = [set(tokenize(t)) for t in sentences["text_normalized"]]

    evidence_rows = []
    example_rows = []
    for pc in range(3):
        values = loadings[pc]
        pos = np.argsort(values)[::-1][:15]
        neg = np.argsort(values)[:15]
        for direction, indices in [("positive", pos), ("negative", neg)]:
            for rank, j in enumerate(indices, 1):
                f = features[j]
                col = raw[:, j]
                total = int(col.sum())
                doc_count = int((col > 0).sum())
                author_count = len({works[i]["author"] for i in range(len(works)) if col[i] > 0})
                west = int(col[west_idx].sum())
                east = int(col[east_idx].sum())
                work_shares = [(int(col[i]), works[i]["work_id"], works[i]["work_title"]) for i in range(len(works))]
                top_work_count, top_work_id, top_work_title = max(work_shares, key=lambda x: x[0])
                author_counts = Counter()
                for i in range(len(works)):
                    if col[i] > 0:
                        author_counts[works[i]["author"]] += int(col[i])
                top_author, top_author_count = author_counts.most_common(1)[0]
                concentration = []
                if total < 5:
                    concentration.append("稀少")
                if doc_count <= 3:
                    concentration.append("集中於少數篇章")
                if total and top_author_count / total >= 0.5:
                    concentration.append("集中於單一作者")
                if total and top_work_count / total >= 0.5:
                    concentration.append("集中於單篇")
                examples = []
                seen_works = set()
                for si, tokens in enumerate(sentence_tokens):
                    if f in tokens and sentences.iloc[si]["work_id"] not in seen_works:
                        row = sentences.iloc[si]
                        examples.append({
                            "sent_id": row["sent_id"], "work_id": row["work_id"],
                            "work_title": row["work_title"], "author": row["author"],
                            "period": row["period"], "text_original": row["text_original"],
                            "base_url": row["base_url"], "fixed_url": row["fixed_url"],
                        })
                        seen_works.add(row["work_id"])
                        if len(examples) >= 3:
                            break
                evidence_rows.append({
                    "feature_set": n_features, "pc": pc + 1, "direction": direction,
                    "rank": rank, "feature": f, "loading": float(values[j]),
                    "total_count": total, "doc_count": doc_count, "author_count": author_count,
                    "west_count": west, "west_total_tokens": west_tokens,
                    "west_freq": west / west_tokens if west_tokens else 0.0,
                    "east_count": east, "east_total_tokens": east_tokens,
                    "east_freq": east / east_tokens if east_tokens else 0.0,
                    "max_work_share": top_work_count / total if total else 0.0,
                    "top_work_id": top_work_id, "top_work_title": top_work_title,
                    "max_author_share": top_author_count / total if total else 0.0,
                    "top_author": top_author,
                    "concentration": "；".join(concentration) if concentration else "分散",
                })
                for ex in examples:
                    example_rows.append({"feature_set": n_features, "pc": pc + 1,
                                         "direction": direction, "feature": f, **ex})

    pd.DataFrame(evidence_rows).to_csv(
        DATA_OUT / f"pc_word_evidence_{n_features}.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(example_rows).to_csv(
        DATA_OUT / f"pc_word_examples_{n_features}.csv", index=False, encoding="utf-8-sig")
    return evidence_rows, example_rows


def similarity_and_neighbors(works, space, n_features):
    work_ids = space["work_ids"]
    sim = cosine_similarity(space["vectors"])
    np.fill_diagonal(sim, 1.0)
    if not np.allclose(sim, sim.T, atol=1e-12):
        raise ValueError("Similarity matrix is not symmetric")
    if not np.allclose(np.diag(sim), 1.0, atol=1e-12):
        raise ValueError("Similarity diagonal is not 1")
    pd.DataFrame(sim, index=work_ids, columns=work_ids).to_csv(
        DATA_OUT / f"similarity_{n_features}.csv", encoding="utf-8-sig")

    meta = {w["work_id"]: w for w in works}
    rows = []
    for i, wid in enumerate(work_ids):
        order = np.argsort(sim[i])[::-1]
        rank = 0
        for j in order:
            if j == i:
                continue
            rank += 1
            target = work_ids[j]
            rows.append({
                "source_work_id": wid, "rank": rank, "target_work_id": target,
                "similarity": float(sim[i, j]),
                "target_title": meta[target]["work_title"],
                "target_author": meta[target]["author"],
                "target_period": meta[target]["period"],
            })
            if rank >= 5:
                break
    pd.DataFrame(rows).to_csv(
        DATA_OUT / f"neighbors_{n_features}.csv", index=False, encoding="utf-8-sig")
    return sim, rows


def reuse_candidates(sentences):
    # Exact normalized matches (deduplicated corpus)
    exact_groups = defaultdict(list)
    for i, row in sentences.iterrows():
        if row["cjk_len"] >= EXACT_MIN_CJK:
            exact_groups[norm_key(row["text_normalized"])].append(i)
    exact_rows = []
    for key, indices in exact_groups.items():
        if len(indices) < 2:
            continue
        for a in range(len(indices)):
            for b in range(a + 1, len(indices)):
                ia, ib = indices[a], indices[b]
                ra, rb = sentences.iloc[ia], sentences.iloc[ib]
                if ra["work_id"] == rb["work_id"]:
                    continue
                exact_rows.append({
                    "method": "exact_normalized", "similarity": 1.0,
                    "containment": 1.0, "jaccard": 1.0,
                    "sent_id_a": ra["sent_id"], "work_id_a": ra["work_id"],
                    "title_a": ra["work_title"], "author_a": ra["author"], "period_a": ra["period"],
                    "text_a": ra["text_original"], "url_a": ra["fixed_url"],
                    "sent_id_b": rb["sent_id"], "work_id_b": rb["work_id"],
                    "title_b": rb["work_title"], "author_b": rb["author"], "period_b": rb["period"],
                    "text_b": rb["text_original"], "url_b": rb["fixed_url"],
                    "shared_ngrams": len(key), "lcs_len": len(key), "lcs_text": key,
                })
    exact_cols = [
        "method", "similarity", "containment", "jaccard",
        "sent_id_a", "work_id_a", "title_a", "author_a", "period_a", "text_a", "url_a",
        "sent_id_b", "work_id_b", "title_b", "author_b", "period_b", "text_b", "url_b",
        "shared_ngrams", "lcs_len", "lcs_text",
    ]
    exact_df = (pd.DataFrame(exact_rows, columns=exact_cols).sort_values(
        ["shared_ngrams"], ascending=False) if exact_rows else pd.DataFrame(columns=exact_cols))
    exact_df.to_csv(DATA_OUT / "reuse_exact.csv", index=False, encoding="utf-8-sig")

    # Approximate character 4-gram containment
    grams = []
    index = defaultdict(list)
    for i, row in sentences.iterrows():
        if row["cjk_len"] < APPROX_MIN_CJK:
            grams.append(set())
            continue
        g = {row["cjk_text"][k:k + NGRAM_N] for k in range(len(row["cjk_text"]) - NGRAM_N + 1)}
        grams.append(g)
        for ng in g:
            index[ng].append(i)

    pair_shared = defaultdict(int)
    for ng, ids in index.items():
        if len(ids) < 2:
            continue
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                ia, ib = ids[a], ids[b]
                if sentences.iloc[ia]["work_id"] == sentences.iloc[ib]["work_id"]:
                    continue
                pair_shared[(ia, ib)] += 1

    approx_rows = []
    for (ia, ib), shared in pair_shared.items():
        if shared < MIN_SHARED_NGRAMS:
            continue
        ga, gb = grams[ia], grams[ib]
        containment = shared / min(len(ga), len(gb)) if min(len(ga), len(gb)) else 0.0
        jaccard = shared / len(ga | gb) if ga | gb else 0.0
        if containment < CONTAINMENT_THRESHOLD:
            continue
        ra, rb = sentences.iloc[ia], sentences.iloc[ib]
        from difflib import SequenceMatcher
        match = SequenceMatcher(None, ra["cjk_text"], rb["cjk_text"]).find_longest_match(
            0, len(ra["cjk_text"]), 0, len(rb["cjk_text"]))
        approx_rows.append({
            "method": "char4_containment", "similarity": containment,
            "containment": containment, "jaccard": jaccard,
            "sent_id_a": ra["sent_id"], "work_id_a": ra["work_id"],
            "title_a": ra["work_title"], "author_a": ra["author"], "period_a": ra["period"],
            "text_a": ra["text_original"], "url_a": ra["fixed_url"],
            "sent_id_b": rb["sent_id"], "work_id_b": rb["work_id"],
            "title_b": rb["work_title"], "author_b": rb["author"], "period_b": rb["period"],
            "text_b": rb["text_original"], "url_b": rb["fixed_url"],
            "shared_ngrams": int(shared), "lcs_len": int(match.size),
            "lcs_text": ra["cjk_text"][match.a:match.a + match.size],
        })
    approx_df = pd.DataFrame(approx_rows)
    if not approx_df.empty:
        approx_df = approx_df.sort_values(
            ["containment", "jaccard", "shared_ngrams"], ascending=False).reset_index(drop=True)
    approx_df.to_csv(DATA_OUT / "reuse_approx.csv", index=False, encoding="utf-8-sig")

    # Special check W06-015 / E11-018
    special = {}
    a = sentences[sentences["sent_id"] == "W06-015"]
    b = sentences[sentences["sent_id"] == "E11-018"]
    if len(a) and len(b):
        ra, rb = a.iloc[0], b.iloc[0]
        ga = {ra["cjk_text"][k:k + NGRAM_N] for k in range(len(ra["cjk_text"]) - NGRAM_N + 1)}
        gb = {rb["cjk_text"][k:k + NGRAM_N] for k in range(len(rb["cjk_text"]) - NGRAM_N + 1)}
        shared = ga & gb
        containment = len(shared) / min(len(ga), len(gb)) if min(len(ga), len(gb)) else 0.0
        jaccard = len(shared) / len(ga | gb) if ga | gb else 0.0
        from difflib import SequenceMatcher
        match = SequenceMatcher(None, ra["cjk_text"], rb["cjk_text"]).find_longest_match(
            0, len(ra["cjk_text"]), 0, len(rb["cjk_text"]))
        in_approx = False
        if not approx_df.empty:
            in_approx = bool(((approx_df["sent_id_a"].isin(["W06-015", "E11-018"])) &
                              (approx_df["sent_id_b"].isin(["W06-015", "E11-018"]))).any())
        special = {
            "pair": ["W06-015", "E11-018"],
            "exact_normalized_equal": norm_key(ra["text_normalized"]) == norm_key(rb["text_normalized"]),
            "n": NGRAM_N,
            "min_shared": MIN_SHARED_NGRAMS,
            "threshold": CONTAINMENT_THRESHOLD,
            "min_short_cjk": APPROX_MIN_CJK,
            "shared_ngrams": len(shared),
            "containment": containment,
            "jaccard": jaccard,
            "lcs_len": int(match.size),
            "lcs_text": ra["cjk_text"][match.a:match.a + match.size],
            "detected_by_approx": in_approx,
            "reason": "" if in_approx else "未達門檻或不在前段候選；見數值",
            "text_a": ra["text_original"], "text_b": rb["text_original"],
            "url_a": ra["fixed_url"], "url_b": rb["fixed_url"],
        }
    (DATA_OUT / "reuse_special_check.json").write_text(
        json.dumps(special, ensure_ascii=False, indent=2), encoding="utf-8")
    return exact_df, approx_df, special


def formal_predictions():
    rows = []
    for path, source in [
        (ROOT / "output" / "v3" / "independent_predictions.csv", "v3 independent_predictions"),
        (ROOT / "output" / "v3" / "test_predictions.csv", "v3 test_predictions"),
    ]:
        if path.exists():
            df = pd.read_csv(path, encoding="utf-8-sig")
            for _, row in df.iterrows():
                rows.append({
                    "sent_id": row["sent_id"], "source": source,
                    "period_true": row.get("period_true", "東漢"),
                    "period_pred": row["period_pred"],
                    "prob_east": float(row["prob_east"]),
                    "prob_west": float(row["prob_west"]),
                    "correct": bool(str(row.get("period_true", "東漢")) == str(row["period_pred"])),
                    "text_original": row["text_original"],
                })
    pred = pd.DataFrame(rows)
    pred.to_csv(DATA_OUT / "predictions_formal.csv", index=False, encoding="utf-8-sig")
    return pred


def main():
    catalogue, ref, sa = load_corpus()
    works, sa_ref = build_works(ref, sa)
    sentences = build_sentence_table(sa_ref, works)
    sentences.to_csv(DATA_OUT / "sentences.csv", index=False, encoding="utf-8-sig")
    works_df = pd.DataFrame([{k: v for k, v in w.items() if k != "tokens"}
                             for w in works])
    works_df.to_csv(DATA_OUT / "works.csv", index=False, encoding="utf-8-sig")

    west_tokens = sum(w["token_count"] for w in works if w["period"] == "西漢")
    east_tokens = sum(w["token_count"] for w in works if w["period"] == "東漢")
    overview = {
        "n_works": len(works),
        "n_sentences": len(sentences),
        "period_sentence_counts": {k: int(v) for k, v in sentences["period"].value_counts().items()},
        "period_work_counts": {k: int(v) for k, v in works_df["period"].value_counts().items()},
        "period_token_counts": {"西漢": int(west_tokens), "東漢": int(east_tokens)},
        "short_works": [
            {"work_id": w["work_id"], "work_title": w["work_title"],
             "sentences": w["sentence_count"], "tokens": w["token_count"], "chars": w["char_count"]}
            for w in works if w["short_flag"]
        ],
        "short_threshold_tokens": SHORT_TOKEN_THRESHOLD,
        "feature_settings": FEATURE_SETTINGS,
        "tokenization": "jieba.lcut on text_normalized, keep CJK/alnum tokens only; train_model.USER_WORDS added",
        "user_words": tm.USER_WORDS,
        "unit": "one work or defined excerpt; not one sentence",
        "caveat": "full-corpus exploration (1654 sentences), not the 1163-sentence main-sample test result; PCA positions are not prediction probabilities",
        "counts_match_catalogue": True,
    }
    (DATA_OUT / "corpus_overview.json").write_text(
        json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8")

    spaces = {}
    sims = {}
    neighbors = {}
    evidence = {}
    examples = {}
    projections = {}
    chaoyi_sims = {}
    for n in FEATURE_SETTINGS:
        print("Fitting", n, "features")
        space = fit_feature_space(works, n)
        spaces[n] = space
        ev, ex = word_evidence(works, sentences, space, n)
        evidence[n] = ev
        examples[n] = ex
        sim, nb = similarity_and_neighbors(works, space, n)
        sims[n] = sim
        neighbors[n] = nb
        proj, csims, corder, chaoyi_vec, chaoyi_counts, chaoyi_token_count = project_chaoyi(space, n)
        projections[n] = proj
        # save chaoyi neighbors
        meta = {w["work_id"]: w for w in works}
        crows = []
        for rank, j in enumerate(corder, 1):
            wid = space["work_ids"][j]
            crows.append({
                "source_work_id": "E01", "rank": rank, "target_work_id": wid,
                "similarity": float(csims[j]),
                "target_title": meta[wid]["work_title"],
                "target_author": meta[wid]["author"],
                "target_period": meta[wid]["period"],
            })
        pd.DataFrame(crows).to_csv(
            DATA_OUT / f"chaoyi_neighbors_{n}.csv", index=False, encoding="utf-8-sig")

        # All-feature comparison for the top 10 超奇 neighbours
        stats = pd.read_csv(DATA_OUT / f"feature_stats_{n}.csv", encoding="utf-8-sig").set_index("feature")
        work_token_counts = {w["work_id"]: w["token_count"] for w in works}
        shared_rows = []
        contribution_checks = []
        norm_a = float(np.linalg.norm(chaoyi_vec))
        for rank, j in enumerate(corder, 1):
            wid = space["work_ids"][j]
            nz = space["zscores"][j]
            norm_b = float(np.linalg.norm(nz))
            contributions = chaoyi_vec * nz / (norm_a * norm_b)
            both_present_count = 0
            both_above_count = 0
            both_below_count = 0
            other_count = 0
            for k, f in enumerate(space["features"]):
                za = float(chaoyi_vec[k])
                zb = float(nz[k])
                ca = int(chaoyi_counts.get(f, 0))
                cb = int(space["raw"][j, k])
                if za > 0 and zb > 0:
                    category = "both_above_mean"
                    both_above_count += 1
                elif za < 0 and zb < 0:
                    category = "both_below_mean"
                    both_below_count += 1
                else:
                    category = "other"
                    other_count += 1
                both_present = bool(ca > 0 and cb > 0)
                if both_present:
                    both_present_count += 1
                st = stats.loc[f]
                shared_rows.append({
                    "feature_set": n, "neighbor_work_id": wid, "neighbor_rank": rank,
                    "feature": f,
                    "count_chaoyi": ca,
                    "count_neighbor": cb,
                    "rel_freq_chaoyi": ca / chaoyi_token_count if chaoyi_token_count else 0.0,
                    "rel_freq_neighbor": cb / work_token_counts[wid] if work_token_counts[wid] else 0.0,
                    "z_chaoyi": za, "z_neighbor": zb,
                    "category": category,
                    "both_present": both_present,
                    "z_product": za * zb,
                    "cosine_contribution": float(contributions[k]),
                    "total_count": int(st["total_count"]), "doc_count": int(st["doc_count"]),
                    "author_count": int(st["author_count"]),
                    "west_count": int(st["west_count"]), "east_count": int(st["east_count"]),
                })
            contribution_checks.append({
                "neighbor_work_id": wid, "neighbor_rank": rank,
                "similarity": float(csims[j]),
                "contribution_sum": float(contributions.sum()),
                "difference": float(abs(contributions.sum() - csims[j])),
                "n_features": int(len(space["features"])),
                "both_present_count": int(both_present_count),
                "both_above_count": int(both_above_count),
                "both_below_count": int(both_below_count),
                "other_count": int(other_count),
                "norm_chaoyi": norm_a,
                "norm_neighbor": norm_b,
            })
        if shared_rows:
            pd.DataFrame(shared_rows).to_csv(
                DATA_OUT / f"chaoyi_shared_features_{n}.csv", index=False, encoding="utf-8-sig")
            (DATA_OUT / f"chaoyi_contribution_checks_{n}.json").write_text(
                json.dumps(contribution_checks, ensure_ascii=False, indent=2),
                encoding="utf-8")

    # 超奇 top-5/top-10 neighbour overlap, computed from the saved high-dimensional neighbours
    cn100 = pd.read_csv(DATA_OUT / "chaoyi_neighbors_100.csv", encoding="utf-8-sig")
    cn50 = pd.read_csv(DATA_OUT / "chaoyi_neighbors_50.csv", encoding="utf-8-sig")
    top5_100 = set(cn100[cn100["rank"] <= 5]["target_work_id"])
    top5_50 = set(cn50[cn50["rank"] <= 5]["target_work_id"])
    top10_100 = set(cn100[cn100["rank"] <= 10]["target_work_id"])
    top10_50 = set(cn50[cn50["rank"] <= 10]["target_work_id"])
    e02_100 = cn100[cn100["target_work_id"] == "E02"]["rank"].tolist()
    e02_50 = cn50[cn50["target_work_id"] == "E02"]["rank"].tolist()
    overlap = {
        "top5_100": sorted(top5_100),
        "top5_50": sorted(top5_50),
        "top5_overlap": sorted(top5_100 & top5_50),
        "top5_overlap_count": len(top5_100 & top5_50),
        "top5_only_100": sorted(top5_100 - top5_50),
        "top5_only_50": sorted(top5_50 - top5_100),
        "top10_100": sorted(top10_100),
        "top10_50": sorted(top10_50),
        "top10_overlap": sorted(top10_100 & top10_50),
        "top10_overlap_count": len(top10_100 & top10_50),
        "top10_only_100": sorted(top10_100 - top10_50),
        "top10_only_50": sorted(top10_50 - top10_100),
        "e02_rank_100": int(e02_100[0]) if e02_100 else None,
        "e02_rank_50": int(e02_50[0]) if e02_50 else None,
        "e05_top10_100": "E05" in top10_100,
        "e05_top10_50": "E05" in top10_50,
        "e03_top10_100": "E03" in top10_100,
        "e03_top10_50": "E03" in top10_50,
    }
    (DATA_OUT / "chaoyi_neighbor_overlap.json").write_text(
        json.dumps(overlap, ensure_ascii=False, indent=2), encoding="utf-8")
    print("超奇 neighbour overlap:", json.dumps(overlap, ensure_ascii=False))

    # Neighbor stability between 100 and 50
    stability = []
    for wid in spaces[100]["work_ids"]:
        n100 = {r["target_work_id"] for r in neighbors[100] if r["source_work_id"] == wid}
        n50 = {r["target_work_id"] for r in neighbors[50] if r["source_work_id"] == wid}
        stability.append({
            "work_id": wid,
            "stable_count": len(n100 & n50),
            "stable_neighbors": "、".join(sorted(n100 & n50)),
            "only_100": "、".join(sorted(n100 - n50)),
            "only_50": "、".join(sorted(n50 - n100)),
        })
    pd.DataFrame(stability).to_csv(
        DATA_OUT / "neighbor_stability.csv", index=False, encoding="utf-8-sig")

    exact_df, approx_df, special = reuse_candidates(sentences)
    pred = formal_predictions()

    print("Exact reuse rows:", len(exact_df))
    print("Approx reuse rows:", len(approx_df))
    print("Special check:", json.dumps(special, ensure_ascii=False, indent=2))
    print("PCA variance 100:", spaces[100]["explained"], "cum", spaces[100]["cumulative"])
    print("PCA variance 50:", spaces[50]["explained"], "cum", spaces[50]["cumulative"])
    print("Chaoyi projection 100:", projections[100])
    print("Wrote exploration data to", DATA_OUT)


if __name__ == "__main__":
    main()
