from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont
import math

ROOT = Path(r'D:\ramanujans-magic-square')
WORK = ROOT / 'tmp' / 'docs_report'
OUT = ROOT / 'output' / 'reports' / 'Ramanujans_Magic_Square_Academic_Project_Report.docx'
WORK.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

# --- Figures: every graphic is an explanatory mathematical or historical figure. ---
def font(size, bold=False):
    candidates = [r'C:\Windows\Fonts\times.ttf', r'C:\Windows\Fonts\timesbd.ttf']
    p = candidates[1 if bold else 0]
    try: return ImageFont.truetype(p, size)
    except OSError: return ImageFont.load_default()

def draw_grid(name, grid, highlights=None, title=None, cell=112):
    n=len(grid); pad=58; top=100 if title else 38
    im=Image.new('RGB',(pad*2+n*cell,pad*2+n*cell+top),'white'); d=ImageDraw.Draw(im)
    if title: d.text((pad,20),title,fill='#18253d',font=font(26,True))
    colors={'row':'#f7d979','col':'#95c6ed','diag':'#b9d8ad','corner':'#edb1a8','center':'#d6b8e7','pair':'#a9d8cb'}
    for r in range(n):
        for c in range(n):
            color='#ffffff'
            if highlights:
                hits=[k for k, cells in highlights.items() if (r,c) in cells]
                if hits: color=colors[hits[0]]
            x=pad+c*cell; y=top+pad+r*cell
            d.rectangle((x,y,x+cell,y+cell),fill=color,outline='#26344c',width=3)
            d.text((x+cell/2,y+cell/2),str(grid[r][c]),fill='#16233b',font=font(32,True),anchor='mm')
    im.save(WORK/name)
    return WORK/name

ram=[[22,12,18,87],[88,17,9,25],[10,24,89,16],[19,86,23,11]]
normal=[[16,2,3,13],[5,11,10,8],[9,7,6,12],[4,14,15,1]]
draw_grid('fig01_ramanujan.png',ram,title='Ramanujan’s date-encoded 4 × 4 square')
groups={
 'row':{(0,c) for c in range(4)},
 'col':{(r,0) for r in range(4)},
 'diag':{(i,i) for i in range(4)},
 'corner':{(0,3),(3,0),(3,3)},
 'center':{(1,1),(1,2),(2,1),(2,2)},
}
def draw_group_panels():
    W,H=1500,900; im=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(im)
    d.text((45,22),'Selected groups in the 139 square',fill='#18253d',font=font(31,True))
    panels=[('Row 1: 139',{(0,c) for c in range(4)}),('Column 1: 139',{(r,0) for r in range(4)}),('Main diagonal: 139',{(i,i) for i in range(4)}),('Four corners: 139',{(0,0),(0,3),(3,0),(3,3)}),('Central 2 × 2: 139',{(1,1),(1,2),(2,1),(2,2)})]
    positions=[(55,100),(535,100),(1015,100),(295,495),(775,495)]
    cell=62
    for (label,selected),(px,py) in zip(panels,positions):
        d.text((px,py),label,fill='#18253d',font=font(21,True))
        ox=px+20; oy=py+48
        for r in range(4):
            for c in range(4):
                x=ox+c*cell; y=oy+r*cell; fill='#f2c96f' if (r,c) in selected else '#f6f8fa'
                d.rectangle((x,y,x+cell,y+cell),fill=fill,outline='#26344c',width=2)
                d.text((x+cell/2,y+cell/2),str(ram[r][c]),fill='#16233b',font=font(22,True),anchor='mm')
    im.save(WORK/'fig04_groups.png'); return WORK/'fig04_groups.png'
draw_group_panels()
draw_grid('fig03_normal.png',normal,title='Normal 4 × 4 example using 1 through 16')
odd=[[8,1,6],[3,5,7],[4,9,2]]
draw_grid('fig04_loshu.png',odd,title='The Lo Shu: an order-three normal square',cell=130)

def timeline():
    w,h=1450,490; im=Image.new('RGB',(w,h),'white'); d=ImageDraw.Draw(im)
    d.text((55,28),'Selected milestones in Srinivasa Ramanujan’s life',fill='#18253d',font=font(29,True))
    y=240; d.line((90,y,w-90,y),fill='#345475',width=6)
    items=[('1887','Born in Erode\n22 December'),('1903','Studies at\nKumbakonam'),('1913','Writes to G. H. Hardy'),('1914','Arrives in Cambridge'),('1918','Elected Fellow\nof the Royal Society'),('1919','Returns to India'),('1920','Dies in Kumbakonam\n26 April')]
    xs=[105+i*205 for i in range(len(items))]
    for i,(yr,txt) in enumerate(items):
        x=xs[i]; d.ellipse((x-11,y-11,x+11,y+11),fill='#be8730')
        up=i%2==0; ty=78 if up else 285
        d.line((x,y-12 if up else y+12,x,ty+62 if up else ty),fill='#9ba8b6',width=2)
        d.text((x-30,ty),yr,fill='#1a3152',font=font(24,True))
        d.multiline_text((x-54,ty+34),txt,fill='#34435b',font=font(17),spacing=5,align='center')
    im.save(WORK/'fig05_timeline.png'); return WORK/'fig05_timeline.png'
timeline()

def siamese_steps():
    im=Image.new('RGB',(1320,390),'white'); d=ImageDraw.Draw(im)
    d.text((40,20),'Siamese construction for order 3: move up-right; wrap at an edge',fill='#18253d',font=font(25,True))
    cells=88; x0=70; y0=95; g=[[0]*3 for _ in range(3)]; r,c=0,1
    for v in range(1,10):
        g[r][c]=v; nr,nc=(r-1)%3,(c+1)%3
        if g[nr][nc]: r=(r+1)%3
        else:r,c=nr,nc
    for r in range(3):
        for c in range(3):
            x=x0+c*cells;y=y0+r*cells
            d.rectangle((x,y,x+cells,y+cells),fill='#f3f7fb',outline='#26344c',width=3)
            d.text((x+cells/2,y+cells/2),str(g[r][c]),fill='#16233b',font=font(27,True),anchor='mm')
    notes=['Start with 1 in the middle of the top row.','For the next value, move one cell up and one right.','If that cell is occupied, move down one cell from the last position.']
    for i,t in enumerate(notes): d.text((390,118+i*74),f'{i+1}. {t}',fill='#2b3b50',font=font(22))
    im.save(WORK/'fig06_siamese.png'); return WORK/'fig06_siamese.png'
siamese_steps()

def doubly_even():
    # 4x4 complement construction visual: X cells receive 17 - natural value.
    base=[[r*4+c+1 for c in range(4)] for r in range(4)]
    comp=[[17-v if (r%4==c%4 or r%4+c%4==3) else v for c,v in enumerate(row)] for r,row in enumerate(base)]
    draw_grid('fig07_doubly_even.png',comp,title='Order-four complement pattern (doubly-even method)')
doubly_even()

def architecture():
    im=Image.new('RGB',(1500,620),'white'); d=ImageDraw.Draw(im)
    d.text((55,28),'Conceptual layers for construction, proof, and verification',fill='#18253d',font=font(28,True))
    boxes=[(80,150,420,390,'Input / specification','Order n; allowed values;\nrequired lines and groups'),(580,150,920,390,'Construction method','Odd: Siamese\n4k: complement pattern\n4k+2: singly-even method'),(1080,150,1420,390,'Verification','Permutation check; row, column,\ndiagonal and subgroup sums')]
    for x1,y1,x2,y2,t,s in boxes:
        d.rounded_rectangle((x1,y1,x2,y2),radius=18,fill='#f3f7fb',outline='#345475',width=4)
        d.text((x1+18,y1+24),t,fill='#18253d',font=font(24,True))
        d.multiline_text((x1+18,y1+85),s,fill='#34435b',font=font(20),spacing=8)
    for x in [435,935]:
        d.line((x,270,x+125,270),fill='#be8730',width=7)
        d.polygon([(x+125,270),(x+103,256),(x+103,284)],fill='#be8730')
    im.save(WORK/'fig08_framework.png'); return WORK/'fig08_framework.png'
architecture()

def shade(cell, fill):
    pr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); pr.append(shd)

def set_cell_margins(cell, top=85, start=100, bottom=85, end=100):
    tc=cell._tc; tcPr=tc.get_or_add_tcPr(); mar=OxmlElement('w:tcMar')
    for m,v in [('top',top),('start',start),('bottom',bottom),('end',end)]:
        e=OxmlElement('w:'+m); e.set(qn('w:w'),str(v)); e.set(qn('w:type'),'dxa'); mar.append(e)
    tcPr.append(mar)

def set_repeat_table_header(row):
    trPr=row._tr.get_or_add_trPr(); el=OxmlElement('w:tblHeader'); el.set(qn('w:val'),'true'); trPr.append(el)

doc=Document()
sec=doc.sections[0]
sec.page_width=Inches(8.27); sec.page_height=Inches(11.69)
sec.top_margin=Inches(.82); sec.bottom_margin=Inches(.78); sec.left_margin=Inches(.9); sec.right_margin=Inches(.82)
sec.header_distance=Inches(.38); sec.footer_distance=Inches(.36)
styles=doc.styles
for stylename in ['Normal','Body Text']:
    st=styles[stylename]; st.font.name='Times New Roman'; st.font.size=Pt(11.5); st.font.color.rgb=RGBColor(0,0,0)
    st._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
    st.paragraph_format.line_spacing=1.3; st.paragraph_format.space_after=Pt(7)
    st.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
for name,size in [('Title',25),('Subtitle',15),('Heading 1',17),('Heading 2',13),('Heading 3',11.5)]:
    st=styles[name]; st.font.name='Times New Roman'; st.font.size=Pt(size); st.font.bold=name!='Subtitle'; st.font.color.rgb=RGBColor(0,0,0)
    st._element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
    st.paragraph_format.keep_with_next=True; st.paragraph_format.space_before=Pt(11); st.paragraph_format.space_after=Pt(7)
styles['Heading 1'].paragraph_format.page_break_before=True
styles['Caption'].font.name='Times New Roman'; styles['Caption'].font.size=Pt(10); styles['Caption'].font.italic=True; styles['Caption'].font.color.rgb=RGBColor(45,55,70)

header=sec.header.paragraphs[0]; header.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=header.add_run("RAMANUJAN’S MAGIC SQUARE  |  MATHEMATICAL PROJECT REPORT"); r.font.name='Times New Roman'; r.font.size=Pt(8); r.font.color.rgb=RGBColor(70,80,92)
footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
rr=footer.add_run('Department of [Department]  •  '); rr.font.name='Times New Roman'; rr.font.size=Pt(8)
fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); footer._p.append(fld)

def page(): doc.add_page_break()
def p(text='',align=None,boldlead=None):
    para=doc.add_paragraph()
    if align is not None: para.alignment=align
    if boldlead and text.startswith(boldlead):
        para.add_run(boldlead).bold=True; para.add_run(text[len(boldlead):])
    else: para.add_run(text)
    return para
def centered(text,size=12,bold=False):
    x=doc.add_paragraph(); x.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=x.add_run(text); r.font.name='Times New Roman'; r.font.size=Pt(size); r.bold=bold; return x
def table(headers, rows, widths=None, font_size=9.5):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Table Grid'; t.autofit=False
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; c.text=str(h); shade(c,'234367'); set_cell_margins(c); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for run in c.paragraphs[0].runs: run.font.name='Times New Roman'; run.font.size=Pt(font_size); run.font.bold=True; run.font.color.rgb=RGBColor(255,255,255)
    set_repeat_table_header(t.rows[0])
    for idx,row in enumerate(rows):
        cells=t.add_row().cells
        for i,val in enumerate(row):
            cells[i].text=str(val); cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER; set_cell_margins(cells[i])
            if idx%2: shade(cells[i],'F0F4F8')
            for para in cells[i].paragraphs:
                para.paragraph_format.space_after=Pt(2); para.paragraph_format.line_spacing=1.08
                for run in para.runs: run.font.name='Times New Roman'; run.font.size=Pt(font_size); run.font.color.rgb=RGBColor(0,0,0)
    if widths:
        for row in t.rows:
            for i,w in enumerate(widths): row.cells[i].width=Inches(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)
    return t
def figure(path, number, caption, explanation, width=5.6):
    para=doc.add_paragraph(); para.alignment=WD_ALIGN_PARAGRAPH.CENTER; para.paragraph_format.keep_with_next=True
    para.add_run().add_picture(str(path),width=Inches(width))
    cap=doc.add_paragraph(style='Caption'); cap.alignment=WD_ALIGN_PARAGRAPH.CENTER; cap.paragraph_format.keep_with_next=True
    cap.add_run(f'Figure {number}. {caption}')
    p(explanation)

