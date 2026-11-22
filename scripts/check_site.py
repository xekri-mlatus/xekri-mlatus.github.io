"""Check the built site against SPEC.md. Run from the repository root:

    python scripts/check_site.py

It builds the site as the deploy workflow does (hugo --gc --minify) into a
temporary folder and checks that:

- every address in mockups/current-urls.txt still exists (except the junk
  under /public/), as a page or a redirect, and redirects go where the spec
  says: /archives/ to the home page, retired page numbers to their list;
- notes have no titles (nothing would show them), and every note has its
  page, its tile, its feed item and its search entry;
- every picture has a width, a height and an alt text;
- the main feeds and the search index hold exactly the notes;
- every artifact has its page with the bar back to the site, loads nothing
  from another site, and every file it loads is there;
- every `continues:` names another, older note, and the two notes link to
  each other on their pages and tiles (SPEC.md, "Threads");
- the site's icon is there, and every page (artifacts too) links it.

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


def notes_meta():
    """(front matter, Markdown text) of every note."""
    for path in sorted((ROOT / "content" / "notes").glob("**/*.md")):
        if path.name == "_index.md":
            continue
        _, fm, body = path.read_text(encoding="utf-8").split("---\n", 2)
        yield yaml.safe_load(fm), body


def threads():
    """{slug: the slugs of every note in its thread}, for notes in threads."""
    prev = {m["slug"]: m["continues"] for m, _ in notes_meta() if m.get("continues")}
    groups = {}
    for slug in {*prev, *prev.values()}:
        first = slug
        for _ in range(1000):  # a loop of notes is reported below, not followed forever
            if first not in prev:
                break
            first = prev[first]
        groups.setdefault(first, set()).add(slug)
    return {slug: group for group in groups.values() for slug in group}


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

        # 2. Notes have no titles: the site never shows them, and a note is named
        # by the start of its text instead. Every note is in each place the
        # theme puts it: its page, its tile, its feed item and its search entry.
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
        for meta, _ in notes_meta():
            slug = meta["slug"]
            if "title" in meta:
                problems.append(f"/notes/{slug}/ has a title in its front matter (notes have none)")
            url = f"/notes/{slug}/"
            places = {
                "its page": flat((out / url.lstrip("/") / "index.html").read_text(encoding="utf-8")),
                "its tile": tiles.get(url, ""),
                "its feed item": feed.get(SITE + url, ""),
                "its search entry": index.get(url, ""),
            }
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
        count = sum(1 for _ in notes_meta())
        for feed in ("index.xml", "notes/index.xml"):
            items = re.findall(r"<item>.*?<link>([^<]+)</link>", (out / feed).read_text(encoding="utf-8"), re.S)
            if len(items) != count or any("/notes/" not in link for link in items):
                problems.append(f"/{feed} has {len(items)} items, expected the {count} notes")

        entries = json.loads((out / "index.json").read_text(encoding="utf-8"))
        if len(entries) != count or any(not e["url"].startswith("/notes/") for e in entries):
            problems.append(f"/index.json has {len(entries)} entries, expected the {count} notes")

        # 5. Artifacts: served with the bar back to the site, and self-contained.
        artifacts = sorted(p.parent.name for p in (ROOT / "content" / "artifacts").glob("*/index.md"))
        for name in artifacts:
            page = out / "artifacts" / name / "index.html"
            if not page.exists():
                problems.append(f"missing: /artifacts/{name}/")
                continue
            text = page.read_text(encoding="utf-8")
            if "mlatus-bar" not in text:
                problems.append(f"/artifacts/{name}/ has no bar back to the site")
            refs = re.findall(r"""url\(\s*["']?([^"')\s]+)""", text)
            for tag in re.findall(r"<(?:script|link|img|iframe|source|video|audio|embed)\b[^>]*>", text):
                # The canonical link and the site's visit counter (added by the
                # theme, see SPEC.md) are the only addresses elsewhere allowed.
                if not re.search(r"rel=\"?canonical|data-goatcounter=", tag):
                    refs += re.findall(r"""\b(?:src|href)=["']?([^"'\s>]+)""", tag)
            refs += [f"@import {m}" for m in re.findall(r"@import\s+([^;]+)", text)]
            for ref in refs:
                if re.match(r"(https?:)?//|@import", ref):
                    problems.append(f"/artifacts/{name}/ loads from another site: {ref[:100]}")
                elif not ref.startswith(("#", "data:", "/")) and not (page.parent / ref.split("#")[0].split("?")[0]).exists():
                    problems.append(f"/artifacts/{name}/ loads a missing file: {ref}")

        # 6. Threads: each continuation names another, older note, and the two
        # link to each other on their pages and tiles.
        metas = {m["slug"]: m for m, _ in notes_meta()}
        for slug, m in metas.items():
            prev = m.get("continues")
            if not prev:
                continue
            if prev not in metas or prev == slug:
                problems.append(f"/notes/{slug}/ continues {prev!r}, which is no other note")
                continue
            if str(metas[prev]["date"]) >= str(m["date"]):
                problems.append(f"/notes/{slug}/ continues /notes/{prev}/, which isn't older")
            a, b = f"/notes/{slug}/", f"/notes/{prev}/"
            for here, there, kind in ((a, b, "prev"), (b, a, "next")):
                page = (out / here.lstrip("/") / "index.html").read_text(encoding="utf-8")
                if not re.search(rf'<a class="?quote {kind}"? href="?{re.escape(there)}"?', page):
                    problems.append(f"{here} doesn't quote {there}")
                if not re.search(r'id="?thread"?', page):
                    problems.append(f"{here} has no whole-thread view")
                if here in tiles and f'href={there}' not in tiles[here].replace('"', ""):
                    problems.append(f"{here}'s tile doesn't link to {there}")

        # 7. The icon: its files at the root, linked from every page that isn't a redirect.
        icons = ("favicon.ico", "favicon.svg", "apple-touch-icon.png")
        for name in icons:
            if not (out / name).exists():
                problems.append(f"missing: /{name} (run python scripts/make_favicons.py)")
        for f in out.rglob("*.html"):
            text = f.read_text(encoding="utf-8")
            if refresh_target(text):
                continue
            if not re.search(r'<link rel="?icon"? href="?/favicon\.svg', text):
                problems.append(f"{f.relative_to(out).as_posix()} doesn't link the site's icon")

        print(f"Checked {checked} addresses, {count} notes, every picture, the feeds, "
              f"{len(artifacts)} artifact(s), {len(threads())} notes in threads and the icon.")
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
    # Hugo's messages and the notes' text aren't all in the Windows console's code page.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
