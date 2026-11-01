from __future__ import annotations

import io
import os
import re
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageOps
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph


ROOT = Path(r"D:\ramanujans-magic-square")
SOURCE = ROOT / "Ramanujans_Magic_Square_Academic_Project_Report.docx"
OUTPUT = ROOT / "Ramanujans_Magic_Square_Academic_Project_Report_Revised.docx"


def new_paragraph(parent, before=None, after=None, style=None):
    p_el = OxmlElement("w:p")
    if before is not None:
        before.addprevious(p_el)
    elif after is not None:
        after.addnext(p_el)
    else:
        parent._element.body.append(p_el)
    p = Paragraph(p_el, parent)
    if style:
        p.style = style
    return p


def add_field(run, instruction, fallback="1"):
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    result = OxmlElement("w:t")
    result.text = fallback
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(result)
    run._r.append(end)


def bookmark_paragraph(p, name, bid):
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(bid))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(bid))
    p._p.insert(0, start)
    p._p.append(end)


def field_list_entry(doc, before, label, bookmark, style="Normal"):
    p = new_paragraph(doc, before=before, style=style)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.15), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    p.add_run(label)
    p.add_run("\t")
    add_field(p.add_run(), f"PAGEREF {bookmark} \\h")
    return p


def math_run(text):
    r = OxmlElement("m:r")
    t = OxmlElement("m:t")
    if text[:1].isspace() or text[-1:].isspace():
        t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


def group_node(tag, children):
    node = OxmlElement(tag)
    for child in children:
        node.append(child)
    return node


class MathParser:
    """Small LaTeX-to-OMML parser for the elementary formulas used in this report."""
    def __init__(self, source: str):
        self.s = source.strip()
        self.i = 0

    def read_group(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1
        if self.i < len(self.s) and self.s[self.i] == "{":
            self.i += 1
            children = self.read_sequence(stop="}")
            if self.i < len(self.s) and self.s[self.i] == "}":
                self.i += 1
            return children
        return self.read_atom()

    def read_atom(self):
        if self.i >= len(self.s):
            return []
        if self.s[self.i] == "\\":
            self.i += 1
            start = self.i
            while self.i < len(self.s) and self.s[self.i].isalpha():
                self.i += 1
            cmd = self.s[start:self.i]
            symbols = {"cdots": "⋯", "ldots": "…", "times": "×", "pi": "π", "leq": "≤", "geq": "≥", "qquad": "   ", "quad": "  ", ";": " ", ",": " "}
            if cmd == "frac":
                num = self.read_group()
                den = self.read_group()
                f = OxmlElement("m:f")
                fpr = OxmlElement("m:fPr")
                ftype = OxmlElement("m:type")
                ftype.set(qn("m:val"), "bar")
                fpr.append(ftype)
                f.append(fpr)
                f.append(group_node("m:num", num))
                f.append(group_node("m:den", den))
                return [f]
            if cmd in ("left", "right"):
                return self.read_atom()
            if cmd == "sum":
                return [math_run("∑")]
            if cmd == "cdot":
                return [math_run("·")]
            if cmd == "infty":
                return [math_run("∞")]
            return [math_run(symbols.get(cmd, cmd or "\\"))]
        if self.s[self.i] in "{}":
            ch = self.s[self.i]
            self.i += 1
            return [math_run(ch)]
        if self.s[self.i].isalpha() or self.s[self.i].isdigit():
            start = self.i
            while self.i < len(self.s) and (self.s[self.i].isalnum()):
                self.i += 1
            return [math_run(self.s[start:self.i])]
        ch = self.s[self.i]
        self.i += 1
        if ch in "^_":
            return [math_run(ch)]
        return [math_run(ch)]

    def read_sequence(self, stop=None):
        out = []
        while self.i < len(self.s) and (stop is None or self.s[self.i] != stop):
            while self.i < len(self.s) and self.s[self.i].isspace():
                self.i += 1
            if self.i >= len(self.s) or (stop is not None and self.s[self.i] == stop):
                break
            if self.s.startswith("\\,", self.i) or self.s.startswith("\\;", self.i):
                self.i += 2
                out.append(math_run(" "))
                continue
            atom = self.read_atom()
            if not atom:
                continue
            base = atom[0]
            sub = sup = None
            while self.i < len(self.s) and self.s[self.i] in "_^":
                marker = self.s[self.i]
                self.i += 1
                val = self.read_group()
                if marker == "_":
                    sub = val
                else:
                    sup = val
            if sub is not None and sup is not None:
                node = OxmlElement("m:sSubSup")
                node.append(group_node("m:e", [base]))
                node.append(group_node("m:sub", sub))
                node.append(group_node("m:sup", sup))
                out.append(node)
            elif sub is not None:
                node = OxmlElement("m:sSub")
                node.append(group_node("m:e", [base]))
                node.append(group_node("m:sub", sub))
                out.append(node)
            elif sup is not None:
                node = OxmlElement("m:sSup")
                node.append(group_node("m:e", [base]))
                node.append(group_node("m:sup", sup))
                out.append(node)
            else:
                out.extend(atom)
        return out

    def parse(self):
        return self.read_sequence()


def omml(expression, display=False):
    math = OxmlElement("m:oMath")
    for child in MathParser(expression).parse():
        math.append(child)
    if display:
        para = OxmlElement("m:oMathPara")
        para.append(math)
        return para
    return math


def add_math_parts(p, text):
    # Display equations are handled as one native Word math paragraph.
    display_match = re.fullmatch(r"\s*\\\[(.*?)\\\]\s*", text, flags=re.S)
    if display_match:
        p.clear()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p._p.append(omml(display_match.group(1), display=True))
        return True

    # Convert inline TeX delimiters and common plain-text formula spellings.
    token_re = re.compile(r"\\\((.+?)\\\)|M\s*\(n\)\s*=\s*n\s*\(n²?\s*\+\s*1\)\s*/\s*2|M\s*=\s*n\s*\(n²?\s*\+\s*1\)\s*/\s*2", re.S)
    matches = list(token_re.finditer(text))
    if not matches:
        return False
    p.clear()
    pos = 0
    for m in matches:
        if m.start() > pos:
            p.add_run(text[pos:m.start()])
        expr = m.group(1) if m.group(1) is not None else m.group(0)
        expr = expr.replace("²", "^2")
        p._p.append(omml(expr))
        pos = m.end()
    if pos < len(text):
        p.add_run(text[pos:])
    return True


def add_bookmark_list(doc, title, entries, anchor, bid_start):
    h = new_paragraph(doc, before=anchor, style="Normal")
    h.paragraph_format.page_break_before = True
    hr = h.add_run(title)
    hr.bold = True
    hr.font.size = Pt(15)
    # Repeated insertion immediately before the anchor preserves forward order.
    for label, bookmark in entries:
        p = new_paragraph(doc, before=anchor, style="Normal")
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(6.15), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        p.add_run(label)
        p.add_run("\t")
        add_field(p.add_run(), f"PAGEREF {bookmark} \\h")
    return h


def set_field_update(doc):
    settings = doc.settings.element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "true")


