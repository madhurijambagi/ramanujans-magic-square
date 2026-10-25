from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
folder = Path(r'D:\ramanujans-magic-square\tmp\pdfs\reference')
files = sorted(folder.glob('page-*.jpg'), key=lambda p: int(p.stem.split('-')[-1]))
w, h, cols, rows = 340, 460, 3, 3
for start in range(0, len(files), cols * rows):
    canvas = Image.new('RGB', (w * cols, h * rows), 'white')
    draw = ImageDraw.Draw(canvas)
    for offset, path in enumerate(files[start:start + cols * rows]):
        idx = start + offset
        thumb = Image.open(path).convert('RGB')
        x, y = (offset % cols) * w, (offset // cols) * h
        canvas.paste(ImageOps.contain(thumb, (w - 10, h - 28)), (x + 5, y + 24))
        draw.text((x + 7, y + 5), f'PDF page {idx + 1}', fill='black')
    canvas.save(folder / f'labeled-{start // (cols * rows) + 1}.jpg', quality=88)
