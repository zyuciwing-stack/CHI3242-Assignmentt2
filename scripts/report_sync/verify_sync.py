# -*- coding: utf-8 -*-
"""Verify the Word/HTML sync against report.md and the saved evidence."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

import fitz
from lxml import etree as E
from lxml import html as LH

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "report_sync"))
import build_report_sync as B  # noqa: E402
import validate_evidence as V  # noqa: E402

REPORT_MD = ROOT / "report.md"
APPENDIX_MD = ROOT / "output" / "report_support" / "corpus_appendix.md"
DOCX = ROOT / "report.docx"
HTML = ROOT / "report.html"
PREVIEW_PDF = ROOT / "output" / "report_sync" / "report_sync_preview.pdf"
HTML_PRINT = ROOT / "output" / "report_sync" / "report_html_print.pdf"
HTML_SCREEN = ROOT / "output" / "report_sync" / "report_html_screen.png"
HTML_DOM = ROOT / "output" / "report_sync" / "report_html_dom.html"
REF = Path(r"C:\CHI3242文本發掘\第一次作業\Report.docx")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text: str) -> str:
    return re.sub(r"[\s\u3000]+", "", text)


def docx_text_and_tables(path: Path):
    with ZipFile(path) as z:
        root = E.fromstring(z.read("word/document.xml"))
    body = root.find("w:body", NS)
    texts = []
    tables = []
    for child in body:
        if child.tag == f"{{{W}}}p":
            texts.append("".join(t.text or "" for t in child.findall(".//w:t", NS)))
        elif child.tag == f"{{{W}}}tbl":
            rows = []
            for tr in child.findall("w:tr", NS):
                rows.append(
                    [
                        "".join(t.text or "" for t in tc.findall(".//w:t", NS))
                        for tc in tr.findall("w:tc", NS)
                    ]
                )
            tables.append(rows)
            for row in rows:
                texts.extend(row)
    return "".join(texts), tables


def source_text(blocks, html_mode=False):
    out = []
    for b in blocks:
        if b["kind"] in ("heading", "caption"):
            out.append(b["text"])
        elif b["kind"] == "paragraph":
            text = b["text"]
            if html_mode:
                text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
                text = text.replace("**", "")
            else:
                text = B.inline_plain(text)
            out.append(text)
        elif b["kind"] == "table":
            for row in b["rows"]:
                out.extend(row)
    return "".join(out)


def main():
    checks = []
    known = []
    unverified = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        return ok

    blocks = B.parse_markdown(REPORT_MD)
    word_text, word_tables = docx_text_and_tables(DOCX)
    html_doc = LH.parse(str(HTML))
    main_nodes = html_doc.xpath("//main")
    html_text = "".join(main_nodes[0].text_content()) if main_nodes else ""

    check("report.md unchanged after sync", sha(REPORT_MD) == json.loads((ROOT / "output" / "report_sync" / "build_manifest.json").read_text(encoding="utf-8"))["report_md_sha256"], sha(REPORT_MD))
    manifest = json.loads((ROOT / "output" / "report_sync" / "build_manifest.json").read_text(encoding="utf-8"))
    check("external appendix unchanged", sha(APPENDIX_MD) == manifest["appendix_reference_sha256"], sha(APPENDIX_MD))
    check("report.md keeps appendix external", "### 甲" not in REPORT_MD.read_text(encoding="utf-8") and "corpus_appendix.md" in REPORT_MD.read_text(encoding="utf-8"), "full catalogue only in output/report_support")

    src_word = norm(source_text(blocks, html_mode=False))
    src_html = norm(source_text(blocks, html_mode=True))
    act_word = norm(word_text)
    act_html = norm(html_text)
    check("Word text == report.md", act_word == src_word, f"word={len(act_word)} source={len(src_word)}")
    check("HTML text == report.md", act_html == src_html, f"html={len(act_html)} source={len(src_html)}")
    if act_word != src_word:
        i = next((i for i, (a, b) in enumerate(zip(act_word, src_word)) if a != b), min(len(act_word), len(src_word)))
        known.append({"where": "Word text", "detail": repr({"word": act_word[max(0, i - 60):i + 100], "source": src_word[max(0, i - 60):i + 100]})})
    if act_html != src_html:
        i = next((i for i, (a, b) in enumerate(zip(act_html, src_html)) if a != b), min(len(act_html), len(src_html)))
        known.append({"where": "HTML text", "detail": repr({"html": act_html[max(0, i - 60):i + 100], "source": src_html[max(0, i - 60):i + 100]})})

    check("Word has 2 result tables only", len(word_tables) == 2, str([len(t) for t in word_tables]))
    check("Word result table 1", word_tables[0] == [["分期", "可建模全庫", "主樣本", "訓練", "測試"], ["西漢", "702", "632", "505", "127"], ["東漢", "952", "531", "425", "106"]], str(word_tables[0]))
    check("Word result table 2", word_tables[1] == [["文獻分期", "判西漢（句）", "判東漢（句）", "精確率", "召回率", "F1"], ["西漢", "100", "27", "0.633", "0.787", "0.702"], ["東漢", "58", "48", "0.640", "0.453", "0.530"]], str(word_tables[1]))
    check("Word does not embed full catalogue", "W22" not in word_text and "P05" not in word_text and "### 甲" not in word_text, "only the 配套材料 link is present")

    html_rows = []
    for table in html_doc.xpath("//table"):
        rows = []
        for tr in table.xpath("./tr|./thead/tr|./tbody/tr"):
            cells = [c.text_content().strip() for c in tr.xpath("./th|./td")]
            rows.append(cells)
        html_rows.append(rows)
    check("HTML has 2 result tables only", len(html_rows) == 2, str([len(t) for t in html_rows]))
    check("HTML result table 1", html_rows[0] == [["分期", "可建模全庫", "主樣本", "訓練", "測試"], ["西漢", "702", "632", "505", "127"], ["東漢", "952", "531", "425", "106"]], str(html_rows[0]))
    check("HTML result table 2", html_rows[1] == [["文獻分期", "判西漢（句）", "判東漢（句）", "精確率", "召回率", "F1"], ["西漢", "100", "27", "0.633", "0.787", "0.702"], ["東漢", "58", "48", "0.640", "0.453", "0.530"]], str(html_rows[1]))
    check("HTML does not embed full catalogue", "W22" not in html_text and "P05" not in html_text and "### 甲" not in html_text, "only the 配套材料 link is present")

    # Structure and Word package preservation.
    with ZipFile(REF) as z:
        ref_styles = z.read("word/styles.xml")
        ref_sect = E.fromstring(z.read("word/document.xml")).find(".//w:sectPr", NS)
    with ZipFile(DOCX) as z:
        new_styles = z.read("word/styles.xml")
        new_sect = E.fromstring(z.read("word/document.xml")).find(".//w:sectPr", NS)
        foot = E.fromstring(z.read("word/footnotes.xml"))
        footer = z.read("word/footer1.xml")
    check("Word styles.xml preserved", ref_styles == new_styles, "byte-identical to Report.docx")
    check("Word section geometry preserved", E.tostring(ref_sect) == E.tostring(new_sect), "sectPr identical")
    check("Word footnote count 0", len([f for f in foot if int(f.get(f"{{{W}}}id", "0")) > 0]) == 0, "old footnotes not carried over")
    check("Word footer PAGE field present", b"PAGE" in footer, "page-number field inherited")

    # PDF preview checks.
    pdf = fitz.open(PREVIEW_PDF)
    page_texts = [p.get_text() for p in pdf]
    pdf_text = "".join(page_texts)
    check("Word preview PDF 3 pages", pdf.page_count == 3, str(pdf.page_count))
    check("Word preview no blank page", all(len(t.strip()) >= 50 for t in page_texts), str([len(t.strip()) for t in page_texts]))
    check("Word preview page numbers", all(t.strip().splitlines()[0].strip() == str(i) for i, t in enumerate(page_texts, 1)), str([t.strip().splitlines()[0] for t in page_texts]))
    check("Word preview current subtitle", "從詞彙比較到文獻考辨" in page_texts[0], page_texts[0][:80].replace("\n", " / "))
    check("Word preview sections", all(h in pdf_text for h in ["一、由兩漢賦論", "二、文獻範圍", "三、詞彙差異", "四、回到引語", "五、詞彙辨期", "參考書目", "研究流程", "配套材料"]), "five sections and end matter present")
    check("Word preview no full catalogue", "W01" not in pdf_text and "W22" not in pdf_text and "P05" not in pdf_text, "catalogue is linked externally, not embedded")
    check("Word preview no replacement glyph", "\ufffd" not in pdf_text, "no U+FFFD")

    # HTML links and offline/print properties.
    check("HTML no external script", not html_doc.xpath("//script[@src]"), "no script src")
    check("HTML no external stylesheet", not html_doc.xpath("//link[@rel='stylesheet']"), "inline CSS only")
    hrefs = [a.get("href") for a in html_doc.xpath("//a[@href]")]
    relative = [h for h in hrefs if h and not h.startswith(("http://", "https://", "#"))]
    missing = [h for h in relative if not (ROOT / h).exists()]
    check("HTML local links resolve", not missing, str(missing))
    check("HTML exploration link", "output/exploration/index.html" in relative and (ROOT / "output/exploration/index.html").exists(), "offline exploration entry")
    check("HTML external appendix link", "output/report_support/corpus_appendix.md" in relative and (ROOT / "output/report_support/corpus_appendix.md").exists(), "full catalogue remains external")
    external_links = [h for h in hrefs if h and h.startswith("http")]
    check("HTML external source links", len(external_links) >= 5, f"{len(external_links)} external links")
    check("HTML print CSS", "@media print" in HTML.read_text(encoding="utf-8") and "@page" in HTML.read_text(encoding="utf-8"), "print rules present")
    check("HTML lang/charset", html_doc.getroot().get("lang") == "zh-Hant" and html_doc.xpath("//meta[@charset='utf-8']"), "zh-Hant/utf-8")
    check("HTML browser screenshot exists", HTML_SCREEN.exists() and HTML_SCREEN.stat().st_size > 20000, str(HTML_SCREEN))
    check("HTML DOM dump exists", HTML_DOM.exists() and "詞語與兩漢文論的時期歸屬" in HTML_DOM.read_text(encoding="utf-8"), str(HTML_DOM))
    html_print = fitz.open(HTML_PRINT)
    html_print_texts = [p.get_text() for p in html_print]
    check("HTML print PDF 3 pages", html_print.page_count == 3, str(html_print.page_count))
    check("HTML print no blank page", all(len(t.strip()) >= 50 for t in html_print_texts), str([len(t.strip()) for t in html_print_texts]))
    check("HTML print tables and end matter", "表一" in html_print_texts[0] and "表二" in "".join(html_print_texts) and "配套材料" in "".join(html_print_texts), "tables and 配套材料 printed")

    # Data anchors recomputed from original CSV/JSON.
    evidence = V.main()
    expected = {
        "corpus": (52, 15, 1654, 702, 952),
        "main": (1163, 632, 531, 930, 233, 505, 425, 127, 106),
        "model": (148, 233, 127, 0.6351931330472103, 0.616070563148202, [[100, 27], [58, 48]]),
        "grouped": (238, 136),
        "genre": (82, 51, 59),
        "uncertain": (56, 3),
        "exploration": (20.068828410268602, 3, 8, 0.5584869926694442, 0.5584869926694443, 55),
    }
    anchors_ok = (
        (evidence["corpus"]["works"], evidence["corpus"]["authors"], evidence["corpus"]["sentences"], evidence["corpus"]["period"]["西漢"], evidence["corpus"]["period"]["東漢"]) == expected["corpus"]
        and (evidence["main"]["sentences"], evidence["main"]["period"]["西漢"], evidence["main"]["period"]["東漢"], evidence["main"]["split"]["train"], evidence["main"]["split"]["test"], evidence["main"]["split_period"]["西漢"]["train"], evidence["main"]["split_period"]["東漢"]["train"], evidence["main"]["split_period"]["西漢"]["test"], evidence["main"]["split_period"]["東漢"]["test"]) == expected["main"]
        and abs(evidence["model"]["accuracy"] - 0.6351931330472103) < 1e-12
        and abs(evidence["model"]["majority_baseline"] - 0.5450643776824035) < 1e-12
        and abs(evidence["model"]["macro_f1"] - 0.616070563148202) < 1e-12
        and evidence["model"]["confusion"] == [[100, 27], [58, 48]]
        and (evidence["grouped"]["n_test"], evidence["grouped"]["correct"]) == expected["grouped"]
        and (evidence["genre"]["n_test"], evidence["genre"]["full_correct"], evidence["genre"]["zip_correct"]) == expected["genre"]
        and (evidence["uncertain"]["total_clean"], evidence["uncertain"]["zero_features"]) == expected["uncertain"]
        and abs(evidence["exploration"]["pca_cum3_100"] * 100 - 20.068828410268602) < 1e-9
        and (evidence["exploration"]["overlap5"], evidence["exploration"]["overlap10"]) == (3, 8)
        and abs(evidence["exploration"]["e02_similarity"] - 0.5584869926694442) < 1e-15
        and abs(evidence["exploration"]["e02_contribution_sum"] - 0.5584869926694443) < 1e-15
        and evidence["exploration"]["e02_both_present"] == 55
        and evidence["author_pair"]["P1"]["full_east_hits"] == 50
        and evidence["author_pair"]["P1"]["zip_east_hits"] == 60
    )
    check("evidence anchors from CSV/JSON", anchors_ok, json.dumps(evidence, ensure_ascii=False)[:1200])
    check("appendix 70 and sums", evidence["appendix"]["rows"] == 70 and evidence["appendix"]["unique_ids"] == 70 and evidence["appendix"]["groups"] == {"甲　西漢可建模語料": 21, "乙　東漢可建模語料": 31, "丙　整篇留出與歸屬待核": 4, "丁　未擷取及不收的來源記錄": 14} and evidence["appendix"]["sums"] == {"candidate": 1888, "full": 1654, "main": 1163, "train": 930, "test": 233}, json.dumps(evidence["appendix"], ensure_ascii=False)[:900])
    check("appendix count columns match catalogue", not evidence["appendix"]["count_diff"], str(evidence["appendix"]["count_diff"]))
    known.append({
        "where": "appendix usage vs corpus_catalogue.csv",
        "detail": evidence["appendix"]["usage_diff"],
        "note": "附錄依報告寫『疑難探測，不作訓練』；來源表寫『歸屬待核』。兩者均表示不參與訓練，未改數據。",
    })

    # PDF is known to be stale relative to the current Markdown.
    pdf_root = fitz.open(ROOT / "report.pdf")
    pdf_first = pdf_root[0].get_text()
    pdf_matches_md = "從詞彙比較到文獻考辨" in pdf_first and "揚雄謂" in pdf_first
    if not pdf_matches_md:
        known.append({
            "where": "report.pdf",
            "detail": {
                "report_md_mtime": REPORT_MD.stat().st_mtime,
                "report_pdf_mtime": (ROOT / "report.pdf").stat().st_mtime,
                "pdf_first": pdf_first[:120].replace("\n", " / "),
                "md_first": REPORT_MD.read_text(encoding="utf-8").splitlines()[:8],
            },
            "note": "report.pdf 仍是舊版（副標題與首段均與目前 report.md 不同）；本次未修改 PDF，Word/HTML 以目前 report.md 為準。",
        })
    else:
        check("report.pdf matches current Markdown", True, "title/subtitle present")

    # Hash comparison against the pre-sync snapshot.
    pre = json.loads((ROOT / "output" / "report_sync" / "pre_sync_hashes.json").read_text(encoding="utf-8"))
    changed = []
    for rel, old in pre.items():
        p = ROOT / rel
        if not p.exists():
            changed.append((rel, "missing"))
        elif sha(p) != old:
            changed.append((rel, "changed"))
    unexpected = [x for x in changed if x[0] not in ("report.docx", "report.html")]
    check("protected inputs unchanged", not unexpected, str(unexpected))
    check("report.docx intentionally changed", ("report.docx", "changed") in changed, str(changed))
    check("report.html intentionally changed", ("report.html", "changed") in changed, str(changed))
    unverified.append("未在一般桌面瀏覽器以滑鼠逐一點擊外部來源連結；已用 headless Chrome 載入、截圖與列印。")

    result = {
        "checks": checks,
        "passed": sum(1 for c in checks if c["ok"]),
        "failed": sum(1 for c in checks if not c["ok"]),
        "known_discrepancies": known,
        "unverified": unverified,
        "evidence": evidence,
        "hashes": {
            "report_md": sha(REPORT_MD),
            "report_pdf": sha(ROOT / "report.pdf"),
            "report_docx": sha(DOCX),
            "report_html": sha(HTML),
            "preview_pdf": sha(PREVIEW_PDF),
        },
        "text_lengths": {"word": len(act_word), "html": len(act_html), "source": len(src_word)},
        "word_tables": [len(t) for t in word_tables],
        "html_tables": [len(t) for t in html_rows],
        "pdf_pages": pdf.page_count,
        "html_print_pages": html_print.page_count,
        "visual_review": {
            "word_preview_pages": pdf.page_count,
            "word_all_pages_inspected": True,
            "word_no_clipping_or_blank_page": all(len(t.strip()) >= 50 for t in page_texts),
            "html_screen_inspected": True,
            "html_print_pages": html_print.page_count,
            "html_print_no_blank_page": all(len(t.strip()) >= 50 for t in html_print_texts),
        },
        "browser_check": {
            "tool": "Google Chrome headless (--headless=new)",
            "screen_shot": str(HTML_SCREEN),
            "dom_dump": str(HTML_DOM),
            "print_pdf": str(HTML_PRINT),
            "local_links_resolved": not missing,
        },
        "changed_files": changed,
    }
    out = ROOT / "output" / "report_sync" / "verification.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("passed", "failed", "known_discrepancies", "unverified", "hashes", "pdf_pages")}, ensure_ascii=False, indent=2))
    print(out)


if __name__ == "__main__":
    main()
