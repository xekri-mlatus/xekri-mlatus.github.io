"""Post notes to the Telegram channel, whole, as the site shows them.

Run by the deploy workflow after the site is published:

    python scripts/post_to_telegram.py --since <commit>      # notes added since a commit
    python scripts/post_to_telegram.py --notes slug1 slug2   # these notes

It reads each note from the built site (`public/` by default, made by `hugo`),
so shortcodes, image sizes and links are already resolved, and turns the
note's text into Telegram's HTML: bold, italics, links, quotes, lists. Links
to the site become full addresses. The hashtags follow the text, and old
notes keep their "old note" disclaimer.

How a note is sent:

- no pictures: one message (more if the text is longer than Telegram allows);
- pictures: a photo, or albums of up to 10, with the text as the caption when
  it fits (1024 characters); otherwise the text follows as its own message.
  The caption goes above the pictures when the note's text comes before them.

Needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL (`@name` or a `-100…` ID) in
the environment; `--channel` overrides the second. `--dry-run` prints what
would be sent and needs neither.
"""

import argparse
import html
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "content" / "notes"

TEXT_LIMIT = 4096     # characters in a message
CAPTION_LIMIT = 1024  # characters in a photo or album caption
ALBUM_LIMIT = 10      # pictures in an album

YOUTUBE = re.compile(r"youtube(?:-nocookie)?\.com/embed/([\w-]+)")


# ---------------------------------------------------------------- the notes

def front_matter(path):
    """The slug and date of a note file (no YAML library needed for these two)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    fields = {}
    for line in (m.group(1) if m else "").splitlines():
        km = re.match(r"(slug|date):\s*(.+?)\s*$", line)
        if km:
            fields[km.group(1)] = km.group(2).strip("'\"")
    return fields


def note_key(path):
    """'2026-11-22-name' for content/notes/2026-11-22-name(.md|/index.md), else None."""
    parts = Path(path).as_posix().split("/")
    if parts[:2] != ["content", "notes"]:
        return None
    if len(parts) == 3 and parts[2].endswith(".md") and parts[2] != "_index.md":
        return parts[2][:-3]
    if len(parts) == 4 and parts[3] == "index.md":
        return parts[2]
    return None


def all_notes():
    """{slug: (date, file)} for every note in the working tree."""
    notes = {}
    for path in NOTES.rglob("*.md"):
        key = note_key(path.relative_to(ROOT))
        if key:
            fm = front_matter(path)
            slug = fm.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", key)
            notes[slug] = (fm.get("date", ""), path)
    return notes


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", check=True).stdout


def added_since(rev):
    """Slugs of the notes that exist now but didn't at `rev`."""
    def keys(r):
        return {k for k in map(note_key, git("ls-tree", "-r", "--name-only", r,
                                             "--", "content/notes").splitlines()) if k}
    try:
        git("cat-file", "-e", rev + "^{commit}")
    except subprocess.CalledProcessError:
        print(f"Commit {rev} isn't known (a new branch or a force push?); posting nothing.")
        return []
    new = keys("HEAD") - keys(rev)
    by_key = {}
    for slug, (_, path) in all_notes().items():
        by_key[note_key(path.relative_to(ROOT))] = slug
    return [by_key[k] for k in sorted(new) if k in by_key]


# ------------------------------------------------- a built page -> Telegram

