"""Check the built site against SPEC.md. Run from the repository root:

    python scripts/check_site.py

It builds the site as the deploy workflow does (hugo --gc --minify) into a
temporary folder and checks that:

- every address in mockups/current-urls.txt still exists (except the junk
  under /public/), as a page or a redirect, and redirects go where the spec
  says: /archives/ to the home page, retired page numbers to their list;
- no note's title appears on its page, tile, feed item or search entry,
  unless those words are in the note itself;
- every picture has a width, a height and an alt text;
- the main feeds hold exactly the notes.

Exits with 1 and lists the problems if anything fails.
"""
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
URLS = ROOT / "mockups" / "current-urls.txt"
SITE = "https://xekri-mlatus.github.io"


def notes():
    """(title, Markdown text, slug) of every note."""
    for path in sorted((ROOT / "content" / "notes").glob("**/*.md")):
        if path.name == "_index.md":
            continue
        _, fm, body = path.read_text(encoding="utf-8").split("---\n", 2)
        meta = yaml.safe_load(fm)
        yield str(meta["title"]), body, meta["slug"]


def refresh_target(text):
    m = re.search(r'http-equiv="?refresh"?\s+content="0; url=([^"]+)"', text)
    return m.group(1) if m else None


def main():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        build = subprocess.run(["hugo", "--gc", "--minify", "-d", tmp], cwd=ROOT,
                               capture_output=True, text=True, encoding="utf-8")
        if build.returncode or re.search(r"\b(WARN|ERROR)\b", build.stdout + build.stderr):
            problems.append("hugo reported problems:\n" + build.stdout + build.stderr)
        if build.returncode:
            return report(problems)

        # 1. Every current address still exists; redirects go where they should.
        checked = 0
        for url in URLS.read_text(encoding="utf-8").splitlines():
            if not url or url.startswith("#") or url.startswith("/public/"):
                continue
            checked += 1
            file = out / (url.lstrip("/") + ("index.html" if url.endswith("/") else ""))
            if not file.exists():
                problems.append(f"missing: {url}")
                continue
            if file.suffix != ".html":
                continue
            target = refresh_target(file.read_text(encoding="utf-8"))
            if url == "/archives/":
                if target != SITE + "/":
                    problems.append(f"/archives/ should redirect to the home page, goes to {target}")
            elif target:
                # A retired page number goes to its list's first page.
                m = re.fullmatch(r"(.*/)page/\d+/", url)
                if not m or target != SITE + m.group(1):
                    problems.append(f"{url} redirects to {target}")

        # 2. No note's title anywhere, unless its words are in the note itself.
        # Titles can only leak through the theme's templates, so each note is
        # checked where those put it: its page, its tile, its feed item and its
        # search entry. (Searching every file would trip over titles that are
        # ordinary words, like "Скоро", in other notes.)
        def flat(s):
            return html.unescape(html.unescape(s)).lower()
        tiles = {}
        for f in [out / "index.html", *out.glob("page/*/index.html")]:
            for url, tile in re.findall(r'<article class="?card tile"? data-url="?([^" >]+)"?>(.*?)</article>',
                                        f.read_text(encoding="utf-8"), re.S):
                tiles[url] = flat(tile)
        feed = {link: flat(item) for item, link in re.findall(
            r"(<item>.*?<link>([^<]+)</link>.*?</item>)", (out / "index.xml").read_text(encoding="utf-8"), re.S)}
        index = {e["url"]: json.dumps(e, ensure_ascii=False).lower()
                 for e in json.loads((out / "index.json").read_text(encoding="utf-8"))}
        for title, body, slug in notes():
            t = title.lower()
            if t in body.lower():
                continue
            url = f"/notes/{slug}/"
            places = {
                "its page": flat((out / url.lstrip("/") / "index.html").read_text(encoding="utf-8")),
                "its tile": tiles.get(url, ""),
                "its feed item": feed.get(SITE + url, ""),
                "its search entry": index.get(url, ""),
            }
            hits = [where for where, text in places.items() if t in text]
            if hits:
                problems.append(f'title "{title}" shows in {", ".join(hits)}')
            missing = [where for where, text in places.items() if not text]
            if missing:
                problems.append(f"{url} has no {', '.join(missing)}")

        # 3. Pictures have a width, a height and an alt text.
        for f in out.rglob("*.html"):
            for img in re.findall(r"<img\b[^>]*>", f.read_text(encoding="utf-8")):
                missing = [a for a in ("width", "height", "alt") if not re.search(rf"\s{a}\b", img)]
                if missing:
                    problems.append(f"{f.relative_to(out)}: picture without {', '.join(missing)}: {img[:120]}")

        # 4. The main feeds hold exactly the notes.
        count = sum(1 for _ in notes())
        for feed in ("index.xml", "notes/index.xml"):
            items = re.findall(r"<item>.*?<link>([^<]+)</link>", (out / feed).read_text(encoding="utf-8"), re.S)
            if len(items) != count or any("/notes/" not in link for link in items):
                problems.append(f"/{feed} has {len(items)} items, expected the {count} notes")

        print(f"Checked {checked} addresses, {count} notes' titles, every picture and the feeds.")
    return report(problems)


def report(problems):
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(" -", p)
        return 1
    print("All checks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