def insert_frontmatter(doc, first_chapter):
    # Preserve the source document's existing Table of Contents field and its format.
    # The new Lists of Figures and Tables are inserted after it and before Chapter 1.

    lof_entries = []
    for idx, p in enumerate(doc.paragraphs):
        if p.text.strip().startswith("Figure "):
            key = f"_FigureCaption{idx}"
            bookmark_paragraph(p, key, 2000 + idx)
            lof_entries.append((p.text.strip(), key))

    table_entries = []
    captions = [
        "Lo Shu normal 3×3 magic square",
        "Sequential arrangement used to construct a normal 4×4 square",
        "Completed normal 4×4 magic square",
        "Ramanujan’s date-based 4×4 magic square",
        "Users table schema",
        "Attempts table schema",
        "Game sessions table schema",
        "User achievements table schema",
        "Functional test cases and expected outcomes",
        "Project capability summary",
        "Ramanujan date-square reference grid",
        "Magic constants for supported normal-square orders",
        "Application environment variables",
    ]
    for i, table in enumerate(list(doc.tables)):
        label = f"Table {i+1}: {captions[i]}"
        p = Paragraph(OxmlElement("w:p"), table._parent)
        p.style = "Caption"
        p.add_run(label)
        table._tbl.addprevious(p._p)
        key = f"_TableCaption{i+1}"
        bookmark_paragraph(p, key, 3000 + i)
        table_entries.append((label, key))

    # Add dashboard chapter after the conclusion and before References.
    ref = next(p for p in doc.paragraphs if p.text.strip().upper() == "REFERENCES")
    chapter = new_paragraph(doc, before=ref._p, style="Heading 1")
    chapter.add_run("CHAPTER 15: DASHBOARD SCREENSHOTS")
    chapter.paragraph_format.page_break_before = True
    screens = [
        ("15.1 Home Page and Account Entry", "Figure 15.1: Home page and account entry screen.", "Home page and account entry"),
        ("15.2 User Registration and Login", "Figure 15.2: User registration and login screen.", "Registration and login"),
        ("15.3 Player Dashboard", "Figure 15.3: Player dashboard showing progress and achievements.", "Player dashboard"),
        ("15.4 Profile Dashboard", "Figure 15.4: Profile dashboard and account-management actions.", "Profile dashboard"),
        ("15.5 Magic Square Gameplay", "Figure 15.5: Magic-square gameplay interface.", "Gameplay interface"),
        ("15.6 Daily Challenge and Leaderboard", "Figure 15.6: Daily Challenge and leaderboard screens.", "Daily Challenge and leaderboard"),
        ("15.7 Formula and Learning Section", "Figure 15.7: Formula and learning section.", "Formula and learning section"),
        ("15.8 Admin Dashboard", "Figure 15.8: Administrator dashboard and review interface.", "Admin dashboard"),
    ]
    new_figures = []
    for j, (head, caption, short) in enumerate(screens, 1):
        h = new_paragraph(doc, before=ref._p, style="Heading 2")
        h.add_run(head)
        h.paragraph_format.page_break_before = True
        placeholder = new_paragraph(doc, before=ref._p, style="Normal")
        placeholder.alignment = WD_ALIGN_PARAGRAPH.CENTER
        placeholder.paragraph_format.space_before = Pt(72)
        placeholder.paragraph_format.space_after = Pt(72)
        placeholder.add_run(f"[SCREENSHOT PLACEHOLDER — {short}: image not supplied]")
        cap = new_paragraph(doc, before=ref._p, style="Caption")
        cap.add_run(caption)
        key = f"_DashboardFigure15_{j}"
        bookmark_paragraph(cap, key, 4000 + j)
        new_figures.append((caption, key))

    all_figures = lof_entries + new_figures
    add_bookmark_list(doc, "LIST OF FIGURES", all_figures, first_chapter._p, 5000)
    add_bookmark_list(doc, "LIST OF TABLES", table_entries, first_chapter._p, 6000)

    set_field_update(doc)