class Note(HTMLParser):
    """Reads a note's built page: its text as Telegram HTML blocks, its
    pictures, videos, hashtags and old-note disclaimer."""

    INLINE = {"strong": "b", "b": "b", "em": "i", "i": "i", "s": "s",
              "del": "s", "strike": "s", "u": "u", "ins": "u", "code": "code"}
    BLOCK = {"p", "div", "figure", "figcaption", "details", "summary", "table",
             "tr", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote",
             "ul", "ol", "li", "hr"}

    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.where = None        # "body", "tags", "old" while inside one of them
        self.depth = 0           # element depth inside that part
        self.lang = "en"
        self.blocks = []         # top-level blocks of text, Telegram HTML
        self.buf = ""
        self.images = []         # (address in the built site, whether text comes before it)
        self.videos = []         # YouTube addresses
        self.tags = []
        self.old = {}            # lang -> disclaimer text
        self.old_lang = None
        self.lists = []          # [kind, counter] for each open ul/ol
        self.pre = 0
        self.links = []          # whether each open <a> was kept as a link
        self.seen_body = False
        self.done = False        # past the note's own article (the thread view repeats it)

    # -- output helpers
    def add(self, s):
        self.buf += s

    def text(self, s):
        if not self.pre:
            s = re.sub(r"\s+", " ", s)
            visible = re.sub(r"(<[^>]+>)+$", "", self.buf)
            if not visible or visible[-1] in " \n":
                s = s.lstrip(" ")
        self.add(html.escape(s, quote=False))

    def br(self, n):
        """End the current line (n=1) or paragraph (n=2) inside a block."""
        if re.search(r"(^|\n)\u2003*(•|\d+\.) $", self.buf):
            return  # right after a list item's bullet: its text goes on the same line
        self.buf = self.buf.rstrip(" ")
        if not re.sub(r"<[^>]+>", "", self.buf).strip():
            return
        have = len(self.buf) - len(self.buf.rstrip("\n"))
        self.buf += "\n" * max(0, n - have)

    def flush(self):
        block = self.buf.strip()
        block = re.sub(r"<(b|i|s|u|code)>\s*</\1>", "", block)
        block = re.sub(r"[ ]+\n", "\n", block)
        if re.sub(r"<[^>]+>", "", block).strip():
            self.blocks.append(block)
        self.buf = ""

    # -- parsing
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        if self.done:
            return
        if self.where is None:
            if tag == "div" and "body" in cls:
                self.where, self.depth, self.seen_body = "body", 0, True
                self.lang = a.get("lang") or "en"
            elif tag == "span" and "tags" in cls and not self.seen_body:
                self.where, self.depth = "tags", 0
            elif tag == "aside" and "old-note" in cls:
                self.where, self.depth = "old", 0
            return
        if tag not in ("img", "br", "hr", "input", "source", "meta", "link", "wbr"):
            self.depth += 1
        if self.where == "old":
            if tag == "p":
                self.old_lang = a.get("lang")
            return
        if self.where != "body":
            return
        self.start(tag, a)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def start(self, tag, a):
        if tag in self.INLINE and not (tag == "code" and self.pre):
            self.add(f"<{self.INLINE[tag]}>")
        elif tag == "a":
            href = a.get("href") or ""
            keep = bool(href) and not href.startswith("#")
            if keep:
                self.add(f'<a href="{html.escape(urllib.parse.urljoin(self.url, href))}">')
            self.links.append(keep)
        elif tag == "br":
            self.br(1)
        elif tag == "img":
            src = a.get("data-full") or a.get("src") or ""
            has_text = bool(self.blocks) or bool(re.sub(r"<[^>]+>", "", self.buf).strip())
            self.images.append((src, has_text))
        elif tag == "iframe":
            m = YOUTUBE.search(a.get("src") or "")
            if m:
                video = f"https://www.youtube.com/watch?v={m.group(1)}"
                self.videos.append(video)
                self.br(2)
                self.add(f'<a href="{video}">{video}</a>')
        elif tag in ("ul", "ol"):
            self.br(1 if self.lists else 2)
            self.lists.append([tag, 0])
        elif tag == "li":
            self.br(1)
            kind = self.lists[-1] if self.lists else ["ul", 0]
            kind[1] += 1
            mark = "•" if kind[0] == "ul" else f"{kind[1]}."
            self.add(" " * (len(self.lists) - 1) + mark + " ")
        elif tag == "hr":
            self.br(2)
            self.add("———")
            self.br(2)
        elif tag == "blockquote":
            self.br(2)
            self.add("<blockquote>")
        elif tag == "pre":
            self.br(2)
            self.add("<pre>")
            self.pre += 1
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "summary"):
            self.br(2)
            self.add("<b>")
        elif tag in ("td", "th"):
            if not self.buf.endswith("\n") and self.buf:
                self.add(" | ")
        elif tag in self.BLOCK:
            self.br(2 if tag not in ("tr", "figcaption") else 1)

    def handle_endtag(self, tag):
        if self.done or self.where is None:
            if tag == "article" and self.seen_body:
                self.done = True
            return
        if tag == "p" and self.where == "old":
            self.old_lang = None
        if self.where == "body":
            self.end(tag)
        self.depth -= 1
        if self.depth < 0:
            if self.where == "body":
                self.flush()
            self.where = None
        elif self.depth == 0 and self.where == "body":
            self.flush()

    def end(self, tag):
        if tag in self.INLINE and not (tag == "code" and self.pre):
            self.buf = self.buf.rstrip(" ")
            self.add(f"</{self.INLINE[tag]}>")
        elif tag == "a":
            if self.links and self.links.pop():
                self.add("</a>")
        elif tag in ("ul", "ol"):
            if self.lists:
                self.lists.pop()
            self.br(1 if self.lists else 2)
        elif tag == "blockquote":
            self.buf = self.buf.rstrip()
            self.add("</blockquote>")
            self.br(2)
        elif tag == "pre":
            self.pre -= 1
            self.add("</pre>")
            self.br(2)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "summary"):
            self.add("</b>")
            self.br(2)
        elif tag in self.BLOCK and tag != "li":
            self.br(2 if tag not in ("tr", "figcaption") else 1)

    def handle_data(self, data):
        if self.done:
            return
        if self.where == "body":
            self.text(data)
        elif self.where == "tags" and data.strip().startswith("#"):
            self.tags.append(data.strip())
        elif self.where == "old" and self.old_lang:
            self.old[self.old_lang] = self.old.get(self.old_lang, "") + data


