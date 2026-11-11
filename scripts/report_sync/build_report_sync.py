# -*- coding: utf-8 -*-
"""Sync report.docx and report.html from the current report.md.

Reads report.md and the linked corpus appendix; writes only the root Word and
HTML files.  It never writes report.md or report.pdf and does not touch the
corpus, model, or exploration outputs.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[2]
REF = Path(r"C:\CHI3242文本發掘\第一次作業\Report.docx")
REPORT_MD = ROOT / "report.md"
APPENDIX_MD = ROOT / "output" / "report_support" / "corpus_appendix.md"
DOCX_OUT = ROOT / "report.docx"
HTML_OUT = ROOT / "report.html"
MANIFEST = ROOT / "output" / "report_sync" / "build_manifest.json"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def tag(name: str) -> str:
    return "{" + W + "}" + name


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inline_plain(text: str) -> str:
    """Markdown inline -> Word-visible text (link target retained)."""
    def repl(match):
        label, url = match.group(1), match.group(2)
        return f"{label}（{url}）"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)
    return text.replace("**", "")


def inline_html(text: str) -> str:
    """Markdown inline -> escaped HTML with links and bare URLs clickable."""
    placeholders = {}

    def keep_link(match):
        label, url = match.group(1), match.group(2)
        key = f"\x00LINK{len(placeholders)}\x00"
        placeholders[key] = (
            f'<a href="{html.escape(url, quote=True)}"'
            + (' target="_blank" rel="noopener"' if url.startswith("http") else "")
            + f">{html.escape(label)}</a>"
        )
        return key

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", keep_link, text)
    text = html.escape(text)
    url_re = re.compile(r"(https?://[^\s，。；、）)]+)")
    pieces = []
    last = 0
    for m in url_re.finditer(text):
        pieces.append(text[last:m.start()])
        pieces.append(
            f'<a href="{html.escape(m.group(1), quote=True)}" target="_blank" rel="noopener">{m.group(1)}</a>'
        )
        last = m.end()
    pieces.append(text[last:])
    text = "".join(pieces)
    for key, link in placeholders.items():
        text = text.replace(html.escape(key), link)
    text = re.sub(r"\[\^(\d+)\]", lambda m: '<sup><a href="#note-' + m.group(1) + '">' + m.group(1) + '</a></sup>', text)
    return text


def cell_html(text: str) -> str:
    text = html.escape(text)
    m = re.search(r"（(\d{5,})）", text)
    if m:
        oldid = m.group(1)
        text = text.replace(
            m.group(0),
            f'（<a href="https://zh.wikisource.org/w/index.php?oldid={oldid}"'
            f' target="_blank" rel="noopener">{oldid}</a>）',
        )
    return text


def parse_markdown(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("|"):
            table = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = lines[i].strip()
                i += 1
                if re.match(r"^\|[-:|]+\|$", row):
                    continue
                table.append([c.strip() for c in row.strip("|").split("|")])
            if table:
                blocks.append({"kind": "table", "rows": table})
            continue
        if s.startswith("#"):
            level = len(s) - len(s.lstrip("#"))
            blocks.append({"kind": "heading", "level": level, "text": s[level:].strip()})
            i += 1
            continue
        m = re.fullmatch(r"\*\*(.*)\*\*", s)
        if m:
            blocks.append({"kind": "caption", "text": m.group(1).strip()})
            i += 1
            continue
        blocks.append({"kind": "paragraph", "text": s})
        i += 1
    return blocks


def paragraph_from_template(template, text: str, *, break_before=False, keep_next=False):
    p = deepcopy(template)
    pr = p.find("w:pPr", NS)
    if pr is None:
        pr = E.Element(tag("pPr"))
        p.insert(0, pr)
    for c in list(p):
        if c is not pr:
            p.remove(c)
    if break_before and pr.find("w:pageBreakBefore", NS) is None:
        E.SubElement(pr, tag("pageBreakBefore"))
    if keep_next and pr.find("w:keepNext", NS) is None:
        E.SubElement(pr, tag("keepNext"))
    r = E.SubElement(p, tag("r"))
    E.SubElement(r, tag("t")).text = text
    return p


def build_docx(blocks):
    with ZipFile(REF) as z:
        parts = {name: z.read(name) for name in z.namelist()}

    doc = E.fromstring(parts["word/document.xml"])
    body = doc.find("w:body", NS)
    ps = body.findall("w:p", NS)
    section = deepcopy(body.find("w:sectPr", NS))
    templates = {
        "title": deepcopy(ps[0]),
        "subtitle": deepcopy(ps[1]),
        "head": deepcopy(ps[2]),
        "text": deepcopy(ps[3]),
        "caption": deepcopy(ps[7]),
        "ref": deepcopy(ps[32]),
    }
    tables = body.findall("w:tbl", NS)
    table_template = deepcopy(tables[1] if len(tables) > 1 else tables[0])

    for c in list(body):
        body.remove(c)

    def add_paragraph(text, kind="text", break_before=False, keep_next=False):
        p = paragraph_from_template(
            templates[kind], text, break_before=break_before, keep_next=keep_next
        )
        if kind in ("head", "caption", "title"):
            ppr = p.find("w:pPr", NS)
            if ppr.find("w:keepNext", NS) is None:
                E.SubElement(ppr, tag("keepNext"))
        if kind == "title":
            for run in p.findall("w:r", NS):
                rp = run.find("w:rPr", NS)
                if rp is None:
                    rp = E.SubElement(run, tag("rPr"))
                E.SubElement(rp, tag("sz")).set(tag("val"), "28")
        if kind == "head":
            pp = p.find("w:pPr", NS)
            spacing = pp.find("w:spacing", NS)
            if spacing is None:
                spacing = E.SubElement(pp, tag("spacing"))
            spacing.set(tag("before"), "160")
            spacing.set(tag("after"), "80")
        body.append(p)
        return p

    def add_table(rows, widths):
        t = deepcopy(table_template)
        for c in list(t):
            if c.tag == tag("tr"):
                t.remove(c)
        grid = t.find("w:tblGrid", NS)
        for c in list(grid):
            grid.remove(c)
        for width in widths:
            E.SubElement(grid, tag("gridCol")).set(tag("w"), str(width))
        pr = t.find("w:tblPr", NS)
        for e in pr.findall("w:tblW", NS):
            e.set(tag("w"), str(sum(widths)))
            e.set(tag("type"), "dxa")
        for j, row in enumerate(rows):
            tr = E.SubElement(t, tag("tr"))
            trpr = E.SubElement(tr, tag("trPr"))
            E.SubElement(trpr, tag("cantSplit"))
            if j == 0:
                E.SubElement(trpr, tag("tblHeader"))
            for k, value in enumerate(row):
                tc = E.SubElement(tr, tag("tc"))
                cp = E.SubElement(tc, tag("tcPr"))
                tw = E.SubElement(cp, tag("tcW"))
                tw.set(tag("w"), str(widths[k]))
                tw.set(tag("type"), "dxa")
                E.SubElement(cp, tag("vAlign")).set(tag("val"), "center")
                if j == 0:
                    E.SubElement(cp, tag("shd")).set(tag("fill"), "F2F2F2")
                borders = E.SubElement(cp, tag("tcBorders"))
                for side in ("top", "left", "bottom", "right"):
                    el = E.SubElement(borders, tag(side))
                    el.set(tag("val"), "single")
                    el.set(tag("sz"), "4")
                    el.set(tag("color"), "D9D9D9")
                margins = E.SubElement(cp, tag("tcMar"))
                for side in ("top", "bottom", "left", "right"):
                    el = E.SubElement(margins, tag(side))
                    el.set(tag("w"), "65")
                    el.set(tag("type"), "dxa")
                p = E.SubElement(tc, tag("p"))
                ppr = E.SubElement(p, tag("pPr"))
                E.SubElement(ppr, tag("spacing")).set(tag("after"), "0")
                if j == 0:
                    E.SubElement(ppr, tag("keepNext"))
                E.SubElement(ppr, tag("jc")).set(
                    tag("val"), "center" if k not in (1, 2) else "left"
                )
                r = E.SubElement(p, tag("r"))
                rp = E.SubElement(r, tag("rPr"))
                E.SubElement(rp, tag("sz")).set(tag("val"), "20")
                if j == 0:
                    E.SubElement(rp, tag("b"))
                E.SubElement(r, tag("t")).text = value
        body.append(t)

    pending_caption = False
    appendix_mode = False
    in_refs = False
    for block in blocks:
        if block["kind"] == "heading":
            text = block["text"]
            if block["level"] == 1:
                add_paragraph(text, "title", keep_next=True)
            elif block["level"] == 2 and text.startswith("——"):
                add_paragraph(text, "subtitle", keep_next=True)
            elif block["level"] == 2 and text.startswith("附錄"):
                appendix_mode = True
                in_refs = False
                add_paragraph(text, "head", keep_next=True)
            else:
                if text.startswith("參考書目"):
                    in_refs = True
                elif text.startswith("AI使用") or text in ("研究流程與AI使用說明", "配套材料"):
                    in_refs = False
                p = add_paragraph(text, "head", keep_next=True, break_before=False)
            pending_caption = False
        elif block["kind"] == "caption":
            add_paragraph(block["text"], "caption", keep_next=True)
            pending_caption = True
        elif block["kind"] == "paragraph":
            raw = block["text"]
            if re.match(r"^\[\^\d+\]:", raw):
                continue
            p = add_paragraph("", "ref" if in_refs else "text")
            for run in list(p.findall("w:r", NS)):
                p.remove(run)
            pos = 0
            for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", raw):
                if match.start() > pos:
                    rr = E.SubElement(p, tag("r"))
                    E.SubElement(rr, tag("t")).text = raw[pos:match.start()]
                label, url = match.groups()
                field = E.SubElement(p, tag("fldSimple"))
                field.set(tag("instr"), ' HYPERLINK "' + url + '" ')
                rr = E.SubElement(field, tag("r"))
                E.SubElement(rr, tag("t")).text = label + ("（" + url + "）" if not url.startswith("http") else "")
                pos = match.end()
            if pos < len(raw):
                rr = E.SubElement(p, tag("r"))
                E.SubElement(rr, tag("t")).text = raw[pos:]
            if in_refs:
                pp = p.find("w:pPr", NS)
                spacing = pp.find("w:spacing", NS)
                if spacing is None:
                    spacing = E.SubElement(pp, tag("spacing"))
                spacing.set(tag("before"), "0")
                spacing.set(tag("after"), "80")
                spacing.set(tag("line"), "240")
                spacing.set(tag("lineRule"), "auto")
            pending_caption = False
        elif block["kind"] == "table":
            rows = block["rows"]
            ncols = max(len(r) for r in rows)
            if appendix_mode:
                widths = [550, 2050, 3000, 850, 1000, 850]
            elif ncols == 5:
                widths = [1660] * 5
            else:
                widths = [1350, 1400, 1400, 1300, 1400, 1450]
            add_table(rows, widths)
            pending_caption = False

    body.append(section)

    foot = E.fromstring(parts["word/footnotes.xml"])
    for f in list(foot):
        fid = f.get(tag("id"))
        if fid is not None and int(fid) > 0:
            foot.remove(f)

    # Actual page-bottom footnotes, sourced from the Markdown definitions.
    notes = {}
    for block in blocks:
        if block["kind"] == "paragraph":
            match = re.match(r"^\[\^(\d+)\]:\s*(.*)$", block["text"])
            if match:
                notes[match.group(1)] = match.group(2)
    for t in list(doc.findall(".//w:t", NS)):
        if not t.text or not re.search(r"\[\^\d+\]", t.text):
            continue
        run = t.getparent(); parent = run.getparent(); idx = parent.index(run)
        for fragment in re.split(r"(\[\^\d+\])", t.text):
            if not fragment:
                continue
            newrun = E.Element(tag("r"))
            match = re.fullmatch(r"\[\^(\d+)\]", fragment)
            if match:
                rp = E.SubElement(newrun, tag("rPr"))
                E.SubElement(rp, tag("vertAlign")).set(tag("val"), "superscript")
                E.SubElement(newrun, tag("footnoteReference")).set(tag("id"), match.group(1))
            else:
                E.SubElement(newrun, tag("t")).text = fragment
            parent.insert(idx, newrun); idx += 1
        parent.remove(run)
    for fid, note in notes.items():
        f = E.SubElement(foot, tag("footnote")); f.set(tag("id"), fid)
        pp = E.SubElement(f, tag("p")); pr = E.SubElement(pp, tag("pPr"))
        E.SubElement(pr, tag("pStyle")).set(tag("val"), "FootnoteText")
        rr = E.SubElement(pp, tag("r")); E.SubElement(rr, tag("footnoteRef"))
        rr = E.SubElement(pp, tag("r")); rp = E.SubElement(rr, tag("rPr"))
        E.SubElement(rp, tag("sz")).set(tag("val"), "18")
        E.SubElement(rr, tag("t")).text = " " + note
    core = E.fromstring(parts["docProps/core.xml"])
    for x in core:
        if E.QName(x).localname in ("creator", "lastModifiedBy", "description", "subject"):
            x.text = ""
    title_value = next((b["text"] for b in blocks if b["kind"] == "heading" and b["level"] == 1), "")
    for x in core:
        if E.QName(x).localname == "title":
            x.text = title_value

    parts["word/document.xml"] = E.tostring(
        doc, encoding="UTF-8", xml_declaration=True, standalone=True
    )
    parts["word/footnotes.xml"] = E.tostring(
        foot, encoding="UTF-8", xml_declaration=True, standalone=True
    )
    parts["docProps/core.xml"] = E.tostring(
        core, encoding="UTF-8", xml_declaration=True, standalone=True
    )

    with ZipFile(DOCX_OUT, "w", ZIP_DEFLATED) as z:
        for name, value in parts.items():
            z.writestr(name, value)


def build_html(blocks):
    parts = []
    in_refs = False
    appendix_mode = False
    for block in blocks:
        if block["kind"] == "heading":
            level = block["level"]
            text = block["text"]
            if level == 1:
                parts.append(f'<h1 id="top">{html.escape(text)}</h1>')
            elif level == 2 and text.startswith("——"):
                parts.append(f'<p class="subtitle">{html.escape(text)}</p>')
            elif text.startswith("附錄"):
                in_refs = False
                appendix_mode = True
                parts.append(f'<h2 class="appendix">{html.escape(text)}</h2>')
            elif level == 2:
                if text.startswith("參考書目"):
                    in_refs = True
                elif text.startswith("AI使用") or text in ("研究流程與AI使用說明", "配套材料"):
                    in_refs = False
                parts.append(f"<h2>{html.escape(text)}</h2>")
            else:
                parts.append(f'<h3 class="group">{html.escape(text)}</h3>')
        elif block["kind"] == "caption":
            parts.append(f'<p class="caption">{html.escape(block["text"])}</p>')
        elif block["kind"] == "paragraph":
            cls = ' class="reference"' if in_refs else ""
            parts.append(f"<p{cls}>{inline_html(block['text'])}</p>")
        elif block["kind"] == "table":
            rows = block["rows"]
            table_class = "appendix-table" if appendix_mode else "result-table"
            out = [f'<div class="tablewrap"><table class="{table_class}">']
            if rows:
                out.append("<thead><tr>")
                for cell in rows[0]:
                    out.append(f"<th>{cell_html(cell)}</th>")
                out.append("</tr></thead><tbody>")
                for row in rows[1:]:
                    out.append("<tr>")
                    for cell in row:
                        out.append(f"<td>{cell_html(cell)}</td>")
                    out.append("</tr>")
                out.append("</tbody>")
            out.append("</table></div>")
            parts.append("".join(out))

    css = """
