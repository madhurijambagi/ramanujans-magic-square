from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path(r"D:\ramanujans-magic-square\output\reports\ramanujans_magic_square_folder_structure.png")
OUT.parent.mkdir(parents=True, exist_ok=True)
W, H = 2400, 1580
im = Image.new("RGB", (W, H), "#fbfaf7")
d = ImageDraw.Draw(im)
font_path = r"C:\Windows\Fonts\arial.ttf"
bold_path = r"C:\Windows\Fonts\arialbd.ttf"
def font(size, bold=False):
    try:
        return ImageFont.truetype(bold_path if bold else font_path, size)
    except OSError:
        return ImageFont.load_default()
ink, line, gold, pale, muted = "#292c34", "#535966", "#e6ad59", "#fff2dc", "#667085"
def rounded_box(box, fill, outline=line, radius=13, width=3):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
def center_text(box, text, fnt, fill=ink):
    x1,y1,x2,y2=box
    bb=d.textbbox((0,0),text,font=fnt); tw,th=bb[2]-bb[0],bb[3]-bb[1]
    d.text(((x1+x2-tw)/2,(y1+y2-th)/2-bb[1]),text,font=fnt,fill=fill)
d.text((120,56),"PROJECT DIRECTORY STRUCTURE",font=font(36,True),fill=ink)
d.text((120,108),"Ramanujan's Magic Square | Active Flask application and supporting files",font=font(23),fill=muted)
root=(840,190,1560,278)
rounded_box(root,"#e5a64c",outline="#3d414a",radius=14,width=4)
center_text(root,"ramanujans-magic-square/",font(31,True))
cols=[
 ("Flask backend",["app.py","chatbot_rules.py","chatbot_i18n.py"]),
 ("public/",["HTML pages (index, game, daily, dashboard, profile, admin, etc.)","css/style.css","js/api.js","js/companion.js","js/magicSquare.js","js/theme.js"]),
 ("knowledge/",["magic-square-guide.md"]),
 ("data/",["data.sqlite"]),
 ("Deployment & setup",["requirements.txt",".env.example","Dockerfile","render.yaml","README.md"]),
 ("src/ (legacy)",["db.js","magicSquare.js","achievements.js","mailer.js","middleware/auth.js","routes/*.js"])
]
margin,gap=90,30
cw=(W-2*margin-gap*(len(cols)-1))//len(cols)
top,cat_h,item_h,item_gap=425,66,66,20
root_center=(root[0]+root[2])//2
d.line((root_center,root[3],root_center,340),fill=line,width=4)
centers=[margin+i*(cw+gap)+cw//2 for i in range(len(cols))]
d.line((centers[0],340,centers[-1],340),fill=line,width=4)
for i,(label,items) in enumerate(cols):
 x=margin+i*(cw+gap); cx=x+cw//2
 d.line((cx,340,cx,top),fill=line,width=4)
 cbox=(x,top,x+cw,top+cat_h)
 rounded_box(cbox,gold,radius=10,width=3)
 center_text(cbox,label,font(23,True))
 y=top+cat_h+29
 for item in items:
  fnt=font(18); maxw=cw-24; words=item.split(); lines=[]; cur=""
  for word in words:
   test=(cur+" "+word).strip()
   if d.textbbox((0,0),test,font=fnt)[2] <= maxw: cur=test
   else:
    if cur: lines.append(cur)
    cur=word
  if cur: lines.append(cur)
  h=max(item_h,len(lines)*25+24)
  d.line((cx,y-29,cx,y),fill=line,width=3)
  box=(x,y,x+cw,y+h); rounded_box(box,pale,outline="#7a6a54",radius=9,width=2)
  yy=y+(h-len(lines)*25)//2-2
  for ln in lines:
   bb=d.textbbox((0,0),ln,font=fnt); tw=bb[2]-bb[0]
   d.text((x+(cw-tw)/2,yy-bb[1]),ln,font=fnt,fill=ink); yy+=25
  y+=h+item_gap
note_y=1410
d.line((120,note_y-26,W-120,note_y-26),fill="#d8d4cc",width=2)
d.text((120,note_y),"Note: app.py is the active server entry point. The Node.js files under src/ are retained as a legacy implementation.",font=font(20),fill=muted)
d.text((120,note_y+38),"Runtime database file shown for structure reference; do not replace it when deploying code updates.",font=font(20),fill=muted)
im.save(OUT,"PNG",optimize=True)
print(OUT)
print(im.size)
