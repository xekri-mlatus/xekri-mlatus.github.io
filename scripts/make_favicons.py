"""Draw the site's icon for browser tabs, search results and phone home
screens: a purple-to-pink circle with a white "M" (the header's avatar until
2026-11-22, when the header got a picture; the icon stayed). Run from the
repository root after changing it:

    python scripts/make_favicons.py

It writes into static/ (served at the site's root):

- favicon.svg: the icon for current browsers, sharp at any size;
- favicon.ico: 16, 32 and 48 px, for older browsers and anything that asks
  for /favicon.ico (Google's results among them);
- apple-touch-icon.png: 180 px, for Safari and phone home screens, on the
  site's background colour (iOS fills transparent corners with black).

The "M" is drawn as lines, not typed in a font, so it looks the same
everywhere. The theme links the files from every page (_partials/icons.html).
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static"

# The circle's colours (the old "M" avatar's) and the light background (--bg).
FROM, TO = (0x7B, 0x6C, 0xF6), (0xE4, 0x6F, 0xA7)
BACKGROUND = (0xF3, 0xF2, 0xEE)

# On a 64 x 64 grid: the circle fills it; the M's strokes run through these
# points, this thick.
M_POINTS = [(19, 45), (19, 21), (32, 36), (45, 21), (45, 45)]
M_WIDTH = 7


def svg():
    points = " ".join(f"{x},{y}" for x, y in M_POINTS)
    hex_ = lambda c: "#%02x%02x%02x" % c
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{hex_(FROM)}"/><stop offset="1" stop-color="{hex_(TO)}"/>
</linearGradient></defs>
<circle cx="32" cy="32" r="32" fill="url(#g)"/>
<polyline points="{points}" fill="none" stroke="#fff" stroke-width="{M_WIDTH}" stroke-linejoin="round"/>
</svg>
"""


def icon(size, background=None):
    """The icon as a size x size image, drawn 8 times larger and scaled down
    so the edges are smooth."""
    big = size * 8
    s = big / 64
    # Diagonal gradient, top left to bottom right, as in the CSS (135deg).
    ramp = [tuple(round(a + (b - a) * i / 510) for a, b in zip(FROM, TO)) for i in range(511)]
    gradient = Image.new("RGB", (big, big))
    gradient.putdata([ramp[(x + y) * 255 // big] for y in range(big) for x in range(big)])
    ImageDraw.Draw(gradient).line([(x * s, y * s) for x, y in M_POINTS], fill="white",
                                  width=round(M_WIDTH * s), joint="curve")
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
    out = Image.new("RGBA", (big, big), (*background, 255) if background else (0, 0, 0, 0))
    out.paste(gradient, (0, 0), mask)
    return out.resize((size, size), Image.LANCZOS)


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "favicon.svg").write_text(svg(), encoding="utf-8")
    icon(48).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)],
                  append_images=[icon(16), icon(32)])  # each size drawn, not shrunk
    icon(180, BACKGROUND).convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
    for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png"):
        print(f"static/{name}: {(OUT / name).stat().st_size} bytes")


if __name__ == "__main__":
    main()