def length(s):
    """Telegram's length of a text in its HTML: visible characters, in UTF-16 units."""
    visible = html.unescape(re.sub(r"<[^>]+>", "", s))
    return len(visible.encode("utf-16-le")) // 2


def split(blocks, limit):
    """Pack blocks into messages of at most `limit` characters, splitting a
    block that is too long by itself (as plain text) between words."""
    messages, cur = [], ""
    pieces = []
    for b in blocks:
        if length(b) <= limit:
            pieces.append(b)
            continue
        words = html.unescape(re.sub(r"<[^>]+>", "", b)).split(" ")
        part = ""
        for w in words:
            if part and length(html.escape(part + " " + w)) > limit:
                pieces.append(html.escape(part))
                part = w
            else:
                part = f"{part} {w}" if part else w
        if part:
            pieces.append(html.escape(part))
    for p in pieces:
        joined = f"{cur}\n\n{p}" if cur else p
        if cur and length(joined) > limit:
            messages.append(cur)
            cur = p
        else:
            cur = joined
    if cur:
        messages.append(cur)
    return messages


def plan(slug, public):
    """The Telegram calls that post one note: [(method, params, files)]."""
    page = public / "notes" / slug / "index.html"
    if not page.exists():
        raise FileNotFoundError(page)
    source = page.read_text(encoding="utf-8")
    m = re.search(r'<link rel=["\']?canonical["\']? href=["\']?([^"\'\s>]+)', source)
    url = m.group(1) if m else f"https://xekri-mlatus.github.io/notes/{slug}/"
    note = Note(url)
    note.feed(source)
    note.close()

    blocks = list(note.blocks)
    if note.old:
        blocks.append(f"<i>{html.escape(note.old.get(note.lang) or next(iter(note.old.values())), quote=False)}</i>")
    if note.tags:
        blocks.append(" ".join(note.tags))
    text = "\n\n".join(blocks)

    files = []
    for src, _ in note.images:
        path = public / urllib.parse.unquote(urllib.parse.urlparse(src).path).lstrip("/")
        if not path.exists():
            raise FileNotFoundError(f"{slug}: picture {src} isn't in {public}")
        files.append(path)
    # The caption goes above the pictures when the note starts with text.
    above = bool(note.images) and note.images[0][1]

    calls = []
    if not files:
        preview = ({"url": note.videos[0]} if note.videos else {"is_disabled": True})
        for part in split(blocks, TEXT_LIMIT):
            calls.append(("sendMessage", {"text": part, "link_preview_options": preview}, []))
        return calls

    caption = text if length(text) <= CAPTION_LIMIT else ""
    albums = [files[i:i + ALBUM_LIMIT] for i in range(0, len(files), ALBUM_LIMIT)]
    for n, album in enumerate(albums):
        first = n == 0 and caption
        if len(album) == 1:
            params = {"photo": "attach://file0"}
            if first:
                params.update(caption=caption, show_caption_above_media=above)
            calls.append(("sendPhoto", params, album))
        else:
            media = []
            for i, _ in enumerate(album):
                item = {"type": "photo", "media": f"attach://file{i}"}
                if first and i == 0:
                    item.update(caption=caption, parse_mode="HTML",
                                show_caption_above_media=above)
                media.append(item)
            calls.append(("sendMediaGroup", {"media": media}, album))
    if not caption:
        for part in split(blocks, TEXT_LIMIT):
            calls.append(("sendMessage", {"text": part,
                                          "link_preview_options": {"is_disabled": True}}, []))
    return calls