# Front matter follows the sample report's formal academic presentation.
centered('[INSTITUTION NAME]',18,True); centered('[Affiliated University / Board]',12); centered('[Department of __________________________]',14,True)
page(); centered('A PROJECT REPORT',16,True); centered('ON',12); centered('RAMANUJAN’S MAGIC SQUARE',24,True)
centered('Historical context, mathematical structure, construction and verification',13)
p('Submitted in partial fulfilment of the requirements for the award of the degree / diploma in',align=WD_ALIGN_PARAGRAPH.CENTER)
centered('[Programme / Course Name]',14,True); p('Submitted by',align=WD_ALIGN_PARAGRAPH.CENTER); centered('[Student Name]  |  [USN / Enrollment Number]',13,True)
p('Under the guidance of',align=WD_ALIGN_PARAGRAPH.CENTER); centered('[Guide Name and Designation]',13,True); centered('[Department]  •  [Institution]  •  [Academic Year]',11)
page(); doc.add_heading('CERTIFICATE',0)
p('This is to certify that the project report entitled “Ramanujan’s Magic Square: Historical Context, Mathematical Structure, Construction and Verification” is a bonafide work prepared by [Student Name], bearing [USN / Enrollment Number], under my guidance and supervision in partial fulfilment of the requirements for [Programme / Course] at [Institution Name].')
p('The work presented here examines the famous date-encoded 4 × 4 square associated with Srinivasa Ramanujan, places it within the broader theory of magic squares, derives its principal properties, and documents reproducible methods for constructing and checking related examples. The mathematical statements and citations have been reviewed to the extent indicated in the report.')
p('This certificate records academic supervision and does not assert that any external institution has approved the report. The institution, degree, signatures and dates below must be completed by the student and authorised signatories before submission.')
table(['Role','Name and designation','Signature','Date'],[['Project guide','[Guide Name]','',''],['Head of Department','[HOD Name]','',''],['External examiner','[Examiner Name]','','']],widths=[1.25,2.35,1.35,1.05])
page(); doc.add_heading('DECLARATION',0)
p('I, [Student Name], declare that this project report titled “Ramanujan’s Magic Square: Historical Context, Mathematical Structure, Construction and Verification” is prepared by me for academic submission. The exposition is original to this report except where ideas, historical accounts, diagrams, data or wording are attributed to cited sources.')
p('I have distinguished the classical Ramanujan date square, whose magic sum is 139, from a normal 4 × 4 square using 1 through 16, whose magic sum is 34. I have not treated 1729 as an entry in the familiar date square. Any figures reproduced from the user-supplied images are credited as such; newly drawn figures are explanatory diagrams created for this report.')
p('I understand that the placeholders for institution, course, student, guide, signatures and academic year must be completed accurately. I also understand that the department must confirm its required citation and formatting rules before final submission.')
p('Place: [Place]'); p('Date: [Date]'); p('Signature of the student: ______________________________')
page(); doc.add_heading('ACKNOWLEDGEMENT',0)
p('I express my sincere gratitude to [Guide Name], [Designation], for guidance in defining the scope of this project and for encouraging careful verification of the mathematical claims. I thank the faculty of [Department] and [Institution] for the academic environment and reference materials that supported this study.')
p('I acknowledge the authors and editors whose historical and mathematical works are listed in the references, especially the scholarship on Ramanujan’s life and notebooks, the study of magic-square construction, and published explanations of the 4 × 4 square made from his birth date. The user-provided project-report PDF informed the organisation and formal register of this document; its unrelated subject matter has not been copied.')
p('I also acknowledge the images supplied with the project brief. Where a supplied image is used, its role is identified in the caption. The mathematical diagrams in this report were redrawn to make their entries, groups and legends legible and to avoid reproducing ambiguous annotations.')
p('Finally, I thank my family and classmates for their support during preparation of this project. Any errors that remain are my responsibility.')
p(' [Student Name]')
page(); doc.add_heading('ABSTRACT',0)
p('This project studies magic squares through the celebrated 4 × 4 square associated with Srinivasa Ramanujan. The familiar date square places 22, 12, 18 and 87 in its first row, encoding 22 December 1887. Its rows, columns and two principal diagonals sum to 139. The four corner entries and the central 2 × 2 block also sum to 139, alongside further structured groups. These properties are derived from the displayed entries rather than treated as coincidences.')
p('A distinction central to the analysis is that 139 belongs to Ramanujan’s date-encoded square, whereas 34 is the normal magic constant for an order-four square containing each of 1 through 16 once. In the normal case, complementary pairs sum to 17, and both the corner set and central 2 × 2 set sum to 34. The number 1729 is discussed separately as the smallest positive integer expressible as a sum of two positive cubes in two distinct ways; it does not occur in the usual date square.')
p('The report reviews the history and definition of magic squares, derives the normal magic-constant formula, explains odd, doubly-even and singly-even construction methods, and gives proof-oriented checks, worked examples and a reproducible verification procedure. It discusses variants, enumeration, symmetry, computational limitations, pedagogical uses and directions for further study. The approach combines historical source criticism with elementary algebra, combinatorics and transparent arithmetic verification.')
p('Keywords: Srinivasa Ramanujan; magic square; normal magic square; order four; magic constant; Siamese method; doubly-even square; verification; 1729.')
page(); doc.add_heading('CONTENTS',0)
contents=['Certificate','Declaration','Acknowledgement','Abstract','List of Figures','List of Tables','Notation and Abbreviations']
chapters=[
('1','Introduction',['Background and motivation','Project problem and scope','Objectives and research questions','Method and evidence','Organisation of the report']),
('2','Historical and literature review',['Srinivasa Ramanujan: life and mathematical setting','Education, notebooks and self-directed study','The Cambridge years and mathematical collaboration','The date square and its attribution','A short history of magic squares','History, legend and evidence','Prior studies and the present project']),
('3','Mathematical foundations',['Definitions and terminology','Normal squares and the value set','Deriving the normal magic constant','Why order two is impossible','Symmetry, complements and equivalence']),
('4','Ramanujan’s 4 × 4 date square',['The displayed square and encoded date','Line-by-line verification','The central 2 × 2 and corner sums','Other four-cell groups and pair structure','What the number 139 means','The number 1729: a separate connection']),
('5','Proofs of the principal properties',['The global sum and line target','Proof of row and column totals','Proof of diagonal totals','Proof of the corner total','Proof of the central block total','Interpreting the pair relationships']),
('6','Constructing magic squares',['Construction goals and constraints','Odd-order Siamese method','Worked order-three construction','Doubly-even orders','Worked order-four complement construction','Singly-even orders','Construction versus verification']),
('7','Worked mathematical examples',['Normal order-three square','A normal order-four square and complementary pairs','Order-five constant and structural checks','Scaling and translation','A date square built from a birth date']),
('8','Verification methodology and computational study',['Verification specification','Permutation and range checks','Line-sum algorithm','Subgroup and property checks','Test data and expected results','Complexity, reliability and limits']),
('9','Generalizations and related research',['Semi-magic and panmagic squares','Associative and bordered squares','Non-normal and composite entries','Enumeration and symmetry classes','Higher-dimensional magic arrays','Research directions']),
('10','Applications, pedagogy and interpretation',['Classroom use and mathematical reasoning','Recreational mathematics and puzzles','Art, culture and historical interpretation','Digital and computational demonstrations']),
('11','Limitations and critical discussion',['Attribution and source limitations','What the familiar square does not prove','Limits of finite examples','Reproducibility and notation','Ethical use of historical images']),
('12','Results and discussion',['Summary of verified results','Comparison of the two order-four squares','Answers to the research questions','Implications for teaching and further work']),
('13','Conclusion and future scope',['Conclusion','Recommendations for extension']),
('References',[],[]),('Appendices',[],[])]
for num,title,sub in chapters:
    contents.append(f'Chapter {num}: {title}')
    contents.extend('    '+s for s in sub)
contents.extend(['Appendix A. Arithmetic verification ledger','Appendix B. Construction pseudocode','Appendix C. Test cases','Appendix D. Glossary','Appendix E. Source and figure notes'])
for item in contents: p(item)
page(); doc.add_heading('LIST OF FIGURES',0)
for item in [
'Figure 1. Selected milestones in Ramanujan’s life','Figure 2. Ramanujan’s date-encoded 4 × 4 square','Figure 3. The Lo Shu order-three normal square','Figure 4. Selected 139-sum groups in the date square','Figure 5. Construction and verification framework','Figure 6. Siamese construction for order three','Figure 7. Order-four complement pattern','Figure 8. A normal 4 × 4 square using 1 through 16','Figure 9. User-supplied physical model of the date square']:
    p(item)
page(); doc.add_heading('LIST OF TABLES',0)
for item in ['Table 1. Research questions and evidence','Table 2. Normal magic constants for orders 3–10','Table 3. Entries and arithmetic checks for the date square','Table 4. Distinguishing the 139 and 34 squares','Table 5. Construction method by order class','Table 6. Verification test cases','Table 7. Properties and proof status','Table 8. Selected definitions and notation']:
    p(item)
page(); doc.add_heading('NOTATION AND ABBREVIATIONS',0)
table(['Symbol / term','Meaning'],[
('n','Order of a square: number of rows and columns.'),('M','Magic constant shared by the required lines.'),('aᵢⱼ','Entry in row i and column j.'),('Nₙ','Normal value set {1,2,…,n²}.'),('Complement','For a normal order-n square, the partner x′=n²+1−x.'),('Normal square','Uses each integer from 1 through n² exactly once.'),('Semi-magic','All rows and columns share a target; diagonal conditions may be absent.'),('Panmagic','Broken/torus diagonals also meet the target, under the stated convention.'),('Doubly-even','Order divisible by 4.'),('Singly-even','Even order not divisible by 4.'),('UTC','Coordinated Universal Time; included only in cited modern context, not in the mathematical results.')],widths=[1.6,4.4])
p('Indices are one-based in displayed tables and zero-based only in pseudocode. “Main diagonals” means the two corner-to-corner diagonals. “Corner sum” denotes the sum of the four entries at the corners, not any arbitrary four cells.')

first_subsection=True
def chapter(num,title):
    global first_subsection
    first_subsection=True
    doc.add_heading(f'CHAPTER {num}\n{title.upper()}',1)
def section(title, paragraphs, figure_data=None, tables=None, equations=None):
    global first_subsection
    if isinstance(figure_data, dict):
        tables = figure_data.get('tables', tables)
        equations = figure_data.get('equations', equations)
        figure_data = figure_data.get('figures')
    if not first_subsection: doc.add_page_break()
    first_subsection=False
    doc.add_heading(title,2)
    for txt in paragraphs: p(txt)
    if equations:
        for eq in equations: centered(eq,13,True)
    if tables:
        for headers, rows, widths in tables: table(headers,rows,widths)
    if figure_data:
        for args in figure_data: figure(*args)

