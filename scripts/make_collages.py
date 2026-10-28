"""Make a collage cover for every note that has more than one image.

For each note folder in content/notes with two or more images in its text,
this writes collage.jpg next to them (up to six pictures; with more, the
last tile shows "+N") and points the note's cover at it, so note lists show
all of the pictures at once. Note pages are unaffected: they show the
images themselves.

Run it from the repository root after adding or changing a note's images:

    python scripts/make_collages.py

Needs Pillow (python -m pip install pillow).
"""

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

NOTES = Path('content/notes')
COLLAGE = 'collage.jpg'
WIDTH, HEIGHT = 1280, 720  # 16:9, like the video thumbnails
GAP = 6
BACKGROUND = (34, 34, 36)
MAX_TILES = 6
FONTS = ['C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/arialbd.ttf', 'DejaVuSans-Bold.ttf']


def row(y, h, count):
    """Boxes for `count` tiles of equal width in one row."""
    w = (WIDTH - GAP * (count - 1)) / count
    return [(round(i * (w + GAP)), y, round(w), h) for i in range(count)]


def layout(count):
    """Tile boxes (x, y, width, height) for 2 to MAX_TILES pictures."""
    half_w, half_h = (WIDTH - GAP) // 2, (HEIGHT - GAP) // 2
    if count == 2:
        return row(0, HEIGHT, 2)
    if count == 3:  # one large on the left, two stacked on the right
        x = half_w + GAP
        return [(0, 0, half_w, HEIGHT), (x, 0, half_w, half_h), (x, half_h + GAP, half_w, half_h)]
    top = {4: 2, 5: 2, 6: 3}[count]
    return row(0, half_h, top) + row(half_h + GAP, half_h, count - top)


def tile(path, size):
    """The image cropped to fill `size`, keeping its top (memes have captions there)."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    if img.mode != 'RGB':
        img = img.convert('RGBA')
        flat = Image.new('RGB', img.size, (255, 255, 255))
        flat.paste(img, mask=img.getchannel('A'))
        img = flat
    return ImageOps.fit(img, size, Image.Resampling.LANCZOS, centering=(0.5, 0.0))


def font(size):
    for name in FONTS:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def make_collage(images, out):
    shown = images[:MAX_TILES]
    canvas = Image.new('RGB', (WIDTH, HEIGHT), BACKGROUND)
    boxes = layout(len(shown))
    for path, (x, y, w, h) in zip(shown, boxes):
        canvas.paste(tile(path, (w, h)), (x, y))
    hidden = len(images) - len(shown)
    if hidden:
        x, y, w, h = boxes[-1]
        shade = Image.new('RGBA', (w, h), (0, 0, 0, 150))
        canvas.paste(shade, (x, y), shade)
        draw = ImageDraw.Draw(canvas)
        draw.text((x + w / 2, y + h / 2), f'+{hidden}', fill='white', font=font(h // 3), anchor='mm')
    canvas.save(out, quality=85, optimize=True)


def note_images(note_dir, body):
    """Local images in the order the note's text shows them."""
    names = []
    for name in re.findall(r'!\[[^\]]*\]\(([^)\s]+)\)', body):
        if '://' not in name and name not in names and (note_dir / name).is_file():
            names.append(name)
    return [note_dir / n for n in names]


def collage_alt(front, body, count):
    """Alt text in the note's language: Russian if its title or text (not image captions) has Cyrillic."""
    title = re.search(r'^title: (.*)$', front, re.M).group(1)
    text = title + re.sub(r'!\[[^\]]*\]\([^)]*\)', '', body)
    if re.search('[а-яё]', text, re.I):
        return f'Коллаж из {count} картинок заметки'
    return f'Collage of the {count} images in this note'


def set_cover(index, front, body, count):
    cover_image = re.compile(r'^(cover:\n(?:  .*\n)*?  image: ).*$', re.M)
    if not cover_image.search(front + '\n'):
        print(f'  skipped {index.parent.name}: no cover in front matter')
        return False
    front = cover_image.sub(lambda m: m.group(1) + COLLAGE, front + '\n', count=1)[:-1]
    alt = collage_alt(front, body, count)
    front = re.sub(r'^(cover:\n(?:  .*\n)*?  alt: ).*$', lambda m: m.group(1) + f'"{alt}"',
                   front + '\n', count=1, flags=re.M)[:-1]
    index.write_text(front + '\n---\n' + body, encoding='utf-8', newline='\n')
    return True


def main():
    made = 0
    for index in sorted(NOTES.glob('*/index.md')):
        front, sep, body = index.read_text(encoding='utf-8').partition('\n---\n')
        images = note_images(index.parent, body)
        if not sep or len(images) < 2:
            continue
        make_collage(images, index.parent / COLLAGE)
        if set_cover(index, front, body, len(images)):
            made += 1
            print(f'{index.parent.name}: {len(images)} images')
    print(f'{made} collages')


if __name__ == '__main__':
    main()