# ------------------------------------------------------------- Telegram API

def call(token, method, params, files):
    """One Bot API call; waits and retries when Telegram asks to slow down."""
    fields = {k: (json.dumps(v) if isinstance(v, (dict, list, bool)) else str(v))
              for k, v in params.items()}
    boundary = uuid.uuid4().hex
    body = bytearray()
    for k, v in fields.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n"
                 f"{v}\r\n").encode("utf-8")
    for i, path in enumerate(files):
        kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file{i}\"; "
                 f"filename=\"{path.name}\"\r\nContent-Type: {kind}\r\n\r\n").encode("utf-8")
        body += path.read_bytes() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}", data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            answer = json.loads(e.read() or b"{}")
            wait = answer.get("parameters", {}).get("retry_after")
            if e.code == 429 and wait and attempt < 4:
                print(f"  Telegram asks to wait {wait} s")
                time.sleep(wait + 1)
                continue
            # The address holds the token, so report only what Telegram said.
            raise SystemExit(f"Telegram refused {method}: {answer.get('description', e.code)}") from None
        except urllib.error.URLError as e:
            raise SystemExit(f"Couldn't reach Telegram for {method}: {e.reason}") from None
    raise SystemExit(f"Telegram kept refusing {method}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    which = ap.add_mutually_exclusive_group(required=True)
    which.add_argument("--since", metavar="COMMIT", help="post the notes added after this commit")
    which.add_argument("--notes", nargs="+", metavar="SLUG", help="post these notes")
    ap.add_argument("--public", default=str(ROOT / "public"), help="the built site (default: public)")
    ap.add_argument("--channel", help="post here instead of TELEGRAM_CHANNEL")
    ap.add_argument("--dry-run", action="store_true", help="print what would be sent")
    args = ap.parse_args()

    notes = all_notes()
    if args.since:
        slugs = added_since(args.since)
    else:
        slugs = [s.strip("/").split("/")[-1] for s in args.notes]
        unknown = [s for s in slugs if s not in notes]
        if unknown:
            raise SystemExit("No such notes: " + ", ".join(unknown))
    if not slugs:
        print("No new notes to post.")
        return
    slugs = sorted(dict.fromkeys(slugs), key=lambda s: notes[s][0])  # oldest first

    public = Path(args.public)
    posts = []
    for slug in slugs:
        try:
            posts.append((slug, plan(slug, public)))
        except FileNotFoundError as e:
            if args.since:  # a draft or a note dated in the future isn't built
                print(f"Skipping {slug}: not in the built site ({e})")
                continue
            raise SystemExit(f"{slug} isn't in the built site: {e}")

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    channel = args.channel or os.environ.get("TELEGRAM_CHANNEL", "")
    if not args.dry_run and not (token and channel):
        raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL must be set.")

    for slug, calls in posts:
        print(f"{slug}: {len(calls)} message(s)")
        for method, params, files in calls:
            params = {"chat_id": channel, **params}
            if method in ("sendMessage", "sendPhoto"):
                params["parse_mode"] = "HTML"
            if args.dry_run:
                shown = {k: v for k, v in params.items() if k != "chat_id"}
                print(f"  {method} {[f.name for f in files]}")
                print("    " + json.dumps(shown, ensure_ascii=False, indent=2).replace("\n", "\n    "))
                continue
            call(token, method, params, files)
            time.sleep(1)  # stay well under Telegram's limits for channels
        if not args.dry_run:
            print("  posted")


if __name__ == "__main__":
    main()