def grayscale_media(docx_path):
    temp = docx_path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("word/media/") and item.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                try:
                    im = Image.open(io.BytesIO(data))
                    alpha = im.getchannel("A") if im.mode in ("RGBA", "LA") else None
                    gray = ImageOps.grayscale(im.convert("RGB"))
                    if alpha is not None:
                        gray.putalpha(alpha)
                    out = io.BytesIO()
                    gray.save(out, format="PNG" if item.filename.lower().endswith(".png") else "JPEG", quality=95)
                    data = out.getvalue()
                except Exception:
                    pass
            zout.writestr(item, data)
    os.replace(temp, docx_path)


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    doc = Document(SOURCE)

    # Bring existing chapter and section labels into the document outline without changing their prose.
    for p in doc.paragraphs:
        t = p.text.strip()
        up = t.upper()
        if re.match(r"(?i)^CHAPTER\s+\d+\s*:", t):
            p.style = "Heading 1"
        elif re.match(r"^\d+\.\d+\s+", t):
            p.style = "Heading 2"
        elif up in {"FUTURE ENHANCEMENTS", "CONCLUSION", "REFERENCES", "BIBLIOGRAPHY", "APPENDIX"}:
            p.style = "Heading 1"
        if t == "1.4 Main Contribution":
            p.text = "1.5 Main Contribution"
        # Remove malformed outline formatting from empty paragraphs and body prose.
        if p.style.name == "Heading 2" and (not t or not re.match(r"^\d+\.\d+\s+", t)):
            p.style = "Normal"

    first_chapter = next(p for p in doc.paragraphs if p.text.strip().upper().startswith("CHAPTER 1:"))

    # Add dynamic contents and lists, then append the final screenshot chapter with explicit missing-image markers.
    insert_frontmatter(doc, first_chapter)

    # Convert existing TeX notation to editable Word math objects, including formulae in table cells.
    for p in doc.paragraphs:
        add_math_parts(p, p.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    add_math_parts(p, p.text)

    # Put an explicit end note after the existing appendix material.
    end_heading = doc.add_paragraph("Screenshot materials to supply", style="Heading 2")
    end_heading.paragraph_format.page_break_before = True
    doc.add_paragraph("The source document did not include dashboard screenshots. Replace the marked placeholders in Chapter 15 with the corresponding website images:", style="Normal")
    for item in ["Home page and account entry", "User registration and login", "Player dashboard", "Profile dashboard", "Magic-square gameplay", "Daily Challenge and leaderboard", "Formula and learning section", "Admin dashboard"]:
        doc.add_paragraph(item, style="List Bullet")
    doc.add_paragraph("In Microsoft Word, update the Table of Contents, List of Figures, and List of Tables fields after inserting screenshots (Ctrl+A, then F9) so page references reflect the final layout.", style="Normal")

    doc.save(OUTPUT)
    grayscale_media(OUTPUT)
    print(f"created={OUTPUT}")
    print(f"paragraphs={len(doc.paragraphs)} tables={len(doc.tables)} inline_shapes={len(doc.inline_shapes)}")


if __name__ == "__main__":
    main()