:root{color-scheme:light}
body{max-width:900px;margin:44px auto;padding:0 26px;color:#111;font:18px/1.9 "Noto Serif TC","PMingLiU","Microsoft JhengHei",serif;background:#fff}
h1{text-align:center;font-size:30px;font-weight:600;line-height:1.35;margin:10px 0 0}
.subtitle{text-align:center;font-size:18px;margin:6px 0 34px;color:#444}
h2{font-size:22px;font-weight:600;line-height:1.4;margin:38px 0 12px;border-left:5px solid #8c6b3f;padding-left:12px}
h3{font-size:19px;font-weight:600;margin:30px 0 10px}
p{margin:0 0 14px;text-align:justify}
.caption{text-align:center;text-indent:0;margin:20px 0 8px;font-weight:600;break-after:avoid}
.reference{text-align:left;text-indent:-2em;padding-left:2em;margin-bottom:10px}
.tablewrap{overflow-x:auto;margin:0 0 24px}
table{border-collapse:collapse;width:100%;font-size:15px;line-height:1.55;table-layout:fixed}
thead{display:table-header-group}
th,td{border:1px solid #d6d0c4;padding:7px 9px;vertical-align:middle;overflow-wrap:anywhere}
th{background:#f2eee6;font-weight:600}
td:first-child,th:first-child{white-space:nowrap}
.result-table th:nth-child(1),.result-table td:nth-child(1){width:18%}
.result-table th:nth-child(2),.result-table td:nth-child(2){width:22%}
.result-table th:nth-child(3),.result-table td:nth-child(3){width:18%}
.result-table th:nth-child(4),.result-table td:nth-child(4){width:14%}
.result-table th:nth-child(5),.result-table td:nth-child(5){width:14%}
.result-table th:nth-child(6),.result-table td:nth-child(6){width:14%}
.appendix-table th:nth-child(1),.appendix-table td:nth-child(1){width:7%}
.appendix-table th:nth-child(2),.appendix-table td:nth-child(2){width:17%}
.appendix-table th:nth-child(3),.appendix-table td:nth-child(3){width:38%}
.appendix-table th:nth-child(4),.appendix-table td:nth-child(4){width:10%}
.appendix-table th:nth-child(5),.appendix-table td:nth-child(5){width:12%}
.appendix-table th:nth-child(6),.appendix-table td:nth-child(6){width:16%}
.appendix-table td:nth-child(n+4),.appendix-table th:nth-child(n+4){white-space:nowrap}
a{color:#7a4f1d;text-decoration:none;border-bottom:1px solid #d8c3a6}
a:hover{text-decoration:underline}
.toolbar{display:flex;justify-content:center;margin:0 0 26px}
.toolbar a{display:inline-block;border:1px solid #cbb58f;border-radius:999px;padding:6px 15px;font-size:15px;background:#faf7f0}
.appendix{break-before:page}
@media print{
  @page{size:A4;margin:20mm}
  body{max-width:none;margin:0;padding:0;font-size:11.5pt;line-height:1.65}
  h1{font-size:20pt;margin-top:0}.subtitle{font-size:12pt;margin-bottom:18pt}
  h2{font-size:15pt;margin-top:20pt;break-after:avoid}h3{font-size:13pt;break-after:avoid}
  .toolbar{display:none}a{color:#000;border-bottom:0}
  .tablewrap{overflow:visible}table{font-size:9.5pt}tr{break-inside:avoid}
}
"""
    body = "".join(parts)
    body = re.sub(r'<p([^>]*)><sup><a href="#note-(\d+)">\d+</a></sup>:', r'<p id="note-\2" style="font-size:0.85em"\1>\2.', body)
    toolbar = (
        '<div class="toolbar"><a href="output/exploration/index.html">'
        "互動探索：PCA、三維圖與篇章近鄰</a></div>"
    )
    title = next((b["text"] for b in blocks if b["kind"] == "heading" and b["level"] == 1), "")
    return (
        '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{css}</style></head><body>"
        f'{toolbar}<main>{body}</main></body></html>'
    )


def main():
    # Current report.md keeps the full catalogue in the linked support file.
    # Do not append it to the manuscript: the argument body only carries the
    # "配套材料" link, per the author's latest instruction.
    blocks = parse_markdown(REPORT_MD)
    build_docx(blocks)
    HTML_OUT.write_text(build_html(blocks), encoding="utf-8")
    manifest = {
        "report_md": str(REPORT_MD),
        "appendix_reference": str(APPENDIX_MD),
        "appendix_reference_sha256": sha(APPENDIX_MD),
        "report_md_sha256": sha(REPORT_MD),
        "report_docx_sha256": sha(DOCX_OUT),
        "report_html_sha256": sha(HTML_OUT),
        "blocks": len(blocks),
        "tables": sum(1 for b in blocks if b["kind"] == "table"),
        "headings": sum(1 for b in blocks if b["kind"] == "heading"),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
