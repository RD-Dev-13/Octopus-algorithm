"""Build the IEEE-style two-column DOCX (and PDF through Word) of the OIOA paper.

    python paper/build_paper.py            -> paper/OIOA_paper_updated.docx
    python paper/build_paper.py --pdf      -> also paper/OIOA_paper_updated.pdf (needs Microsoft Word on Windows)

Layout follows the reference paper: US Letter, 0.75 in margins, one-column title block, two text columns,
Times New Roman 10 pt justified body, roman-numbered section headings, lettered italic subsection
headings, 8 pt tables and captions, numbered equations, numbered references.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from refs import REFS                                               # noqa: E402
import content_static as S                                          # noqa: E402
import content_results as R                                         # noqa: E402

FONT = "Times New Roman"
EQ_FONT = "Cambria Math"
COL_W = 3.375            # column width in inches (7.0 in text width, 0.25 in gap)

TITLE = ("Octopus Imitation Optimization Algorithm (OIOA): A Behavior-Aware Bio-Inspired Metaheuristic with "
         "Observational Learning, Mimicry and Camouflage Operators")
AUTHORS = [
    ("Pavankalyan K", ["Dept. of Computing Technologies", "S.R.M. Institute of Science and Technology", "Chennai, India",
                       "pk138@srmist.edu.in"]),
    ("Santosh Kumar", ["Dept. of Computing Technologies", "S.R.M. Institute of Science and Technology", "Chennai, India",
                       "sk5160@srmist.edu.in"]),
    ("R. Rajmohan", ["Assistant Professor", "Dept. of Computing Technologies", "S.R.M. Institute of Science and Technology",
                     "Chennai, India"]),
]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


# ----------------------------------------------------------------------------- low-level helpers
def set_cols(section, n, space_in=0.25):
    sectPr = section._sectPr
    for c in sectPr.findall(qn("w:cols")):
        sectPr.remove(c)
    cols = OxmlElement("w:cols")
    cols.set(qn("w:num"), str(n))
    cols.set(qn("w:space"), str(int(space_in * 1440)))
    sectPr.append(cols)


def font(run, size=10, bold=None, italic=None, name=FONT, color=None, small_caps=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run._element.rPr.rFonts.set(qn("w:cs"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if small_caps is not None:
        run.font.small_caps = small_caps
    if color:
        run.font.color.rgb = RGBColor(*color)


def pformat(p, align=None, before=0, after=0, line=None, first=None, left=None, keep_next=False, keep_lines=False):
    pf = p.paragraph_format
    if align is not None:
        p.alignment = align
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if line:
        pf.line_spacing = line
    if first is not None:
        pf.first_line_indent = Inches(first)
    if left is not None:
        pf.left_indent = Inches(left)
    pf.keep_with_next = keep_next
    pf.keep_together = keep_lines
    pf.widow_control = True


def add_page_number(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        r = p.add_run()
        font(r, 9)
        if kind:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), kind)
            r._element.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            r._element.append(it)


def cell_borders(cell, **kw):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        spec = kw.get(edge)
        el = OxmlElement(f"w:{edge}")
        if spec:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(spec))
            el.set(qn("w:color"), "000000")
        else:
            el.set(qn("w:val"), "nil")
        b.append(el)
    tcPr.append(b)


def cell_margins(table, top=20, bottom=20, left=60, right=60):
    tblPr = table._tbl.tblPr
    m = OxmlElement("w:tblCellMar")
    for edge, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(v))
        el.set(qn("w:type"), "dxa")
        m.append(el)
    tblPr.append(m)


def set_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


MATH_TOKEN = re.compile(r"(\)|\]|(?<![A-Za-z0-9_])(?:[A-Za-zΑ-Ωα-ω]|\d+))((?:[_^](?:\{[^}]*\}|[A-Za-z0-9]+))+)")
SCRIPT = re.compile(r"([_^])(\{[^}]*\}|[A-Za-z0-9]+)")


def add_math(p, text, size=10, name=FONT, italic_base=True):
    """Write text; X_sub / X^sup / X_{long sub} become italic X with real subscripts and superscripts."""
    pos = 0
    for m in MATH_TOKEN.finditer(text):
        if m.start() > pos:
            font(p.add_run(text[pos:m.start()]), size, name=name)
        font(p.add_run(m.group(1)), size, italic=(italic_base and m.group(1).isalpha()), name=name)
        for kind, body in SCRIPT.findall(m.group(2)):
            r = p.add_run(body.strip("{}"))
            font(r, size, name=name)
            r.font.subscript = kind == "_"
            r.font.superscript = kind == "^"
        pos = m.end()
    if pos < len(text):
        font(p.add_run(text[pos:]), size, name=name)


def add_runs_with_cites(p, text, size=10, cite_map=None):
    """Write text with {c:key,key} placeholders replaced by [n] / [n], [m]."""
    pos = 0
    for m in re.finditer(r"\{c:([a-z0-9,]+)\}", text):
        if m.start() > pos:
            add_math(p, text[pos:m.start()], size)
        nums = [cite_map[k] for k in m.group(1).split(",")]
        font(p.add_run(", ".join(f"[{n}]" for n in nums)), size)
        pos = m.end()
    if pos < len(text):
        add_math(p, text[pos:], size)


# ----------------------------------------------------------------------------- document assembly
class Builder:
    def __init__(self, cite_map):
        self.doc = Document()
        self.cite = cite_map
        self.sec_no = 0
        self.sub_no = 0
        self.eq_no = 0
        self.fig_no = 0
        self.tab_no = 0
        self.in_two_col = False
        self._setup()

    def _setup(self):
        d = self.doc
        st = d.styles["Normal"]
        st.font.name = FONT
        st.font.size = Pt(10)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        sec = d.sections[0]
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        sec.left_margin = sec.right_margin = Inches(0.75)
        sec.top_margin, sec.bottom_margin = Inches(0.75), Inches(0.9)
        set_cols(sec, 1)
        add_page_number(sec)
        for name, size, bold, italic in (("Heading 1", 10, False, False), ("Heading 2", 10, False, True),
                                         ("Title", 24, False, False)):
            s = d.styles[name]
            s.font.name = FONT
            s.font.size = Pt(size)
            s.font.bold = bold
            s.font.italic = italic
            s.font.color.rgb = RGBColor(0, 0, 0)
            s.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
            s.element.rPr.rFonts.set(qn("w:ascii"), FONT)
            s.element.rPr.rFonts.set(qn("w:hAnsi"), FONT)

    # --- front matter
    def front(self, abstract, keywords):
        d = self.doc
        p = d.add_paragraph(style="Title")
        pformat(p, WD_ALIGN_PARAGRAPH.CENTER, before=0, after=10, line=1.0)
        r = p.add_run(TITLE)
        font(r, 20, bold=False)
        t = d.add_table(rows=1, cols=3)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for cell, (name, lines) in zip(t.rows[0].cells, AUTHORS):
            cell.paragraphs[0].text = ""
            p = cell.paragraphs[0]
            pformat(p, WD_ALIGN_PARAGRAPH.CENTER, after=2)
            font(p.add_run(name), 11, bold=False)
            for ln in lines:
                q = cell.add_paragraph()
                pformat(q, WD_ALIGN_PARAGRAPH.CENTER)
                font(q.add_run(ln), 9, italic=(ln == lines[0] and "Dept" in ln) or None)
        sp = d.add_paragraph()
        pformat(sp, after=6)
        # switch to two columns
        sec = d.add_section(WD_SECTION.CONTINUOUS)
        set_cols(sec, 2)
        self.in_two_col = True
        p = d.add_paragraph()
        pformat(p, WD_ALIGN_PARAGRAPH.JUSTIFY, after=4, line=1.0)
        font(p.add_run("Abstract"), 9, bold=True, italic=True)
        font(p.add_run("—" + abstract), 9, bold=True)
        p = d.add_paragraph()
        pformat(p, WD_ALIGN_PARAGRAPH.JUSTIFY, after=8, line=1.0)
        font(p.add_run("Keywords"), 9, bold=True, italic=True)
        font(p.add_run("—" + keywords), 9, bold=True)

    # --- block dispatch
    def add(self, block):
        kind = block[0]
        getattr(self, "b_" + kind)(*block[1:])

    def b_h1(self, text):
        self.sec_no += 1
        self.sub_no = 0
        p = self.doc.add_paragraph(style="Heading 1")
        pformat(p, WD_ALIGN_PARAGRAPH.CENTER, before=8, after=4, keep_next=True)
        font(p.add_run(f"{ROMAN[self.sec_no - 1]}. "), 10, small_caps=True)
        font(p.add_run(text), 10, small_caps=True)

    def b_h2(self, text):
        self.sub_no += 1
        p = self.doc.add_paragraph(style="Heading 2")
        pformat(p, WD_ALIGN_PARAGRAPH.LEFT, before=4, after=2, keep_next=True)
        font(p.add_run(f"{chr(64 + self.sub_no)}. {text}"), 10, italic=True)

    def b_p(self, text):
        p = self.doc.add_paragraph()
        pformat(p, WD_ALIGN_PARAGRAPH.JUSTIFY, after=4, line=1.0, first=0.17)
        add_runs_with_cites(p, text, 10, self.cite)

    def b_eq(self, text):
        self.eq_no += 1
        p = self.doc.add_paragraph()
        pformat(p, WD_ALIGN_PARAGRAPH.LEFT, before=2, after=4, line=1.0, keep_lines=True)
        ts = p.paragraph_format.tab_stops
        ts.add_tab_stop(Inches(COL_W / 2), WD_TAB_ALIGNMENT.CENTER)
        ts.add_tab_stop(Inches(COL_W), WD_TAB_ALIGNMENT.RIGHT)
        font(p.add_run("\t"), 10)
        add_math(p, text, 9, name=EQ_FONT)
        font(p.add_run(f"\t({self.eq_no})"), 10)

    def _caption(self, text, before=2, after=6, bold_label=None):
        p = self.doc.add_paragraph()
        pformat(p, WD_ALIGN_PARAGRAPH.JUSTIFY if len(text) > 70 else WD_ALIGN_PARAGRAPH.CENTER, before=before,
                after=after, line=1.0)
        font(p.add_run(text), 8)
        return p

    def b_fig(self, path, caption, span):
        self.fig_no += 1
        full = ROOT / path
        if span == "span":
            self._end_columns()
        p = self.doc.add_paragraph()
        pformat(p, WD_ALIGN_PARAGRAPH.CENTER, before=2, after=2, keep_next=True)
        width = 7.0 if span == "span" else (R.FIG_WIDTHS.get(path, 3.0))
        p.add_run().add_picture(str(full), width=Inches(width))
        self._caption(f"Fig. {self.fig_no}. {caption}")
        if span == "span":
            self._begin_columns()

    def _end_columns(self):
        s = self.doc.add_section(WD_SECTION.CONTINUOUS)
        set_cols(s, 1)

    def _begin_columns(self):
        s = self.doc.add_section(WD_SECTION.CONTINUOUS)
        set_cols(s, 2)

    def b_table(self, caption, header, rows, weights, size=8):
        self.tab_no += 1
        if not caption.startswith(f"TABLE {ROMAN[self.tab_no - 1]}."):
            raise SystemExit(f"table caption out of order: expected TABLE {ROMAN[self.tab_no - 1]}., got '{caption[:30]}'")
        cap = self._caption(caption, before=4, after=2)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.keep_with_next = True
        tbl = self.doc.add_table(rows=1 + len(rows), cols=len(header))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        cell_margins(tbl)
        total = sum(weights)
        widths = [Inches(COL_W * w / total) for w in weights]
        for ri, row in enumerate([header] + rows):
            tr = tbl.rows[ri]
            set_cant_split(tr)
            for ci, val in enumerate(row):
                c = tr.cells[ci]
                c.width = widths[ci]
                p = c.paragraphs[0]
                pformat(p, WD_ALIGN_PARAGRAPH.LEFT if ci == 0 else WD_ALIGN_PARAGRAPH.CENTER, line=1.0,
                        keep_next=ri < len(rows))
                add_math(p, str(val), size, italic_base=ri > 0)
                if ri == 0:
                    for r in p.runs:
                        r.bold = True
                top = 12 if ri in (0, 1) else None
                bottom = 12 if ri in (0, len(rows)) else None
                cell_borders(c, top=top, bottom=bottom)
        sp = self.doc.add_paragraph()
        pformat(sp, after=2, line=1.0)
        sp.paragraph_format.space_before = Pt(0)
        for r in sp.runs:
            font(r, 4)

    def b_algo(self, caption, lines):
        cap = self._caption(caption, before=4, after=2)
        cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
        cap.paragraph_format.keep_with_next = True
        tbl = self.doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell_margins(tbl, 40, 40, 80, 80)
        c = tbl.rows[0].cells[0]
        c.width = Inches(COL_W)
        cell_borders(c, top=12, bottom=12, left=12, right=12)
        c.paragraphs[0].text = ""
        for i, ln in enumerate(lines):
            p = c.paragraphs[0] if i == 0 else c.add_paragraph()
            pformat(p, WD_ALIGN_PARAGRAPH.LEFT, line=1.0, left=0.0)
            add_math(p, ln, 8)
        sp = self.doc.add_paragraph()
        pformat(sp, after=2, line=1.0)

    # --- references
    def references(self, ordered):
        p = self.doc.add_paragraph(style="Heading 1")
        pformat(p, WD_ALIGN_PARAGRAPH.CENTER, before=8, after=4, keep_next=True)
        font(p.add_run("References"), 10, small_caps=True)
        for i, key in enumerate(ordered, 1):
            text, spans = REFS[key]
            p = self.doc.add_paragraph()
            pformat(p, WD_ALIGN_PARAGRAPH.JUSTIFY, after=2, line=1.0, left=0.3, first=-0.3)
            font(p.add_run(f"[{i}]\t"), 8)
            p.paragraph_format.tab_stops.add_tab_stop(Inches(0.3))
            last = 0
            for a, b in spans:
                if a > last:
                    font(p.add_run(text[last:a]), 8)
                font(p.add_run(text[a:b]), 8, italic=True)
                last = b
            font(p.add_run(text[last:]), 8)


def citation_order(blocks):
    order = []
    for b in blocks:
        if b[0] == "p":
            for m in re.finditer(r"\{c:([a-z0-9,]+)\}", b[1]):
                for k in m.group(1).split(","):
                    if k not in order:
                        order.append(k)
    missing = [k for k in order if k not in REFS]
    if missing:
        raise SystemExit(f"citation keys without a reference entry: {missing}")
    return order


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "paper" / "OIOA_paper_updated.docx"))
    args = ap.parse_args()

    blocks = (S.INTRO + S.SURVEY + S.GAP + S.PROBLEM + S.METHOD + S.EXPERIMENT + R.build_results_blocks())
    order = citation_order(blocks)
    unused = [k for k in REFS if k not in order]
    if unused:
        print("warning: reference entries never cited (left out of the list):", unused)
    cite = {k: i for i, k in enumerate(order, 1)}
    b = Builder(cite)
    b.front(R.abstract(), S.KEYWORDS)
    for blk in blocks:
        b.add(blk)
    b.references(order)
    out = Path(args.out)
    b.doc.save(out)
    print("saved", out, f"({len(order)} references, {b.eq_no} equations, {b.fig_no} figures, {b.tab_no} tables)")
    if args.pdf:
        from docx2pdf import convert
        pdf = out.with_suffix(".pdf")
        convert(str(out), str(pdf))
        print("saved", pdf)


if __name__ == "__main__":
    main()