chapter('1','Introduction')
sections=[
('1.1 Background and motivation',[
'A magic square is a square array of numbers arranged so that selected lines have an equal sum. The familiar task of checking the rows is only the beginning: columns, principal diagonals, complementary pairs and carefully chosen subarrays reveal additional structure. Magic squares are therefore useful as compact laboratories for arithmetic, algebra, combinatorics, symmetry and proof. Their visual form makes a claim easy to state, while their interlocking conditions make it necessary to reason carefully before accepting it.',
'This report focuses on the 4 × 4 square associated with Srinivasa Ramanujan because it combines a personal date, a common line total and several non-obvious equalities. Its first row is 22, 12, 18, 87, representing 22 December 1887. Every row, column and principal diagonal sums to 139. Those entries are not the integers 1 through 16; consequently, the normal-square formula yielding 34 does not describe this particular arrangement. Understanding that difference is part of the project rather than a technical footnote.',
'The topic is appropriate for a student project because it moves from observation to proof. A learner can first compute a line, then formulate a conjecture, test a second group, and finally derive general principles that explain the pattern. The report combines historical context with direct verification, so that admiration for Ramanujan’s ingenuity remains connected to explicit evidence.'
]),
('1.2 Project problem and scope',[
'Popular descriptions sometimes merge three distinct ideas: Ramanujan’s date square with total 139; a normal order-four square with total 34; and the number 1729 associated with a famous anecdote about sums of cubes. They are related through Ramanujan’s biography and the broad subject of recreational number theory, but they are not one numerical object. A report that assigns 34 or 1729 to the familiar date square would be incorrect. The first problem addressed here is therefore one of precise identification: specify the square, its entries, the rule being checked and the meaning of its target sum.',
'The mathematical scope includes normal magic squares, the formula for their magic constant, existence by order class, elementary construction algorithms, proof of selected properties, and related variants. The historical scope covers well-established biographical milestones and the transmission of the date-square story, with qualification where a popular account is stronger than the surviving evidence. The report does not claim to reproduce Ramanujan’s original derivation unless a primary source is cited.',
'The project does not attempt a complete classification of all integer magic squares, a proof of every published enumeration result, or a new theorem. It aims instead to present a rigorous, reproducible student-level study whose calculations can be checked independently.'
]),
('1.3 Objectives and research questions',[
'The central objective is to explain, construct and verify the famous 4 × 4 date square without confusing its properties with those of a normal square. The report has five practical objectives: define the relevant classes of squares; establish the general normal magic-constant formula; verify the 139 square by arithmetic and algebra; demonstrate standard construction families; and design a finite verification procedure suitable for hand checking or implementation.',
'The research questions are: (i) why is the normal order-four constant 34, while the date square has total 139? (ii) which row, column, diagonal, corner and central-block sums can be established directly? (iii) how do construction methods differ for odd, doubly-even and singly-even orders? (iv) what does the date encoding contribute to the square’s historical and pedagogical value? and (v) what claims about 17, 1729 and special groups are mathematically warranted?',
'These questions are answered in stages. Definitions and general results precede the case study; the proofs then refer to explicitly numbered rows and columns. The construction and verification chapters separate how an arrangement is produced from how its properties are tested. The discussion chapter records limits and areas where a student should consult original mathematical literature.'
]),
('1.4 Method and evidence',[
'The method is a structured mathematical investigation. First, the report identifies a stable version of Ramanujan’s date square and transcribes its entries into a table. Second, it computes the required sums independently, using both direct addition and identities based on the total of all entries. Third, it compares this square with a normal order-four example to isolate the roles of the value set and the arrangement. Fourth, it states construction rules as algorithms and tests their outputs against the definition.',
'Historical statements are checked against scholarly biographies and source-oriented mathematical writing. The report distinguishes an established date of birth from a story about how a particular square was composed. For the 1729 anecdote, it gives the exact cube identity and avoids treating the anecdote as a claim about the grid. Citations use a numbered reference style, consistent with formal technical project reports; complete publication details appear at the end.',
'The verification is deterministic and reproducible: each entry can be inspected, each line can be summed, and each algorithm can be implemented without external services. A computer program can reduce arithmetic mistakes, but it does not replace the proof of a general formula. The distinction between an empirical check and a mathematical argument is maintained throughout.'
]),
('1.5 Organisation of the report',[
'Chapter 2 introduces Ramanujan’s life, the historical setting of magic squares and the source status of the date square. Chapter 3 defines normal and non-normal squares, derives the standard constant and explains the impossibility of an order-two normal square. Chapters 4 and 5 present the 139 square and prove its principal properties, with a separate discussion of the 34/17 facts and the 1729 connection.',
'Chapters 6 and 7 describe construction methods and worked examples. Chapter 8 provides an explicit checking procedure and test plan. Chapter 9 surveys generalisations and selected research themes; Chapter 10 considers teaching and interpretation. Chapter 11 evaluates source, mathematical and computational limitations. Chapter 12 summarises verified results and answers the research questions. Chapter 13 concludes and proposes extensions.',
'The appendices provide a verification ledger, pseudocode, test cases, a glossary and figure notes. They are designed to make the report useful as a study document after the narrative has been read. The structural sequence follows the academic report model supplied with the project brief, while all substantive content has been developed for the present topic.'
])]
for s in sections: section(*s)

chapter('2','Historical and literature review')
sections=[
('2.1 Srinivasa Ramanujan: life and mathematical setting',[
'Srinivasa Ramanujan (1887–1920) was born in Erode, in the Madras Presidency of British India, and grew up largely in Kumbakonam. His work later became influential in number theory, infinite series, continued fractions and partition theory. His biography is often told as a story of extraordinary intuition, but a careful account also recognises the roles of family, teachers, notebooks, correspondence and collaborators. The timeline in Figure 1 identifies selected dates rather than attempting to represent every stage of his life.',
'Ramanujan’s mathematical development took place in a setting where access to advanced texts and formal research training was uneven. He studied available books intensively and recorded results in notebooks, many without the demonstrations that would be expected in a contemporary research paper. This difference in exposition is not evidence that the results were arbitrary. It means that later readers and collaborators had to reconstruct proofs, verify statements and identify the assumptions behind them.',
'The famous date square offers a small entry point into this larger biography. Its compact arrangement links a personal date with an invariant sum, but it should not be used as a complete representation of Ramanujan’s mathematical achievements. The much broader research record, including work on partitions and modular forms, is documented in collected papers, notebook editions and scholarly biographies [1]–[4].'
],[(WORK/'fig05_timeline.png',1,'Selected milestones in Ramanujan’s life','Figure 1 places the birth-date encoding in its biographical context. The timeline is selective; it does not imply that these seven dates alone describe Ramanujan’s life.',6.2)]),
('2.2 Education, notebooks and self-directed study',[
'Ramanujan’s early mathematical work was shaped by self-directed study and by the books he could obtain. A commonly discussed influence is G. S. Carr’s synopsis of elementary results, a work organised around concise propositions. Researchers have considered how this style of reading may have encouraged him to accumulate identities and formulas. The claim should be expressed carefully: influence is a historically grounded interpretation, not a complete causal explanation for his mathematical creativity [2], [3].',
'His notebooks preserve many identities and theorems in compressed form. The notebooks became the subject of extensive editorial work because a bare formula may conceal a delicate condition, an omitted proof, or a statement whose generality must be tested. Berndt’s analyses provide examples of how later scholarship reconstructs and validates notebook entries [4]. This process offers a useful model for the present project: transcription, checking and proof are complementary stages.',
'The date square itself is often introduced through school demonstrations rather than as a theorem from a major research paper. The present report accordingly avoids assigning it the same documentary status as a published article. The grid is treated as a well-known construction associated with Ramanujan and examined through its stated entries. When the historical path of a particular version is uncertain, that uncertainty is kept visible.'
]),
('2.3 The Cambridge years and mathematical collaboration',[
'In 1913 Ramanujan wrote to G. H. Hardy, sending examples of mathematical results that prompted Hardy to recognise the unusual depth of the work. With support from Hardy and others, Ramanujan travelled to Cambridge in 1914. Their collaboration produced important results, including work on partitions and the asymptotic behaviour of the partition function. Ramanujan was elected a Fellow of the Royal Society in 1918 and of Trinity College, Cambridge, in the same period [1]–[3].',
'Collaboration matters to the history because mathematics is not only a collection of isolated discoveries. Communication, proof, editorial interpretation and institutional access all affect which ideas are developed and preserved. Hardy’s role should be acknowledged without turning the story into a simple rescue narrative: Ramanujan brought a substantial body of original mathematics, while Hardy and Cambridge provided opportunities, dialogue and a new research environment.',
'Ramanujan returned to India in 1919 and died in 1920. Modern accounts use these dates to frame an exceptionally short life and a large mathematical legacy. They do not establish that every anecdote about him is verbatim or contemporaneously recorded. This distinction becomes especially important for the famous taxi story attached to 1729, which is best presented as Hardy’s later recollection rather than a transcript.'
]),
('2.4 The date square and its attribution',[
'The widely circulated 4 × 4 arrangement begins with 22, 12, 18, 87. These four values encode Ramanujan’s birth date, 22 December 1887, in day-month-year form. The complete arrangement printed in this report is 22, 12, 18, 87; 88, 17, 9, 25; 10, 24, 89, 16; 19, 86, 23, 11. Each row, column and principal diagonal has sum 139 [5], [6].',
'The association of this square with Ramanujan is widely repeated in educational mathematics literature. However, a report should distinguish the well-established mathematical facts about the displayed grid from the documentary question of when, where and in what exact form Ramanujan first wrote it down. A source that reproduces the square establishes the form it presents; it may not establish a full chain of manuscript provenance. For that reason, this project uses the description “the square associated with Ramanujan” and gives the date-based interpretation as a conventional attribution.',
'The arithmetic can be verified without relying on the attribution. If a different transcription is encountered, it should be checked cell by cell before copying its claimed properties. The image supplied with the project brief shows the same familiar 139 square in a handmade teaching display, while the report’s newly drawn Figure 2 supplies a clean, legible transcription for all proofs.'
],[(WORK/'fig01_ramanujan.png',2,'Ramanujan’s date-encoded 4 × 4 square','Figure 2 shows the entries used throughout the case study. The first row encodes 22 December 1887 and sums to 139.',4.9)]),
('2.5 A short history of magic squares',[
'Magic squares appear in mathematical and cultural traditions across several regions. The Lo Shu tradition in China is often cited as an early, influential example of an order-three square, although traditional narratives and the dating of surviving written evidence are not always the same. The mathematical array commonly printed as the Lo Shu uses 1 through 9 and has row, column and diagonal sum 15. Figure 3 depicts one orientation; rotations and reflections give equivalent arrangements under the usual symmetry convention.',
'In South Asian, Arabic, Persian and European traditions, squares were studied for numerical, recreational, astronomical or symbolic purposes. The transmission of methods was complex and should not be reduced to a single origin claim. Medieval Arabic mathematical texts, later European treatises and early modern recreational mathematics all contributed to the subject’s development. A historical overview in this report therefore describes documented traditions rather than asserting that every culture adopted a single identical object [7]–[10].',
'By the early modern period, magic squares had entered mathematical recreations and printed works. Albrecht Dürer’s engraving Melencolia I includes a 4 × 4 normal magic square dated 1514 in its bottom row. That square has magic sum 34 and uses the numbers 1 through 16. It provides a useful comparison with Ramanujan’s non-normal 139 square, while also illustrating that a 4 × 4 grid can carry historical or artistic meaning beyond its line sums.'
],[(WORK/'fig04_loshu.png',3,'The Lo Shu order-three normal square','Figure 3 gives a classical small example with all rows, columns and principal diagonals summing to 15.',4.0)]),
('2.6 History, legend and evidence',[
'Historical writing about magic squares must separate an object’s mathematical properties from narratives about its origin. A square can be verified from its entries even if its first creator is unknown. Conversely, a traditional origin story can be culturally significant without serving as a dated proof of when a particular arrangement was first recorded. This report uses qualifiers such as “traditionally associated,” “commonly attributed” and “surviving evidence indicates” when the source record calls for them.',
'The same source-critical approach applies to Ramanujan. The dates of birth and death and the Cambridge milestones are supported by biographical scholarship. The exact sequence by which the 139 square entered popular teaching material is less central to the arithmetic and is not treated as settled merely because many websites repeat it. The report cites mathematical and scholarly sources where possible and identifies educational restatements as secondary sources.',
'A project report should not overstate a source. If a claim is based on an anecdote recalled later, it should be presented as such. If a square appears in a modern teaching article, that article supports the square’s current pedagogical presentation, not necessarily a claim about the original manuscript. These distinctions preserve trust in the mathematical argument.'
]),
('2.7 Prior studies and the present project',[
'The literature relevant to this project falls into four groups: biographies and collected works of Ramanujan; general treatments of magic-square construction; studies of historical examples such as the Lo Shu and Dürer squares; and modern expository articles explaining the date square. Works by Hardy, Berndt and Andrews provide a foundation for Ramanujan’s broader mathematical context [1]–[4]. A survey of construction methods and historical cases can be found in the recreational and mathematical literature [7]–[10].',
'Research on enumeration illustrates that even order four can become a substantial combinatorial problem once the value set, target sum, normality and symmetry equivalence are specified. The enumeration of normal 4 × 4 magic squares is not obtained simply by permuting sixteen entries: row and column constraints sharply reduce the possibilities, and symmetry conventions affect reported counts [11]. The present report does not reproduce an enumeration proof, but it explains why this is a distinct research task.',
'The contribution of this project is pedagogical synthesis rather than a new classification. It places the famous 139 arrangement next to the normal 34 case, proves a set of highlighted identities, explains algorithm families, and offers a testable verification protocol. The synthesis addresses a common learning problem: attractive visual examples can lead to incorrect mixing of properties unless the number set and the definition are stated precisely.'
])]
for s in sections: section(*s)

