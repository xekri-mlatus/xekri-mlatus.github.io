"""Store an artifact's Google Fonts with the artifact. Run from the repository root:

    python scripts/localize_fonts.py

Artifacts (content/artifacts/<name>/) are pages made elsewhere, and they
usually load their fonts from Google Fonts. The site loads nothing from other
sites, so for every artifact page that links to fonts.googleapis.com this
script downloads the fonts into the artifact's fonts/ folder and replaces the
links with @font-face rules pointing at those files. Only the Latin and
Cyrillic character sets are kept; other characters fall back to the page's
other fonts. Pages without such links are left alone, so it's safe to rerun.
"""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "content" / "artifacts"
KEEP = {"latin", "latin-ext", "cyrillic", "cyrillic-ext"}
# Google sends woff2 files only to browsers it recognises.
AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

STYLESHEET = re.compile(r'<link\b[^>]*href="(https://fonts\.googleapis\.com/css2?\?[^"]+)"[^>]*>\s*', re.I)
PRECONNECT = re.compile(r'<link\b[^>]*rel="preconnect"[^>]*href="https://fonts\.(googleapis|gstatic)\.com"[^>]*>\s*', re.I)
FACE = re.compile(r"/\* ([\w-]+) \*/\s*(@font-face\s*\{.*?\})", re.S)


def fetch(url):
    req = urllib.request.Request(url.replace("&amp;", "&"), headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def localize(page):
    text = page.read_text(encoding="utf-8")
    sheets = STYLESHEET.findall(text)
    if not sheets:
        return False
    fonts = page.parent / "fonts"
    fonts.mkdir(exist_ok=True)
    faces, saved = [], {}
    for sheet in sheets:
        for subset, face in FACE.findall(fetch(sheet).decode("utf-8")):
            if subset not in KEEP:
                continue
            family = re.search(r"font-family:\s*'([^']+)'", face).group(1)
            style = re.search(r"font-style:\s*(\w+)", face).group(1)
            url = re.search(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", face).group(1)
            # A variable font serves several weights from one file; static
            # fonts get a file per weight.
            if url not in saved:
                name = f"{slug(family)}-{style}-{subset}.woff2"
                if name in saved.values():
                    weight = re.search(r"font-weight:\s*(\w+)", face).group(1)
                    name = f"{slug(family)}-{style}-{weight}-{subset}.woff2"
                (fonts / name).write_bytes(fetch(url))
                saved[url] = name
            faces.append(face.replace(url, f"fonts/{saved[url]}"))
    style = ("<style>\n/* Fonts from Google Fonts, stored with the page by scripts/localize_fonts.py. */\n"
             + "\n".join(faces) + "\n</style>\n")
    text = PRECONNECT.sub("", text)
    text = STYLESHEET.sub(lambda m, done=[]: "" if done else (done.append(1) or style), text)
    page.write_text(text, encoding="utf-8", newline="\n")
    print(f"{page.relative_to(ROOT)}: {len(saved)} font files, {len(faces)} faces")
    return True


def main():
    pages = sorted(p for p in ARTIFACTS.glob("*/*.html"))
    changed = sum(localize(p) for p in pages)
    print(f"{changed} of {len(pages)} artifact pages changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