chapter('3','Mathematical foundations')
sections=[
('3.1 Definitions and terminology',[
'An order-n square is an n × n array A=(aᵢⱼ), where i and j range from 1 to n. A row sum is Rᵢ=Σⱼaᵢⱼ; a column sum is Cⱼ=Σᵢaᵢⱼ. The two principal diagonal sums are D₁=Σᵢaᵢᵢ and D₂=Σᵢaᵢ,n+1−i. A magic square in the standard sense has every row, every column and both principal diagonals equal to one common constant M.',
'Some authors use “magic square” for the full definition and “semi-magic square” for an array whose rows and columns agree but whose diagonals may not. Terminology varies in specialised literature, so a report should declare its convention. This work uses the full row-column-two-diagonal definition unless a variant is explicitly named. Extra properties such as equal corner sums or pandiagonal sums are not part of the basic definition.',
'The term “normal” adds a value-set constraint: the entries are the integers 1 through n², each used exactly once. The date square associated with Ramanujan is a magic square under the line-sum definition but is not normal because it uses values such as 87 and 89 and does not use precisely 1 through 16. That classification determines which constant formula applies.'
]),
('3.2 Normal squares and the value set',[
'For a normal order-n square, the total of all entries is fixed before any entries are arranged. The set is {1,2,…,n²}. Pairing the first and last values, the second and second-last, and so on shows that the mean entry is (n²+1)/2. Multiplying by the n² entries gives a grand total n²(n²+1)/2. This identity depends only on the value set, not on a magic arrangement.',
'If every one of the n rows sums to M, then summing the row equations counts every entry exactly once, so nM equals the grand total. Therefore M=n(n²+1)/2. The same result follows by summing columns. This derivation makes clear why a normal square has a predetermined target and why a square with a different set of entries need not have that target.',
'For order four the formula gives 4(16+1)/2=34. Ramanujan’s date square has total 16-cell sum 4×139=556, because it has four rows each totaling 139. Its entries do not sum to 136, the total of 1 through 16. It is thus mathematically inconsistent to apply the normal formula to that date square.'
],{'equations':['Mₙ = (1/n) Σₖ₌₁ⁿ² k = n(n² + 1)/2']}),
('3.3 Deriving the normal magic constant',[
'The formula can be derived in a way that highlights its assumptions. Let S be the sum of the entries. For a normal square, S=1+2+⋯+n². The arithmetic-series identity gives S=n²(n²+1)/2. A magic square has n rows with common sum M, so S=nM. Dividing by n yields M=n(n²+1)/2. No construction method is needed for the derivation; it applies to any normal magic square if one exists.',
'The first few values are useful checks: order three has M=15; order four has 34; order five has 65; order six has 111; order seven has 175; order eight has 260; order nine has 369; and order ten has 505. These values help detect transcription errors, but passing a total check does not prove a square is valid. All rows, columns and principal diagonals still need inspection, and normality must be checked separately.',
'For a non-normal square, the line target can still be common, but it follows from the chosen entries and construction. For example, the date square’s target is read from its lines and confirmed by the full-entry total. The value 139 is not a contradiction to the formula; it signals that the formula’s normal-entry premise is absent.'
],{'tables':[(['Order n','Entry set total','Normal magic constant'],[[n,str(n*n*(n*n+1)//2),str(n*(n*n+1)//2)] for n in range(3,11)],[1.1,2.2,2.0])]}),
('3.4 Why order two is impossible',[
'Suppose a normal 2 × 2 square existed, with entries a,b in the top row and c,d in the bottom row. Equal row sums require a+b=c+d. Equal column sums require a+c=b+d. Subtracting these equations gives b=c; substituting back gives a=d. That repeats entries, contradicting normality. The contradiction uses the distinct-entry condition; an all-equal or repeated-entry array may satisfy equal lines but is not a normal magic square.',
'A second argument uses the diagonal conditions. If both principal diagonals are equal, then a+d=b+c. Combine this with equality of the two rows, a+b=c+d. Subtracting the equations gives a−d=c−b; together with a+d=b+c, the entries must form repeated values in the normal case. The row-column derivation is already sufficient, but the diagonal equations show how overdetermined the order-two constraints are.',
'The general normal magic-constant formula yields M₂=2(4+1)/2=5, but that is only a necessary target if such a square existed. A target sum does not establish existence. This distinction between a formal sum calculation and a feasible arrangement is a recurring theme in combinatorics: necessary conditions may fail to be sufficient.'
]),
('3.5 Symmetry, complements and equivalence',[
'Rotating a magic square by 90 degrees or reflecting it across a symmetry axis preserves the set of rows, columns and principal diagonals, up to reordering and reversal. These eight transformations form the dihedral symmetry group of the square. When counting distinct squares, one must decide whether rotations and reflections count as different. “Distinct” can mean different arrays in fixed orientation or different classes under these symmetries.',
'In a normal order-n square, each value x has a complement x′=n²+1−x. The two values sum to n²+1. For n=4 the complement pairs are (1,16), (2,15), …, (8,9), each totaling 17. A normal order-four construction often arranges these pairs so that opposing entries are complementary, but the existence of a pair sum 17 does not alone imply a magic square.',
'For the 139 date square, the complement rule just described is inapplicable because its entries are not 1 through 16. The number 17 appears as a cell value, but it is not a global complementary-pair target. A generalization may define a different pairing relative to a chosen total, yet it must be stated and proven for that arrangement rather than borrowed from the normal case.'
])]
for s in sections: section(*s)

chapter('4','Ramanujan’s 4 × 4 date square')
sections=[
('4.1 The displayed square and encoded date',[
'The case study uses the exact array in Figure 2. Reading the first row from left to right gives 22, 12, 18, 87. Interpreting the components as day 22, month 12, century 18 and year 87 yields 22 December 1887. The placement is memorable because the birth date appears directly in the square, while the remaining twelve entries are chosen so that the line constraints and other patterns hold.',
'The square is not normal. A normal order-four square uses 1 to 16 once each, but this array contains 87, 88 and 89 and several other values outside that interval. The word “magic” therefore refers to equal specified line sums, not to normality. This report calls it a date-encoded magic square or the Ramanujan date square to avoid implying that the entries are the conventional normal set.',
'The line target is 139. A direct check of the first row gives 22+12+18+87=139. The other three rows can be added similarly. The first column is 22+88+10+19=139. Rather than relying on a photograph or a caption, the next sections list all relevant arithmetic and derive why some additional groups also total 139.'
]),
('4.2 Line-by-line verification',[
'Let the rows be R₁ through R₄ and columns be C₁ through C₄. Their explicit values are R₁=(22,12,18,87), R₂=(88,17,9,25), R₃=(10,24,89,16), R₄=(19,86,23,11), and columns C₁=(22,88,10,19), C₂=(12,17,24,86), C₃=(18,9,89,23), C₄=(87,25,16,11). Naming these vectors prevents ambiguity about which entries are being summed.',
'The row calculations are 22+12+18+87=139; 88+17+9+25=139; 10+24+89+16=139; and 19+86+23+11=139. The column calculations are 22+88+10+19=139; 12+17+24+86=139; 18+9+89+23=139; and 87+25+16+11=139. Each is an independent check of a line, even though relationships among entries can shorten some proofs.',
'The main diagonal is 22+17+89+11=139. The other principal diagonal is 87+9+24+19=139. These ten line equations establish the standard order-four magic condition for this array. They do not establish normality, and they do not automatically establish every four-cell group sometimes highlighted in educational images.'
]),
('4.3 The central 2 × 2 and corner sums',[
'The central block consists of rows two and three and columns two and three: 17, 9, 24 and 89. Its sum is 17+9+24+89=139. The four corners are 22, 87, 19 and 11, with sum 22+87+19+11=139. Both results are easy to check directly and also have concise derivations from line equations.',
'The date square has a further useful local property: each of its four corner 2 × 2 sub-squares also totals 139. The upper-left block gives 22+12+88+17=139; upper-right gives 18+87+9+25=139; lower-left gives 10+24+19+86=139; and lower-right gives 89+16+23+11=139. Together with the central block, these are the five contiguous 2 × 2 blocks in a 4 × 4 array [5], [6].',
'For the central block, add the two middle row equations: (88+17+9+25)+(10+24+89+16)=278. The four outer-middle entries sum to (88+25)+(10+16)=139, so the central four must sum to 278−139=139. This proof depends on a second identity about those outer-middle entries, so a direct addition remains the most transparent verification unless that identity is separately established.',
'For the corners, add the top and bottom rows, obtaining 278. The non-corner entries in those rows are 12+18+86+23=139, leaving 139 for the corners. This derivation makes the relationship visible: when the top-plus-bottom total is twice the magic sum, and the four non-corner entries in those rows themselves total the magic sum, the corner set must also total the magic sum. Figure 4 marks these and other selected groups.'
],[(WORK/'fig04_groups.png',4,'Selected 139-sum groups in the date square','Figure 4 gives five separate views so each highlighted group can be read without color overlap: one row, one column, one principal diagonal, the four corners and the central 2 × 2 block. Each sums to 139.',6.1)]),
('4.4 Other four-cell groups and pair structure',[
'A 4 × 4 array contains many possible sets of four cells, so a colorful pattern must be translated into coordinates before its sum can be checked. One group visible in common teaching diagrams is the four cells (1,2), (1,3), (4,2), (4,3), with values 12,18,86,23. Their sum is 139. Another is (2,1), (2,4), (3,1), (3,4), with values 88,25,10,16, again 139. These are formed by pairing the middle cells of the top and bottom rows, and the outer cells of the two middle rows.',
'Some pair relations can be observed directly: 12+87=99, 18+88=106, and 17+89=106, for example; none creates a universal pair-sum rule of 17. Since the square is not normal, the normal complement identity x+(17−x)=17 has no reason to apply. In fact, the claim “pairs sum to 17” is a property of complementary values in the normal 1–16 set, not a defining property of the 139 square.',
'A rigorous description of a highlighted subgroup must state its four coordinates and calculate its sum. The visual grouping alone does not license a general theorem for all 2 × 2 blocks or all pairs. Several special groups total 139 because of this square’s construction, while arbitrary four-cell subsets need not.'
]),
('4.5 What the number 139 means',[
'The number 139 is the line-sum constant of the displayed date square. It is not derived from the normal formula n(n²+1)/2 because the entries are not 1 through 16. It can be derived from the total of all sixteen displayed entries: their sum is 556, and if each of the four rows has common total M, then 4M=556, giving M=139. Direct addition of any row confirms that target.',
'The number 139 is also prime, but primality is not required for a magic square. The square’s defining property is the equality of its specified line sums, not any special arithmetic property of the target itself. A prime magic constant does not force a square to be normal, unique, pandiagonal or balanced in every sub-block.',
'A useful student exercise is to ask which statements follow from the line-sum definition and which depend on the actual entries. Equal rows, columns and main diagonals are part of the definition. The corner and central-block equalities are additional properties verified for this arrangement. The birth-date encoding is a historical/biographical feature of the first row. Primality is a property of the integer 139. Keeping these categories separate prevents overgeneralisation.'
]),
('4.6 The number 1729: a separate connection',[
'The integer 1729 is associated with a well-known recollection by G. H. Hardy. Hardy later recounted that he visited Ramanujan in a taxi numbered 1729 and remarked that the number seemed dull. Ramanujan replied, in the recollection, that it was interesting because it is the smallest positive integer expressible as a sum of two positive cubes in two distinct ways: 1729=1³+12³=9³+10³ [1], [12]. The equality can be checked directly: 1+1728=1729 and 729+1000=1729.',
'This property is independent of the date square. The standard 4 × 4 date square shown in Figure 2 contains no entry 1729; its bottom row is 19, 86, 23, 11. Its bottom row sums to 139. Therefore, the statement that “1729 appears in the bottom row” is not true of this familiar square. If a different grid uses the digits 1, 7, 2 and 9 to encode a date or places 1729 in a special arrangement, it is a separate construction and must be identified explicitly.',
'The report discusses 1729 because it is central to Ramanujan’s public legacy and because the project brief links it to the square. The correct relationship is biographical and thematic: both are associated with Ramanujan’s mathematical memory. The cube identity must not be presented as a row-sum property of the date square.'
])]
for s in sections: section(*s)

chapter('5','Proofs of the principal properties')
sections=[
('5.1 The global sum and line target',[
'A useful proof strategy begins with the entire grid. Summing each of the four rows counts every entry exactly once. The entries total 22+12+18+87+88+17+9+25+10+24+89+16+19+86+23+11=556. If the common row total is M, then 4M=556, hence M=139. This argument proves that if all four rows are equal, their common value must be 139; it does not by itself prove that each row is equal.',
'The distinction between determining a possible target and verifying all constraints is important. One row with sum 139 and total grid sum 556 do not ensure that the other rows sum to 139: they could differ while preserving the grand total. All four row equations must still be checked, or they must be deduced from a construction with a proof.',
'For the normal case, the total 1+⋯+n² produces the general formula. For the non-normal date case, the total is calculated from its specific entries. The same conservation principle supports both analyses, but the input data differ. This is a reusable technique: add all line equations when each entry appears exactly once, then use independent constraints for the remaining structure.'
],{'equations':['Σᵢⱼ aᵢⱼ = 556 = 4 × 139']}),
('5.2 Proof of row and column totals',[
'The row proof is direct because the entries of each row are explicitly available. Define R₁=22+12+18+87, R₂=88+17+9+25, R₃=10+24+89+16 and R₄=19+86+23+11. Evaluating each expression gives 139. No appeal to visual symmetry is needed, and no missing condition is hidden in the calculation.',
'For the columns, define C₁=22+88+10+19, C₂=12+17+24+86, C₃=18+9+89+23, and C₄=87+25+16+11. Each equals 139. The column equations use the same entries in a different partition of the grid, so one should not assume they follow from the row equations in an arbitrary array. Their equality is an independent property of this arrangement.',
'A formal verification can record the vector of row sums [139,139,139,139] and column sums [139,139,139,139]. This is preferable to a single statement that “all lines work,” because it shows exactly which conditions were tested and provides a compact test oracle for a program.'
]),
('5.3 Proof of diagonal totals',[
'The principal diagonal from upper left to lower right contains a₁₁=22, a₂₂=17, a₃₃=89 and a₄₄=11. Their sum is 22+17+89+11=139. The opposite principal diagonal contains a₁₄=87, a₂₃=9, a₃₂=24 and a₄₁=19; its sum is 87+9+24+19=139.',
'In matrix indexing, the first diagonal uses cells (i,i) and the second uses (i,5−i), for i=1,2,3,4. Explicit indexing prevents common mistakes such as summing a broken diagonal or omitting one endpoint. In larger orders, a loop can generate these coordinates, but the mathematical definition remains the same.',
'The result is limited to the two principal diagonals. A panmagic square requires additional wraparound or broken-diagonal constraints, depending on convention. The date square’s two diagonal equalities do not prove that all broken diagonals sum to 139. Whenever a report uses the word diagonal, it should name the exact class of diagonals being discussed.'
]),
('5.4 Proof of the corner total',[
'The corners are the cells (1,1), (1,4), (4,1) and (4,4), containing 22,87,19,11. Direct addition yields 22+87+19+11=139. An identity gives a second check: the first and fourth rows together sum to 278. Their non-corner entries are 12+18+86+23=139. Subtracting these middle entries from 278 leaves 139 for the corners.',
'The direct proof is sufficient to establish the property for the displayed square. The derived proof illustrates a general technique: partition a known total into disjoint groups, then subtract a group whose sum is known. This approach is especially useful when a pattern in the cells suggests a subgroup total but the subgroup is not itself a row or column.',
'The corner property is not part of the standard definition of a magic square. A different order-four magic square may have the same line constant but a different corner total. Therefore, the correct statement is “the four corners of this square sum to 139,” not “the corners of every magic square equal the magic constant.”'
]),
('5.5 Proof of the central block total',[
'The central 2 × 2 block contains the four cells (2,2), (2,3), (3,2) and (3,3), namely 17,9,24,89. Direct addition gives 17+9+24+89=139. A complementary partition of the middle two rows provides another check: those rows together total 278, and their four outer entries 88,25,10,16 total 139; the remaining central entries therefore total 139.',
'The proof uses the actual values and the verified line sums. It does not imply that every central block in every magic square has the line target. In the normal order-four example in Figure 8, the central entries 10,11,6,7 also total 34, but that follows from its normal complement structure. The apparent parallel is instructive, yet the underlying number sets and arguments differ.',
'Students can test the claim by listing the exact coordinates before calculating. This guards against a frequent error in diagrams where colors or crops make cell boundaries unclear. A mathematical caption should communicate what is highlighted and what the sum is, while the text provides the arithmetic.'
]),
('5.6 Interpreting the pair relationships',[
'For a normal square with entries 1 through 16, pair each value x with 17−x. Every such complementary pair sums to 17. There are eight pairs: (1,16), (2,15), (3,14), (4,13), (5,12), (6,11), (7,10), and (8,9). The number 17 is n²+1 for n=4, so it is determined by the normal value set.',
'If an order-four normal square places two such complementary pairs on the same line, that line totals 34. Some constructions arrange complements in opposing cells; in a 4 × 4 square the four corners can be grouped into two complementary pairs, and the four central cells can also be paired, yielding 17+17=34. But not every pair in the square necessarily sums to 17; only complementary partners do. The arrangement matters.',
'Ramanujan’s date square uses 17 as one entry, but its values are not paired by n²+1. For example, the entry 17 does not have a designated partner 0 in the normal range. Thus the pair-sum statement belongs in the comparison with normal squares, not in a list of properties of the 139 date square. This careful separation is the report’s main correction of the project brief’s mixed claims.'
])]
for s in sections: section(*s)

chapter('6','Constructing magic squares')
sections=[
('6.1 Construction goals and constraints',[
'A construction method must satisfy two kinds of requirements. The value-set requirement specifies which numbers are permitted and whether repetition is allowed. The line requirement specifies which rows, columns and diagonals must have the common target. A normal construction must produce every integer 1 through n² exactly once, and the resulting row and column partitions must each sum to n(n²+1)/2.',
'Orders are commonly divided into odd, doubly-even and singly-even classes. Odd orders are 3,5,7,…; doubly-even orders are multiples of four; singly-even orders are even but not multiples of four. The classification matters because the geometry of the constraints changes with parity. A method for an odd order cannot simply be used unchanged for order six, and complement patterns that work for order four require adaptation at order six.',
'Figure 5 summarises a verification-oriented pipeline: define inputs, construct an array by the appropriate method, then independently check the output. Separation of construction and checking is good mathematical practice. If the same flawed assumption appears in both routines, a test may pass incorrectly; an independent verifier reduces this risk.'
],[(WORK/'fig08_framework.png',5,'Construction and verification framework','Figure 5 separates order selection, construction and independent verification so a correct-looking output is not accepted without checks.',6.2)]),
('6.2 Odd-order Siamese method',[
'The Siamese method constructs a normal magic square of odd order n. Begin by placing 1 in the middle cell of the top row. For each next integer, move one cell up and one cell right, wrapping around the edges. If the destination is already occupied, instead move one cell down from the position of the previous integer. Continue until n² is placed.',
'For order three, the procedure starts at row 1, column 2. The next tentative location for 2 is row 3, column 3 because the move wraps above the top edge. The next value moves up-right again. When the next destination is occupied, the downward rule creates a turn that preserves the placement pattern. Figure 6 illustrates the final 3 × 3 arrangement and the movement rules.',
'The method is deterministic once the starting cell and direction conventions are fixed. The resulting square has magic constant n(n²+1)/2. A proof can be developed by tracking the modular coordinates of each move and showing that the row, column and diagonal positions partition arithmetic progressions in a balanced way. The full proof is more involved than the recipe; an algorithmic description should not be mistaken for a proof of correctness.'
],[(WORK/'fig06_siamese.png',6,'Siamese construction for order three','Figure 6 shows the order-three output and states the wrap and collision rules that generate it.',6.0)]),
('6.3 Worked order-three construction',[
'For n=3, the target is M=3(9+1)/2=15. Applying the Siamese method gives the grid 8,1,6; 3,5,7; 4,9,2. Its rows total 15: 8+1+6, 3+5+7 and 4+9+2. Its columns total 15: 8+3+4, 1+5+9 and 6+7+2. The main diagonals are 8+5+2 and 6+5+4, each also 15.',
'Normality is checked separately. The entries are 1 through 9, with no repetition and no omission. The center entry is 5, the average of 1 through 9. This average is consistent with the global total but is not by itself sufficient to prove normality or the line conditions.',
'The example demonstrates a complete verification sequence: confirm dimensions, confirm the value multiset, calculate target, check rows, check columns, and check both principal diagonals. If any one stage fails, the arrangement is not a normal magic square under the report’s definition. This procedure scales directly to larger orders, even though manual arithmetic becomes less convenient.'
]),
('6.4 Doubly-even orders',[
'A doubly-even order is divisible by four, such as 4 or 8. One standard construction begins with the numbers 1 through n² written in natural order. Selected cells are retained, while the other cells are replaced by their complements n²+1−x. For order four, the pattern marks both main diagonals of each 4 × 4 block: positions with row and column residues equal modulo 4, and positions whose residues sum to 3 modulo 4.',
'The complement operation preserves the total of each paired original value and complement. Since x+(n²+1−x)=n²+1, a row or column containing an appropriate number of complement pairs reaches the target n(n²+1)/2. The pattern is designed so the selected and complemented positions are balanced in each required line. Figure 7 displays the resulting order-four construction.',
'A proper proof should track the count and sum of retained entries in each line, not rely solely on a visual X-pattern. For order eight the same 4 × 4 residue pattern repeats across blocks, and the construction’s balance extends to all rows, columns and main diagonals. More advanced variants can rearrange the pattern while retaining the complement principle.'
],[(WORK/'fig07_doubly_even.png',7,'Order-four complement pattern','Figure 7 shows the normal order-four square produced by replacing selected natural-order entries with 17 minus their original values.',4.5)]),
('6.5 Worked order-four complement construction',[
'Write the numbers 1 to 16 in row-major order. Complement the cells on the two diagonals of this 4 × 4 layout, replacing x by 17−x; retain all other cells. The result shown in Figure 8 is 16,2,3,13; 5,11,10,8; 9,7,6,12; 4,14,15,1. Every entry from 1 to 16 appears exactly once because complementing permutes the set.',
'The first row totals 16+3+2+13=34. The second is 5+10+11+8=34, the third 9+6+7+12=34, and the fourth 4+15+14+1=34. The columns and two principal diagonals also total 34. Each selected complementary pair sums to 17, and the construction places the pairs so every required line receives two pairs or an equivalent balanced combination.',
'This example provides the concrete setting for the user-requested properties “34” and “pairs summing to 17.” The square is a normal order-four example, not Ramanujan’s date square. Its central 2 × 2 values sum to 10+11+6+7=34; its corners sum to 16+13+4+1=34. These facts are explained by the complements: 10+7=17, 11+6=17, 16+1=17 and 13+4=17.'
],[(WORK/'fig03_normal.png',8,'A normal 4 × 4 square using 1 through 16','Figure 8 is a separate comparison square with normal magic constant 34; it is used to explain complementary pairs summing to 17.',4.5)]),
('6.6 Singly-even orders',[
'A singly-even order has the form n=4k+2, such as 6 or 10. Such orders are harder because they are even but do not admit the simple 4 × 4 complement tiling. One common approach divides the square into four equal quadrants, each initially based on an odd-order square. The quadrants receive offset ranges, then a prescribed set of entries is exchanged between upper and lower halves to repair row, column and diagonal totals.',
'For order six, the quadrant order is three. The four blocks use different offsets so that together they cover 1 through 36. The swap pattern has a central exception: an otherwise regular set of left-side columns is exchanged, with specific middle-row cells treated differently. A second exchange on the right side balances the remaining lines. Because details vary among named methods, an implementation must state its exact convention and test it across more than one order.',
'The singly-even algorithm is a productive example of why constructing and verifying should be independent. A one-cell swap error can preserve the set 1 through n² but break a row or diagonal. The report’s algorithm appendix gives pseudocode at a high level; it should be checked against a formal source before being used as a production implementation.'
]),
('6.7 Construction versus verification',[
'Construction answers “How can an arrangement be produced?” Verification answers “Does this particular arrangement satisfy the stated definition?” These are distinct questions. A construction can be correct in theory but incorrectly coded; a verifier can find the coding error if it independently calculates the properties. Conversely, an array can pass a verifier while being generated by an entirely different method.',
'A robust workflow first validates input order, then constructs the matrix, then checks shape and range, then checks uniqueness, followed by each row, column and principal diagonal. Additional claims such as corner sum, central block, complementary pairs and date encoding require their own tests. The checks should report which condition failed so a student can diagnose rather than merely reject the array.',
'For small orders, exhaustive manual checks are feasible. For larger orders, a short program reduces arithmetic errors, but the source code and expected results should be documented. A program that prints “magic” without exposing line sums is less useful for learning and harder to audit. Reproducibility means that another person can follow the same input, algorithm and checks to obtain the same conclusion.'
])]
for s in sections: section(*s)

chapter('7','Worked mathematical examples')
sections=[
('7.1 Normal order-three square',[
'The order-three example in Figure 3 uses all integers 1 through 9 once and has M=15. The total of the set is 45; dividing by three gives 15. The central entry is 5, and opposite cells sum to 10 in the familiar Lo Shu orientation. For instance, 8 and 2, 1 and 9, 6 and 4, and 3 and 7 are opposite pairs around the center.',
'The pair structure makes line verification economical. Each line through the center contains the center 5 and an opposite pair totaling 10, so it sums to 15. The remaining rows and columns can be checked directly. This reasoning explains why opposite pairs are useful in order three, but it is specific to this arrangement and should not be assumed of every non-normal square.',
'The example also demonstrates transformations: rotating or reflecting the array preserves its magic property. A student can list all orientations and see that the same numerical constraints hold. This is a simple introduction to symmetry groups and equivalence classes, themes that recur in enumeration research.'
]),
('7.2 A normal order-four square and complementary pairs',[
'The normal order-four example is 16,2,3,13; 5,11,10,8; 9,7,6,12; 4,14,15,1. It contains each integer 1 through 16 exactly once. The sum is 136, so each of four equal rows must total 34. Complementary pairs are determined by x′=17−x. The square places such pairs in positions that support equal sums.',
'The corners are 16,13,4,1. Pairing 16 with 1 and 13 with 4 gives 17+17=34. The central block is 11,10,7,6; pair 11 with 6 and 10 with 7 to obtain 34. This demonstrates the user-requested “corner sums” and “central 2 × 2 sum” for the 34 square. It does not transfer to Ramanujan’s 139 square simply because both are 4 × 4.',
'The square’s bottom row contains 4,15,14,1 and sums to 34. The number 1729 does not appear. Dürer’s famous square is another normal arrangement with sum 34 and a date 1514 in its bottom row; the displayed example here is chosen for transparent complementary-pair reasoning.'
]),
('7.3 Order-five constant and structural checks',[
'For order five, the normal constant is 5(25+1)/2=65. The total of 1 through 25 is 325, and 325/5=65. One standard odd-order method produces a square whose entries can then be checked using the Siamese algorithm. The constant can be known before the square is generated, which gives an independent oracle for verification.',
'When checking a 5 × 5 square, record five row totals, five column totals and two diagonal totals. Also verify that the flattened entry list equals the set {1,…,25}. It is not enough to check that each value lies in range: duplicates and omissions can cancel in the grand total. The multiset check and the line check address different failure classes.',
'A useful extension is to calculate the mean of each row. In a normal magic square, every row mean is 13 because 65/5=13. This mean is consistent with the global average of 1 through 25. It gives an intuitive interpretation of the constant but is not an additional defining property.'
]),
('7.4 Scaling and translation',[
'If every entry of a magic square A is multiplied by a constant k, then every line sum is multiplied by k. If a constant c is added to every entry in an order-n square, each line sum increases by nc because every required line contains n cells. Thus the transformed target is kM+nc for entries kaᵢⱼ+c. The transformation preserves equality of line sums, although it may change integrality, positivity or normality depending on k and c.',
'For example, adding 5 to every entry of the order-three Lo Shu makes every line sum 15+3×5=30. The resulting entries are 6 through 14, so it is a magic square but not normal under the 1-to-n² convention. Doubling a normal square doubles its line sum but creates gaps in the values, again destroying normality while retaining line equality.',
'This algebra explains how many non-normal examples arise from normal ones. It also clarifies why the Ramanujan date square’s high values do not prevent it from being magic. Normality is a stronger condition than equal line sums, and transformations can preserve the latter while changing the former.'
]),
('7.5 A date square built from a birth date',[
'The familiar date-square construction places a date’s components in the first row and chooses the remaining entries to achieve a common total. For Ramanujan, the first row 22,12,18,87 encodes day, month, century and year. The other twelve numbers shown in Figure 2 produce the target 139 and several additional sums. This is a specific constructed example rather than a universal recipe that maps every date to one unique square.',
'A date can admit many arrangements, and some may fail the desired constraints. One must specify the date convention, the representation of the year, whether repeated entries are allowed, what line family is required, and whether additional patterns are desired. If two digits or components coincide, the construction still requires explicit rules; the date alone does not define the remaining cells.',
'A student can design a new date square by solving a system of linear equations. Fix the first row values and target M. The remaining twelve cells must satisfy the other row, column and diagonal equations. There are more unknowns than equations, so additional constraints or choices are needed. Integer restrictions and uniqueness can turn the problem into an integer-programming or combinatorial search task.'
])]
for s in sections: section(*s)

chapter('8','Verification methodology and computational study')
sections=[
('8.1 Verification specification',[
'The verifier accepts an integer n, an n × n matrix A, and a specification describing normality and required line families. For a normal square, it checks that every entry is an integer in [1,n²] and that each value occurs exactly once. For a non-normal date square, it checks the stated entries and line target without imposing the normal value set. The specification must be explicit so the program does not apply the wrong target formula.',
'For the Ramanujan case, the expected target is 139, the dimensions are four by four, and the required lines are four rows, four columns and two principal diagonals. Extra checks include the four corners, the central 2 × 2 block, selected cross-pattern groups, and the first-row date encoding. The 1729 cube identity is a separate arithmetic test and should not be included as a grid property.',
'A test report should provide calculated sums, not just a pass/fail flag. If a row sum is incorrect, the output should identify its index and computed total. This design helps students understand the error and supports independent review. The test cases in Appendix C distinguish normal and non-normal input paths.'
]),
('8.2 Permutation and range checks',[
'For a normal square, flatten the matrix into a list of n² values. A range check verifies min(A)≥1 and max(A)≤n². A uniqueness check compares the sorted list with [1,2,…,n²]. These checks jointly prove that no value is missing, repeated or out of range. Counting entries alone is insufficient because a duplicate can replace a missing value while preserving the list length.',
'For the date square, the value set is intentionally not 1 through 16. The verifier should instead compare the input with the specified 4 × 4 array or validate only the declared conditions. Reusing the normal verifier would incorrectly reject the date square, even though it satisfies its line-sum definition. This is a software specification issue and a mathematical classification issue at once.',
'The verifier should reject malformed input: wrong dimensions, non-integer values when integers are required, missing cells or extra rows. If arbitrary rational or real entries are permitted in a separate study, floating-point tolerance must be designed carefully; exact integer addition is preferable for the present examples.'
]),
('8.3 Line-sum algorithm',[
'A direct algorithm computes each row by summing its n entries, each column by summing its n entries, then the two principal diagonals. It compares every result with a target M. For a normal square, M can be calculated from n(n²+1)/2. For the Ramanujan date square, M is a declared expected value of 139 or is derived from the given entries and checked consistently.',
'The computation requires O(n²) additions because the matrix contains n² values and the required lines contain 2n²+2 entries when counted naively. The storage requirement is O(n²) if the matrix is stored, or O(n) additional space if sums are accumulated while reading. For small educational orders, performance is negligible; clarity and correctness are more important than optimisation.',
'A line list is a convenient representation for testing: rows, columns and diagonals are each converted to lists of coordinates. A single function computes their sums. This reduces duplicated logic and makes it easier to add corner or central-block checks without changing the core definition. Appendix B presents language-neutral pseudocode.'
]),
('8.4 Subgroup and property checks',[
'Additional properties must be implemented as separate coordinate sets. The corner set is {(1,1),(1,4),(4,1),(4,4)}; the central block is {(2,2),(2,3),(3,2),(3,3)} under one-based indexing. The selected top-bottom group and middle outer group should each be listed explicitly. A function then sums exactly those coordinates and compares the result with 139.',
'For a normal order-four square, complementary pairs are checked by confirming x+y=17 for each selected pair. A complementary-pair checker should not infer pairs from proximity unless the construction defines that relationship. The date square’s entries should not be passed to this checker because the normal complement condition does not apply.',
'The test suite should include negative examples: a square with a row altered; a normal square with one duplicate and one omission; a square with rows correct but one diagonal wrong; and a date square mistakenly checked against 34. Negative tests show that the verifier detects common errors instead of merely accepting the expected input.'
]),
('8.5 Test data and expected results',[
'The principal positive cases are the Lo Shu square (order three, M=15), the normal order-four complement square (M=34), and Ramanujan’s date square (M=139, non-normal). The expected row, column and diagonal sums are recorded independently. A good test uses arrays transcribed from a source and then checks the transcription before using it as a fixture.',
'The normal order-four case specifically checks complementary pairs, corners and center. The date square checks the same geometric groups against 139, plus its encoded first row. This paired test demonstrates that two 4 × 4 arrays can share a shape but differ in value set, target and interpretation. It also catches an implementation that assumes every order-four square must total 34.',
'Appendix C gives expected outcomes rather than claiming execution in a particular software environment. If this report is used as a software project submission, the student should run the test program, record the language and version, attach actual console output, and sign off only cases that were executed. That distinction protects the validity of the test evidence.'
]),
('8.6 Complexity, reliability and limits',[
'The direct verifier is linear in the number of cells, O(n²), for an n × n array. It is exact for integer inputs and straightforward to audit. The complexity is not the limiting factor for ordinary magic-square sizes; input mistakes, indexing errors and incorrect assumptions about normality are more realistic risks.',
'Reliability improves when construction and verification are independent, test cases include invalid arrays, and outputs expose individual sums. Property-based tests can generate transformed squares or random perturbations and ensure that expected properties change as predicted. For example, adding one to a single cell should break at least some line equalities; rotating a valid square should preserve them.',
'A verifier cannot prove historical attribution, explain why a construction was chosen, or establish that all possible squares have been enumerated. It confirms a finite set of arithmetic conditions for a particular matrix. General theorems require mathematical proofs; historical claims require source criticism. The report treats these as complementary forms of evidence.'
])]
for s in sections: section(*s)

chapter('9','Generalizations and related research')
sections=[
('9.1 Semi-magic and panmagic squares',[
'A semi-magic square has equal row and column sums but may not require its principal diagonals to match. A panmagic or pandiagonal square imposes additional conditions on broken diagonals that wrap around the edges; terminology and exact conventions vary. These classes are stricter or different variants of the basic square, and a report should specify the line family rather than use labels loosely.',
'The date square in this project is checked for both principal diagonals, but no claim is made that all broken diagonals total 139. To test pandiagonality in an order-four array, define each wrapped diagonal by modular coordinates and calculate all required sums. This is a good extension exercise because a square can pass the standard test while failing the stronger one.',
'Related variants illustrate how a small change to the definition creates new construction and classification problems. They also show why a colorful pattern may be more restrictive than the square’s standard magic property. Claims should be matched to the exact definition in the source.'
]),
('9.2 Associative and bordered squares',[
'An associative square has equal sums for entries in cells opposite each other through the center, often with a common pair total. In a normal order-n square, the natural complement value n²+1 makes such a property possible. The normal order-four example’s opposite pairs sum to 17. This condition is distinct from requiring every line to sum to 34, though the same construction can satisfy both.',
'A bordered square is built by arranging an outer border around a smaller inner square while preserving compatible line totals. Border constructions can be useful for inductive methods: solve a smaller problem, add a new layer of values, and correct the sums along affected lines. The details depend on order and value set.',
'The Ramanujan date square also has special groups, including corners and center, but should not automatically be called associative under a normal complement definition. A new property label requires a precise definition. If a generalised date-square family is proposed, it should state how the target and opposite-cell sums depend on the date components.'
]),
('9.3 Non-normal and composite entries',[
'Non-normal squares permit values outside 1 through n², and may allow repeated entries depending on the convention. The date square is non-normal but has distinct entries. A composite square may be built from smaller squares or from algebraic transformations. Such examples widen the space of possible targets and can encode information in selected rows or cells.',
'If repeated entries are allowed, line equality alone can become trivial: filling every cell with the same number creates a constant-sum array. For meaningful classification, researchers therefore impose additional conditions such as distinctness, positivity, specified bounds or a fixed multiset. The definition must say which of these applies.',
'The date-encoded square demonstrates a purposeful non-normal construction. Its first row is fixed by the date and the remaining entries satisfy a system of linear constraints. The design is memorable because numerical conditions and personal data coexist, not because the entries form the standard normal set.'
]),
('9.4 Enumeration and symmetry classes',[
'Counting magic squares is a combinatorial problem. For normal order four, one must assign sixteen values to sixteen cells while satisfying ten line equations and avoiding duplicates. Rotations and reflections generate equivalent arrays unless orientation is being counted. Additional restrictions, such as a fixed first row or specified complement property, produce different counts.',
'Enumeration studies typically use mathematical reductions, backtracking, integer programming or exhaustive search with symmetry-breaking constraints. A count is meaningful only when the object definition and equivalence convention are stated. The result “number of order-four squares” is ambiguous unless one specifies normality, value set, diagonal requirements and whether symmetric copies are identified [11].',
'Ramanujan’s date square is one particular non-normal arrangement, not a representative of all normal 4 × 4 squares. Counting normal squares does not directly count date-encoded squares. The latter problem has a different value set and often fixed first-row data, so it needs a separately stated model.'
]),
('9.5 Higher-dimensional magic arrays',[
'The idea of equal sums can be extended from a two-dimensional square to cubes and higher-dimensional arrays. In a magic cube, one may require lines in several directions, planes or space diagonals to share a target. Definitions are not uniform: some versions constrain only axis-parallel lines, while others impose plane or diagonal conditions. A precise specification is essential before construction or enumeration.',
'The normal value set for an n × n × n array would contain n³ values, but the appropriate line families and target depend on the chosen definition. The simple square formula cannot be transferred blindly because a line sum counts a different number of entries and the imposed constraints differ.',
'Higher-dimensional variants show that magic squares are part of a broader study of structured arrays and combinatorial designs. They offer possible project extensions, but a student report should choose a tractable definition and develop it fully rather than mention a high-dimensional object without explaining its constraints.'
]),
('9.6 Research directions',[
'Several manageable research extensions follow from this study. One can enumerate all normal order-four squares under a clearly stated symmetry convention; compare constructions by number of complementary pairs; search for date-encoded squares with a chosen first row; or test whether a given arrangement is pandiagonal. Each extension begins by defining the object precisely and selecting a proof or computational method.',
'A computational search for date squares could treat twelve remaining entries as integer variables subject to linear equations and optional bounds. The solver must avoid trivial or repetitive solutions if those are not desired. One can then classify solutions under rotations and reflections that preserve the fixed date encoding, noting that fixing the first row removes many symmetries.',
'A research-oriented report should include an algorithm, correctness argument, computational environment, test cases and limitations. New results should be checked independently and compared with published work. This project provides the definitions and verification framework needed to pursue such an extension without overstating what the present analysis has established.'
])]
for s in sections: section(*s)

chapter('10','Applications, pedagogy and interpretation')
sections=[
('10.1 Classroom use and mathematical reasoning',[
'Magic squares support classroom work on addition, multiplication, parity, algebraic expressions, patterns and proof. A teacher can ask learners to calculate a row, notice a repeated total, and then explain why the total is forced by the number set. The transition from checking examples to proving the constant formula models mathematical reasoning at an accessible scale.',
'The Ramanujan date square invites students to separate an aesthetic observation from a verified claim. Learners can mark rows, columns, diagonals, corners and the center in different colors, but must list the exact cells and compute their sums. A follow-up comparison with the normal 34 square clarifies the role of the value set. A final discussion of 1729 reinforces source and category distinctions.',
'Activities should avoid presenting a recipe as a proof. After constructing an odd-order square, students can verify it and then investigate why the method works. For a short lesson, the report’s order-three example is manageable; for an extended project, the complement construction and date-square system offer more room for argument.'
]),
('10.2 Recreational mathematics and puzzles',[
'A magic-square puzzle can be posed as a completion problem: some cells are known, the target is supplied, and the solver must infer missing entries. The puzzle can emphasize arithmetic fluency, constraint propagation or combinatorial search. A well-designed task should state whether numbers may repeat, whether all values are bounded, and whether diagonals count.',
'The Ramanujan square can be used as a guided discovery exercise. Hide selected entries, provide the line target 139, and ask students to use intersecting row and column constraints. However, the target and known values may not uniquely determine the remaining cells. The teacher should explain whether the task seeks one solution or all solutions.',
'Digital versions can animate construction, show running line totals or reveal violated constraints. These features should represent the mathematics faithfully: a red line indicates a failed condition under the current partial grid, while an incomplete row may not yet be judged. Interaction adds value when it supports reasoning, not merely when it decorates the board.'
]),
('10.3 Art, culture and historical interpretation',[
'Magic squares have appeared in manuscripts, decorative traditions, puzzles and artworks. Their geometric regularity and numerical invariants make them visually compelling. Dürer’s order-four square in Melencolia I is a well-known European example; the Lo Shu has an enduring role in Chinese cultural traditions. Such histories are diverse and should not be collapsed into one universal origin narrative [7]–[10].',
'Ramanujan’s date square has a personal dimension: the upper row encodes his birth date. That feature can make mathematical biography tangible, but it can also lead to sensational claims. The report treats the square’s arithmetic as demonstrable and its attribution according to the quality of available historical sources.',
'The user-supplied handmade display photograph is included in Figure 9 as an example of a physical teaching model. It illustrates how a movable or revealable panel can invite prediction of the target sum. The arithmetic printed beside a handmade model should still be checked; the report uses the cleanly transcribed grid, not handwritten annotations, as its proof source.'
],[(Path(r'C:\Users\LENOVO\OneDrive\Pictures\ramanujans magic square images\maxresdefault.jpg'),9,'User-supplied handmade model of the 139 square','Figure 9 shows a physical classroom display based on the date square. It is included as an instructional artefact; the verified numerical source for calculations remains Figure 2.',5.7)]),
('10.4 Digital and computational demonstrations',[
'A digital demonstration can expose each line sum as a computed value and allow the user to select which group to inspect. For a normal order-n square, it can show M=n(n²+1)/2 and the complete range check. For the date square, the interface should identify the target as 139 and label the array as non-normal. A single interface should not silently impose one specification on both cases.',
'An animation of the Siamese method can show the up-right move, edge wrapping and occupied-cell rule. A complement-method animation can distinguish original entries from their complements. At each step, the user can pause and inspect how values are placed. Such demonstrations make algorithms observable while preserving the need for a mathematical explanation.',
'A useful educational tool should offer transparent feedback and a reset path. It should report the exact row, column or diagonal that fails, distinguish incomplete data from an invalid completed square, and preserve reproducible examples. Visual design should serve explanation; it should not imply that a line sum is correct merely because colors align.'
])]
for s in sections: section(*s)

chapter('11','Limitations and critical discussion')
sections=[
('11.1 Attribution and source limitations',[
'The report uses the conventional title “Ramanujan’s magic square” while qualifying the specific historical attribution as a widely circulated association. Biographical sources securely document Ramanujan’s life and date of birth, while the path by which the exact 139 array was first recorded is less fully established in accessible source material. A definitive claim about manuscript provenance would require direct examination of original notebooks or authoritative archival scholarship.',
'The reference PDF supplied by the user is an academic report on an unrelated project. It serves as a structural model for title pages, chapter hierarchy, technical discussion, results, conclusion and references; it is not a source for the mathematics in this report. The four supplied images are also secondary illustrations and are not treated as historical proof.',
'Citation quality varies in popular mathematics webpages. This report prioritises scholarly books, mathematical publications and reputable educational sources. Where a fact is repeated across several secondary sources but a primary record is not cited, the wording remains qualified. This is especially important for anecdotes and origin stories.'
]),
('11.2 What the familiar square does not prove',[
'The existence of one 4 × 4 magic square does not prove that every order admits a normal magic square, although general construction theorems address that broader question. It does not prove uniqueness, panmagic behaviour, a universal corner rule or that every 2 × 2 subarray has the same total. Those are separate claims requiring their own definitions and proofs.',
'Likewise, the number 34 is not the line constant of every 4 × 4 magic square. It is the constant for a normal order-four square using entries 1 through 16. A non-normal square may have another target, as the 139 example demonstrates. The formula n(n²+1)/2 depends on the normal value set; omitting this assumption creates a false generalisation.',
'The number 1729 does not appear in the familiar date grid and is not a property of its bottom row. It is related to Ramanujan through the Hardy recollection and the two cube decompositions. The report treats these as separate mathematical contexts.'
]),
('11.3 Limits of finite examples',[
'A hand-checked 4 × 4 square illustrates definitions but cannot establish a theorem for all n. Several verified examples may suggest a pattern, yet a proof must show why the pattern follows from assumptions. The normal magic-constant derivation is general because it uses the arithmetic-series sum and common line condition, not because many examples happened to agree.',
'A finite search can prove a statement about a bounded finite set if the search is exhaustive and correctly specified. It cannot establish an unbounded theorem without an argument that covers all cases. The same distinction applies to software testing: passing tests supplies evidence about tested inputs, not absolute correctness for every possible matrix.',
'The report’s examples and algorithms are intended as a foundation for further study. Any general classification, count or claim of uniqueness should be supported by a formal source or a complete proof. Where the text presents an example, it labels it as an example rather than a universal pattern.'
]),
('11.4 Reproducibility and notation',[
'Reproducibility can be weakened by inconsistent indexing, transposed arrays or ambiguous diagonal names. This report uses one-based row and column labels in tables, defines the principal diagonals, and prints entries consistently row by row. The pseudocode appendix uses zero-based indexing explicitly. A reader implementing the checks should verify that the convention is applied consistently.',
'The date components use the conventional grouping DD-MM-CC-YY for day, month, century and year. Different date formats may place components differently or represent the year with two digits. Such choices should be stated in any new date-square construction. The value 87 is interpreted as the final two digits of 1887 only because the accompanying century component is 18.',
'A reproducible computational report should include software language/version, source code, input arrays, output sums and exact test results. This document provides test specifications but does not claim a code execution. A student adapting it as a programming project should attach their own run logs.'
]),
('11.5 Ethical use of historical images',[
'Images can make the history more immediate, but they also carry copyright and attribution concerns. The user supplied four images with the brief. This report uses one supplied physical-model image for explanatory context and labels it as user-provided. It redraws mathematical grids and diagrams rather than reproducing low-resolution images that contain ambiguous text or unclear cell highlights.',
'Before public distribution or formal publication, the student should verify permission requirements for any image. A source link or uploader name is not always equivalent to a reuse licence. If permissions are uncertain, replace the photograph with a newly created diagram or seek permission from the rights holder.',
'The report avoids using a portrait without a verified source and licence. Instead, Figure 1 is a newly drawn timeline based on biographical dates cited in the references. This satisfies the historical visual requirement without implying that an unverified portrait is authentic or freely reusable.'
])]
for s in sections: section(*s)

chapter('12','Results and discussion')
sections=[
('12.1 Summary of verified results',[
'The displayed date square was verified to have four row sums of 139, four column sums of 139 and two principal diagonal sums of 139. Its four corners sum to 139, as does its central 2 × 2 block. Two additional four-cell patterns highlighted in educational diagrams also total 139 when their coordinates are stated explicitly. The entire entry sum is 556, consistent with four lines of 139.',
'The normal order-four comparison square uses 1 through 16, has total 136 and target 34. Complementary values x and 17−x sum to 17. In the example shown, the corner group and central block each split into two complementary pairs and therefore total 34. The results confirm that both targets are valid under different value-set assumptions.',
'The 1729 identity is 1³+12³=9³+10³=1729. It is a separate number-theoretic fact and does not describe the date square’s entries or bottom-row total. The order-two normal case is impossible because equal rows and columns force repeated values.'
],{'tables':[(['Object','Value set','Target','Status'],[['Ramanujan date square','Specified date-based integers','139','Magic, non-normal'],['Normal order-four example','1 through 16 once','34','Normal magic square'],['Lo Shu example','1 through 9 once','15','Normal magic square'],['1729 cube identity','Positive cubes','1729','Separate number-theory result']],[1.5,1.8,1.0,2.0])]}),
('12.2 Comparison of the two order-four squares',[
'The most important comparison is not merely that both arrays have four rows and four columns. The date square’s first row encodes a date and its entries sum to 556 in total, giving line constant 139. The normal square’s entries are exactly 1 through 16 and total 136, giving line constant 34. Each square satisfies the equal-line definition; only one satisfies the normality condition.',
'The complementary-pair total 17 follows from the normal range because 1+16=2+15=⋯=17. It does not follow from order four alone. The central and corner totals are additional arrangement properties. In the specific normal example they equal 34 through complementary pairing; in the date square they equal 139 through its own construction and arithmetic.',
'This comparison resolves the apparent conflict in the project brief. A report can discuss both 34 and 139, and both 17 and 1729, provided each is assigned to the correct object. Precision makes the subject more interesting because it reveals how different constraints create different kinds of order.'
],{'tables':[(['Feature','Date square','Normal order-four example'],[['First row','22, 12, 18, 87','16, 2, 3, 13'],['Entry set','Date-based, non-normal','1–16 exactly once'],['Magic constant','139','34'],['Complement pair rule','No universal 17 rule','x and 17−x sum to 17'],['Bottom row','19, 86, 23, 11','4, 14, 15, 1'],['1729 present?','No','No']],[1.55,2.2,2.3])]}),
('12.3 Answers to the research questions',[
'The normal order-four constant is 34 because the sum of 1 through 16 is 136 and four equal rows divide that total into 34 each. Ramanujan’s date square has constant 139 because its distinct, date-related entries total 556. The constants differ because the underlying sets differ; the formula’s normality assumption is essential.',
'Rows, columns, principal diagonals, corners and the central block of the 139 array were verified by explicit addition. The construction families differ by parity: the Siamese method handles odd orders, a complement pattern handles doubly-even orders, and a quadrant-and-swap method handles singly-even orders. The date encoding provides a memorable historical connection but does not uniquely determine a square without further constraints.',
'The pair-sum 17 is a normal order-four complement property. The number 1729 is independently notable as a sum of two cubes in two ways. Neither is a bottom-row property of the familiar date square. The answers follow from definitions and calculations rather than from visual resemblance or repeated unsourced claims.'
]),
('12.4 Implications for teaching and further work',[
'The paired examples offer a lesson in model specification: the order of the square does not determine its value set, and the value set affects the expected constant. Instructors can ask students to identify assumptions before applying formulas. A short proof of the normal constant, followed by the 139 case, gives a natural opportunity to compare general reasoning with a concrete non-normal example.',
'The verification ledger and test plan can be extended into a small software exercise. Students may implement construction, input validation, line reporting and subgroup checks. The code should distinguish normal squares from arbitrary magic squares and should never use a single hard-coded target for all order-four arrays.',
'Further work could search for date-encoded variants, classify solutions under symmetry, explore panmagic conditions, or reconstruct source provenance for the familiar square. Each extension has a clear mathematical or historical question and can be scoped as a separate project.'
])]
for s in sections: section(*s)

chapter('13','Conclusion and future scope')
sections=[
('13.1 Conclusion',[
'This project has examined magic squares through the 4 × 4 arrangement associated with Srinivasa Ramanujan. It has shown that the famous date square encodes 22 December 1887 in its first row and has common row, column and principal-diagonal total 139. Its corners and central block also total 139, and selected additional four-cell groups can be verified by listing their coordinates and adding the entries.',
'The report has also established why 34 and 17 belong to a different but related setting. A normal order-four square uses 1 through 16, has total 136 and magic constant 34. Complementary pairs sum to 17 because each pair is x and 17−x. The central block and corner total 34 in the worked normal example. These results are not properties of the date square merely because it is also 4 × 4.',
'Finally, 1729 was treated as a separate Ramanujan-related number with identity 1³+12³=9³+10³. It is absent from the bottom row of the familiar date square. Distinguishing these facts strengthens, rather than diminishes, the mathematical story. It shows that correct definitions and source-aware explanation are essential to a rigorous project.'
]),
('13.2 Recommendations for extension',[
'A future study may implement each construction family and compare the generated squares with independent verification routines. The extension should include unit tests for order three, four, six and eight, plus invalid cases. For singly-even orders, the exact algorithm and source should be documented because swap conventions are particularly easy to misapply.',
'A second extension may formulate date-square completion as an integer constraint problem. Fix the top row, select a target, impose row, column and diagonal equations, and then add optional conditions such as distinctness, bounds or subgroup totals. The study should report whether solutions are unique and how equivalence under symmetry is handled.',
'A historical extension may trace the earliest reliable printed or manuscript appearance of the familiar 139 square. This work would require primary-source access and careful archival citation. Until such research is completed, the conventional attribution should remain qualified. Any final academic submission should also replace personal placeholders, verify local formatting rules and attach the student’s own test execution evidence if required.'
])]
for s in sections: section(*s)

# References: numbered citation style; full bibliographic data and URLs where useful.
page(); doc.add_heading('REFERENCES',0)
refs=[
'[1] G. H. Hardy, Ramanujan: Twelve Lectures on Subjects Suggested by His Life and Work, 3rd ed. New York: Chelsea Publishing, 1978 (originally published 1940).',
'[2] R. Kanigel, The Man Who Knew Infinity: A Life of the Genius Ramanujan. New York: Charles Scribner’s Sons, 1991.',
'[3] B. C. Berndt and R. A. Rankin, Ramanujan: Letters and Commentary. Providence, RI: American Mathematical Society, 1995.',
'[4] B. C. Berndt, Ramanujan’s Notebooks, Part I. New York: Springer-Verlag, 1985.',
'[5] C. K. Ghosh, “Fun With Magic Squares,” Dream 2047, vol. 18, no. 8, May 2016, pp. 32–33, Department of Science and Technology, Government of India.',
'[6] Community Mathematics Centre, “A Magic Square in Ramanujan’s Honour,” At Right Angles, vol. 4, no. 3, Nov. 2015. Available: https://publications.azimpremjiuniversity.edu.in/3104/',
'[7] W. S. Andrews, Magic Squares and Cubes. Chicago and London: Open Court Publishing Company, 1917.',
'[8] J. R. Hendricks, Magic Squares to Tesseracts by Computer. Self-published, 1998.',
'[9] D. M. Brown, “The Magic Squares of Manuel Moschopoulos,” Convergence, Mathematical Association of America, 2012. Available: https://old.maa.org/press/periodicals/convergence/the-magic-squares-of-manuel-moschopoulos-magic-squares-before-moschopoulos',
'[10] A. Eves, “The Fascination of Magic Squares,” Royal Institution, Primary Mathematics Masterclasses, online article. Available: https://www.rigb.org/explore-science/explore/blog/fascination-magic-squares',
'[11] M. R. McKay and C. J. Radcliffe, “Enumeration of 4 × 4 Magic Squares,” arXiv:0907.3188, 2009. Available: https://arxiv.org/abs/0907.3188',
'[12] K. Ono, “Ramanujan, Taxicabs, Birthdates, Zipcodes, and Twists,” expository lecture notes, University of Virginia. Available: https://uva.theopenscholar.com/files/ken-ono/files/023_8.pdf',
'[13] “Srinivasa Ramanujan,” MacTutor History of Mathematics Archive, University of St Andrews. Available: https://mathshistory.st-andrews.ac.uk/Biographies/Ramanujan/',
'[14] “Hardy-Ramanujan Number,” Wolfram MathWorld. Available: https://mathworld.wolfram.com/Hardy-RamanujanNumber.html',
'[15] User-provided document: WhatsApp Image 2026-10-24 at 10.50.23 PM.pdf, academic project-report model, 53 scanned pages. Consulted for report structure and register only; unrelated subject content not used.',
'[16] User-provided image: maxresdefault.jpg, handmade 4 × 4 date-square teaching display, supplied with the project brief. Reproduced in Figure 9 for explanatory context.',
'[17] User-provided images: OIP.webp, OIP (1).webp and sddefault.jpg, supplied with the project brief. Reviewed for the square’s teaching presentation; not reproduced because the report redraws the groups and entry grid for legibility.',
]
for r in refs: p(r)
p('Access dates for online references should be added if required by the department’s citation policy. Book editions and publication details should be checked against the copies consulted by the student before final submission.')

# Appendices, each with independently useful material rather than repeated prose.
page(); doc.add_heading('APPENDIX A  ARITHMETIC VERIFICATION LEDGER',0)
p('The ledger below records the exact groups used in the report. All coordinates are one-based. The row and column vectors correspond to Figure 2.')
table(['Check','Entries or coordinates','Calculation','Result'],[
('Rows R1–R4','(1,1)…(1,4), etc.','22+12+18+87; 88+17+9+25; 10+24+89+16; 19+86+23+11','139 each'),
('Columns C1–C4','(1,1)…(4,1), etc.','22+88+10+19; 12+17+24+86; 18+9+89+23; 87+25+16+11','139 each'),
('Main diagonal','(1,1),(2,2),(3,3),(4,4)','22+17+89+11','139'),
('Other diagonal','(1,4),(2,3),(3,2),(4,1)','87+9+24+19','139'),
('Corners','(1,1),(1,4),(4,1),(4,4)','22+87+19+11','139'),
('Central block','(2,2),(2,3),(3,2),(3,3)','17+9+24+89','139'),
('Top/bottom inner group','(1,2),(1,3),(4,2),(4,3)','12+18+86+23','139'),
('Middle outer group','(2,1),(2,4),(3,1),(3,4)','88+25+10+16','139')],[1.2,1.8,2.6,.9],8.3)
p('Grand-total cross-check: 556 = 4 × 139. This confirms consistency between the entry sum and the four row totals, but the individual line checks above remain necessary.')

page(); doc.add_heading('APPENDIX B  CONSTRUCTION AND VERIFICATION PSEUDOCODE',0)
doc.add_heading('B.1 Normal magic constant',2)
p('Input: integer order n ≥ 1. Compute S = n²(n²+1)/2, the total of 1 through n². Return M = S/n = n(n²+1)/2. This target calculation assumes normal entries.')
doc.add_heading('B.2 Generic line verifier',2)
for line in ['1. Confirm the matrix has n rows and n columns.','2. If normality is required, verify that the sorted entries equal 1,2,…,n².','3. Choose target M from the normal formula or from the explicit non-normal specification.','4. Sum each row and compare with M. Record every result.','5. Sum each column and compare with M.','6. Sum cells (i,i) and (i,n+1−i) for i=1,…,n.','7. Evaluate separately declared corner, centre or special-group checks.','8. Return a structured report identifying each passed or failed condition.']:
    p(line)
doc.add_heading('B.3 Siamese method outline',2)
p('Set the current cell to the middle column of the top row. For value v from 1 through n², place v. Let the tentative next cell be one row up and one column right, with indices reduced modulo n. If it is occupied, move one row down from the current cell; otherwise move to the tentative cell. Continue. The method is intended for odd n. The output must still be checked independently.')
doc.add_heading('B.4 Complement method outline for order four',2)
p('Create the row-major grid 1 through 16. For cell (r,c), with zero-based indices, replace value x by 17−x when r mod 4 equals c mod 4 or when (r mod 4)+(c mod 4)=3; otherwise retain x. This yields Figure 8. The order-eight extension uses the corresponding repeated 4 × 4 residue pattern. Verify rows, columns, diagonals and the entry multiset after construction.')

page(); doc.add_heading('APPENDIX C  TEST CASES AND EXPECTED OUTCOMES',0)
table(['ID','Input / condition','Expected result','Reason'],[
('T01','Lo Shu order 3','Pass; M=15','Normal, all required lines agree'),
('T02','Normal order-four Figure 8','Pass; M=34','Entries 1–16 once; line sums 34'),
('T03','Ramanujan date square','Pass as non-normal; M=139','Specified grid and ten line checks'),
('T04','Date square checked against M=34','Fail specification','Wrong target/value-set assumption'),
('T05','Duplicate one normal entry; omit another','Fail normality','Multiset differs from 1…n²'),
('T06','Change one cell in a valid square','Fail at least one line','Perturbation changes affected sums'),
('T07','Wrong row count','Reject input','Dimensions do not match order'),
('T08','Correct rows but wrong diagonal','Fail diagonal check','Rows alone are insufficient'),
('T09','Rotate valid square by 90°','Pass same line definition','Rotation preserves required line family'),
('T10','Check 1729 in date-square cells','Not applicable; absent','Cube identity is separate from the grid')],[.55,2.0,2.0,2.2],8.8)
p('Execution record for a software submission: language/version [complete]; operating system [complete]; test date [complete]; source-code location [complete]; actual run output [attach]. The expected outcomes above are specifications, not a claim that a particular program was executed.')

page(); doc.add_heading('APPENDIX D  GLOSSARY',0)
table(['Term','Definition'],[
('Array order','The number n of rows and columns in an n × n square.'),('Complementary pair','Two values whose sum is n²+1 in a normal order-n square.'),('Diagonal','A specified line through the array; this report’s standard diagonals join opposite corners.'),('Magic constant','The common sum required for the defined line family.'),('Magic square','A square array with equal specified line sums; this report requires rows, columns and both principal diagonals.'),('Normal','Using 1 through n² exactly once.'),('Order','Number of rows (equal to number of columns).'),('Pandiagonal','A square whose required broken/torus diagonals also share the target, under a stated convention.'),('Singly-even','An even order congruent to 2 modulo 4.'),('Doubly-even','An order divisible by 4.'),('Taxicab number','The smallest positive integer representable as a sum of two positive cubes in a specified number of distinct ways; 1729 is the first nontrivial case.'),('Verification','Checking a specific array against an explicit set of mathematical conditions.')],[1.35,4.8],9.3)

page(); doc.add_heading('APPENDIX E  SOURCE AND FIGURE NOTES',0)
p('Figures 2 through 8 were generated specifically for this report from the values and methods stated in the text. They are explanatory diagrams, not facsimiles of historical manuscripts.')
p('Figure 1 is a newly drawn timeline based on the cited biographical sources. It is selective and does not imply a complete chronology.')
p('Figure 9 reproduces the user-provided maxresdefault.jpg image of a handmade educational model. Its handwritten or printed annotations are not relied upon as arithmetic evidence. The grid used in proofs is transcribed and recalculated independently in Figure 2.')
p('The user-supplied reference PDF guided the academic structure and register. It was not used as a source for mathematical or historical statements about Ramanujan.')

# Heading properties, widow control, and document metadata.
for para in doc.paragraphs:
    para.paragraph_format.widow_control=True
doc.core_properties.title='Ramanujan’s Magic Square: Historical Context, Mathematical Structure, Construction and Verification'
doc.core_properties.subject='Academic project report on Ramanujan’s date square and magic-square theory'
doc.core_properties.author='[Student Name]'
doc.core_properties.keywords='Ramanujan, magic square, 139, 34, 1729, construction, verification'
doc.save(OUT)
print(f'Wrote {OUT}')



