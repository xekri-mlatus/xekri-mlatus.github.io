# Spec: a new theme for Mlatus' notes

Status: **all questions answered** (2026-11-15), waiting for your final OK.
Nothing in it is built yet. Once you approve it, it becomes the checklist
the theme is built and checked against.

The approved look lives in the mockups (`mockups/tiles.html`, `note.html`,
`tags.html`, `tag.html`, `search.html`, `about.html`, `404.html`; run the
`mockups` server from `.claude/launch.json` and open
`http://localhost:8765/mockups/tiles.html`). Where this spec and a mockup
disagree, the spec wins.

## Objective

Replace PaperMod with a theme of our own that makes the site read like a
calm Telegram-style channel. Most notes are a meme or a picture with a line
of text, so they appear in full on one wall of tiles instead of as a list
of articles you click into.

Done means: the site builds and deploys as today, every current address still
works, every page matches the mockups, and no note title shows anywhere.

### In scope

- A new Hugo theme in this repository, used in place of PaperMod.
- Every page type: the wall, a note's page, tags, one tag, artifacts, search,
  About, 404.
- Feeds, link previews, the search index, and redirects for removed pages.
- Removing what the new design drops (listed under *Removed*).

### Out of scope

- Changing any note's text or front matter. Titles stay in the notes for now;
  the theme just never shows them.
- Comments, reactions, share buttons, a Telegram link under notes, analytics.
- An Archive page.
- Changing how notes are written and published (`CLAUDE.md`), except where
  the theme makes a step unnecessary.

## Design rules for every page

- **Look.** The "Calm" look from the mockups: plain background (warm
  off-white `#f3f2ee` light, blue-grey `#11171e` dark), white or `#19222c`
  tiles with a hairline border and 16px corners, no shadows. System font
  (`system-ui`), 15px on the wall, 16px on a note's page. Colours as defined
  in `mockups/site.css`.
- **Light and dark.** Follow the system setting. A ☾ / ☀ button in the
  header switches it; the choice is remembered in the browser and applies
  on every page.
- **No titles, anywhere.** Not on pages, not in browser tabs, link previews,
  feeds or the search index. Where something needs a name, use the start of
  the note's text (about 60 characters, cut at a word, with "…"), else the
  first picture's description, else the date. This is called the
  **note's label** below.
- **Tags** are shown as hashtags: lower case, spaces removed (`#memes`,
  `#longreads`, `#oldposts`). Their addresses don't change
  (`/tags/long-reads/`).
- **Dates** are the time the note was written, as in its front matter
  (+03:00, not converted to the visitor's time zone). On tiles:
  `3 Nov, 04:45`, with the year added when it isn't the year of the build
  (`10 Jun 2017, 12:00`). On a note's page: `3 November 2026, 04:45`.
- **Interface text** is in English, as now. A note's text gets `lang="ru"`
  when it's mostly Cyrillic, otherwise `lang="en"`, so browsers hyphenate
  and read it correctly.
- **Phones.** Below 700px wide: 16px side margins, 20px gaps, one column of
  tiles, no sideways scrolling anywhere.
- **Without JavaScript** everything stays readable and every link works.
  The wall falls back to a plain grid; search says it needs JavaScript.

## Header and footer (every page)

- Sticky header with a thin line under it: avatar (the "M" circle, for now)
  and "Mlatus' notes" with "73 notes" under it, both leading to the wall. On
  the right: **Notes · Tags · Artifacts · Search · About**, the current one
  in bold, and the theme button.
- Below 640px the links move to their own row under the name.
- Footer, centred and grey: `Mlatus · RSS`. "Mlatus" leads to About, "RSS"
  to `/notes/index.xml`.

## Pages

### The wall: `/` (and `/notes/`)

- Notes newest first, as tiles in masonry columns: each tile goes where it
  sits highest, leftmost on a tie, so the order reads left to right, top to
  bottom.
- At most 3 columns, each at least 420px wide; the wall is at most 1440px
  wide and centred; 32px gaps and margins.
- Each tile shows the **whole note**: no title, no "Show more", no cut at
  `<!--more-->`. Long reads are ordinary tiles.
- **Pictures** fill the tile's width, at most 380px tall (narrower for tall
  ones); a figure with a set width (phone screenshots) keeps that width.
  Two or more pictures in a row with nothing between them form a
  **gallery**: every one of them, two to a row, uncropped, as on the note's
  page. (Changed 2026-11-15: an earlier album showed at most four, cropped,
  with "+N" for the rest, which hid most of a meme collection.)
  Clicking a picture enlarges it over the page; a click or Esc closes it.
- **YouTube** videos play inside the tile.
- **Tile footer**, small and grey: the hashtags on the left (each leads to
  its tag page) and the date on the right. The date leads to the note's own
  page **in a new tab**; it turns blue and underlined on hover.
- **More notes:** 24 tiles per page. When the bottom of the wall comes
  within about a screen (1200px), the next 24 are added by themselves,
  without leaving the page; under the wall a "Load older notes" button does
  the same on click and says "Loading older notes…" meanwhile. It disappears
  after the last note. If loading fails, it stops loading by itself and the
  button simply opens the next page. Without JavaScript it's a link to
  `/page/2/` and so on. (Changed 2026-11-15: loading used to wait for the
  click.)
- `/notes/` shows the same wall (pointing search engines to `/` as the main
  copy), so its old links and pages keep working.

### A note's page: `/notes/<slug>/`

- One column, 680px wide, centred, holding a single tile:
  - the long date and the hashtags, small and grey, at the top;
  - the whole note, at 16px. Pictures fill the column, at most 80% of the
    screen tall; pictures in a row show two to a row, uncropped. Click to
    enlarge.
  - For notes written before 2025, the existing bilingual disclaimer
    ("This is an old note…" / "Это старая заметка…") in a quiet grey box at
    the end.
- Under the tile: "← Newer" and "Older →", each with a small square picture
  (if the note has one), the date, and the first two lines of the note's
  text (or its first picture's description). Then "All notes".
- Tab: `<note's label> · Mlatus' notes`.
- No title, breadcrumbs, reading time, table of contents, share buttons or
  "edit" link.

### Threads

(Added 2026-11-21. Mockups: `mockups/threads.html` and
`mockups/thread-note.html?slug=mi-klama-le-zarci`.) A note can continue an
earlier one; notes linked this way form a **thread**. As everywhere on the
site, newer notes are above and older ones below (changed 2026-11-21: the
first version put the older note above).

- **Writing one.** The new note says which note it continues, by slug, in its
  front matter: `continues: toaq`. Nothing changes in the earlier note: the
  link back to the new one is worked out when the site is built. A thread is a
  chain; if two notes ever continue the same note, both are linked from it, and
  the thread view follows the older one.
- **Quotes, both ways.** Like a reply in Telegram, a note in a thread
  **quotes** its neighbours in the thread: a blue bar on the left, a light
  blue background, the direction and date in blue, then the other note's label
  in grey on one line, and its small square picture (if it has one) on the
  left. The whole quote is a link. A note that has been continued starts with
  a quote of the newer note, "↑ Next · 29 Nov 2025"; a note that continues
  another ends, just above its footer, with a quote of the older one,
  "↓ Previous · 22 Nov 2025".
- **On the wall** the quotes open the linked note's own page **in a new tab**,
  like the date. The wall does not scroll to the linked tile.
- **On a note's page** the quotes are in the same places in the tile and open
  the linked note's page in the same tab. "← Newer" and "Older →" under the
  tile stay as they are: they go by time, the quotes by thread.
- **The whole thread at once.** At the bottom of a note in a thread, a
  rounded button "Show whole thread · 3 notes" shows every part of the thread
  on the same page instead of the one note: "Thread · 3 notes" and a "Show this
  note only" button above, then each part as its own tile, newest first,
  joined by a thin vertical line, with the long date, "2 of 3" and the
  hashtags at the top (parts are numbered in reading order, so the top one is
  "3 of 3"). The note whose page it is has a blue outline and says
  "2 of 3 · this note"; the other parts' dates lead to their pages. The quotes
  aren't shown in this view (the line already says what comes before and
  after). "Show this note only" again at the bottom. "← Newer" and "Older →"
  stay under it.
- The thread view's address is the note's address with `#thread`
  (`/notes/mi-klama-le-zarci/#thread`), so it can be shared, and the browser's
  Back button returns to the one note. It needs no JavaScript: every part is
  in the page from the start, shown by CSS when the address ends in `#thread`.
  No new pages or addresses.
- **Feeds:** a continuation's item starts with a "Previous: <label>" link to
  the note it continues.
- Link previews, search and tag pages don't change.

### Tags: `/tags/`

- Heading "Tags", then "22 tags, most used first", then every tag as a
  rounded chip `#memes 23`, most used first, ties alphabetical. Each chip
  leads to the tag's page.

### One tag: `/tags/<tag>/`

- Heading `#memes`, then "23 notes · all tags", then that tag's notes on the
  same wall as `/`, with the same "Load older notes".

### Search: `/search/`

- A search box at the top, focused on arrival. Results appear as you type,
  from 2 characters on.
- It finds the query, ignoring case, in the notes' **text** and in their
  **picture descriptions** (so memes without text are found). It doesn't
  search titles. Newest first.
- Each result: a small square picture (if any), the date (with "· in a
  picture" when the match is in a description), and about two lines around
  the match with the match highlighted. The whole result leads to the note.
- The query is kept in the address (`/search/?q=кот`), so a search can be
  shared or reloaded.
- Pressing `/` on any page (outside a text field) opens search.
- Search reads `/index.json`, which the theme generates with each note's
  address, date, text, picture descriptions and small picture, but no title.
  No search library: plain matching, as in the mockup.

### About: `/about/`

- One tile like a Telegram channel's info: a large avatar, "Mlatus' notes",
  "73 notes since 2017 · 22 tags" (counted at build time), then the text of
  `content/about.md` as written, then an RSS chip.

### Artifacts: `/artifacts/` and `/artifacts/<name>/`

(Added 2026-11-17.) Artifacts are interactive pages and references made
elsewhere (such as "Academic Linking Words"), each a whole HTML page with its
own design. Unlike notes, they have names, and the site shows them.

- **The list**, `/artifacts/`: heading "Artifacts", the section's description
  as the lead, then one card per artifact, newest first: its name in bold,
  its description in grey, and the day it was added. The whole card leads to
  the artifact. Tab: `Artifacts · Mlatus' notes`.
- **An artifact**, `/artifacts/<name>/`: the page exactly as it was made, in
  its own design, with no site header or footer. The site adds only:
  - a thin bar at the very top, `← Mlatus' notes / Artifacts`, in the system
    font, inheriting the page's colours, leading to the wall and the list;
  - the visitor's light / dark choice from the site (`data-theme` on
    `<html>`), for pages that honour it;
  - a description, a canonical address and link previews (the artifact's
    name and description).
- **Self-contained.** Artifacts load nothing from other sites. Fonts from
  Google Fonts are stored with the artifact (`scripts/localize_fonts.py`).
- Artifacts are **not** on the wall, in any feed, or in search; the section
  has no feed. They are in `/sitemap.xml`.
- Each artifact is a folder, `content/artifacts/<name>/`: `index.md` with
  `title`, `date` and `description`, the page's HTML file (any name), and
  the files it loads (`fonts/`). Hugo's `security.allowContent` lets HTML
  files into `content/` for this.

### Not found: `/404.html`

- A tile with a large grey "404", "Nothing here", "There's no note at this
  address. It may have moved, or the link has a typo.", and chips for
  "All notes" and "Search". GitHub Pages serves it for unknown addresses.

## Addresses, feeds and previews

- **Every address in `mockups/current-urls.txt` keeps working**, except the
  four under `/public/` (see *Removed*). That covers notes and their images,
  `/tags/…`, `/search/`, `/about/`, the numbered pages (`/page/2/`,
  `/notes/page/2/`, `/tags/memes/page/2/`), every `index.xml`,
  `/index.json`, `/sitemap.xml`, `/robots.txt` and `/404.html`.
- `/archives/` becomes a redirect to `/`.
- **Page numbers:** today's 8 notes per page make `/page/2/` to `/page/10/`.
  With 24 per page there are only 4 pages, so `/page/5/` to `/page/10/`
  (and the same for `/notes/page/…` and tag pages such as
  `/tags/memes/page/3/`) become redirects to the wall or tag page they
  belonged to. A page number then shows different notes than before; only
  search engines are likely to notice. (Decided: 24 per batch.)
- **RSS** (`/index.xml`, `/notes/index.xml`, `/tags/<tag>/index.xml`): only
  notes (the About page drops out of `/index.xml`), each item with the
  note's label as its title, the full note as its content (pictures with
  full addresses), and its date.
- **Link previews** (Telegram, messengers, social sites): the note's label as
  the preview's title, the start of its text as the description, and its
  cover picture (the collage or only picture) as the image.

## Pictures

- An image render hook and a `figure` shortcode replacement output every
  picture with its width and height, so tiles don't jump while pictures
  load, and with `loading="lazy"` below the first screen.
- Pictures are served as resized copies (at most 1200px wide); the
  enlarged view opens the original.
- `scripts/make_collages.py` stays: collages are still the cover used for
  link previews and as the small picture in search results and under notes.

## Removed

- The PaperMod theme (its git submodule) and the overrides made for it:
  `layouts/_partials/extend_post_content.html`,
  `assets/css/extended/custom.css`.
- The Archive page (`content/archives.md`) and its menu link.
- PaperMod-only settings in `hugo.yaml` (share buttons, breadcrumbs, reading
  time, ToC, Fuse options and the like).
- The stray `content/public/` folder: four leftover files committed by
  mistake, which Hugo publishes as junk addresses under `/public/`.

## Tech stack

- Hugo extended 0.169.0, the same version as the deploy workflow. No Node,
  no npm, no CDN, no web fonts, no new dependencies. (Artifacts may bring
  their own fonts, stored with them.)
- One CSS file and one small JavaScript file of our own (theme switch,
  masonry, galleries, enlarged pictures, "Load older notes", search, the `/`
  key), processed with Hugo Pipes (minified, fingerprinted).

## Project structure

```
themes/mlatus/                 the new theme (in this repo, not a submodule)
  layouts/
    baseof.html                page frame: head, header, footer
    home.html, section.html    the wall (/ and /notes/)
    page.html                  a note's page
    taxonomy.html, term.html   /tags/ and /tags/<tag>/
    search.html, about.html    special pages (chosen by layout in front matter)
    artifacts/                 /artifacts/ (section.html) and an artifact (page.html)
    404.html
    home.rss.xml, …            feeds;  home.json for /index.json
    _partials/                 header, footer, tile, date, label, head/meta
    _markup/render-image.html  pictures
    _shortcodes/figure.html    figures, same output as pictures
  assets/css/main.css
  assets/js/main.js
hugo.yaml                      theme: mlatus; pagination 24; outputs
content/                       unchanged, except archives.md and public/ go
scripts/check_site.py          new: the automated checks below
```

## Code style

Templates stay small and say why when it isn't obvious; CSS uses the colour
tokens from the mockups; JavaScript is plain, no build step. For example:

```go-html-template
{{- /* A tile on the wall. No title: the note speaks for itself. */ -}}
<article class="card" lang="{{ partial "lang.html" . }}">
  <div class="body">{{ .Content }}</div>
  <footer class="foot">
    <div class="tags">{{ range .GetTerms "tags" }}<a href="{{ .RelPermalink }}">#{{ partial "hashtag.html" .LinkTitle }}</a>{{ end }}</div>
    <a class="when" href="{{ .RelPermalink }}" target="_blank" rel="noopener">{{ partial "date-short.html" . }}</a>
  </footer>
</article>
```

## Testing

- **Build:** `hugo --gc --minify` finishes with no errors or warnings.
- **Automated checks** (`python scripts/check_site.py`, builds into a
  temporary folder):
  - every address in `mockups/current-urls.txt` exists (except `/public/`),
    as a page or as a redirect; `/archives/` and page numbers past the last
    page redirect where this spec says;
  - no note's title appears in any built page, feed or `index.json`, unless
    those words are also in the note's own text (as with "Mob Control");
  - every `<img>` has a width, a height and an `alt`;
  - `/index.xml` holds exactly the 73 notes, and `/index.json` the notes only;
  - every artifact has its bar back to the site, loads nothing from another
    site, and every file it loads is there;
  - every `continues:` names another, older note, and the two notes' pages
    and tiles link to each other.
- **In the browser** (`hugo server`, the `hugo` entry in `launch.json`), at
  1440px, 1100px and 375px, light and dark: the wall, a note with a gallery
  (`mob-control`), an old note (`welcome`), a note with a video
  (`penguins-escalation`), `/tags/`, `/tags/memes/`, search for "кот" and
  "Падме", About, an unknown address. Compare with the mockups; check there's
  no sideways scrolling and no console errors; scrolling down reaches the
  first note (2017).
- **Formatting:** build once with `--contentDir content_test` and check its
  Markdown field guide (headings, lists, tables, code, quotes, footnotes)
  looks right in a tile and on a page.

## Boundaries

- **Always:** keep every current address; keep notes' Markdown as it is;
  run the checks above before asking you to look; work on the `new-theme`
  branch.
- **Ask first:** pushing or merging to `main` (pushing publishes the site);
  removing the PaperMod submodule; touching any note; changing the deploy
  workflow or `CLAUDE.md`; adding any dependency.
- **Never:** show a note's title; load anything from another site (fonts,
  scripts, trackers), YouTube embeds aside; break or rename an address.

## Success criteria

1. `hugo --gc --minify` and the deploy workflow build the site unchanged.
2. `scripts/check_site.py` passes.
3. Each page matches its mockup at the three widths, in light and dark.
4. You've looked at it locally and approved it before anything is pushed.

## Decisions

Answered on 2026-11-15:

1. **Avatar:** keep the "M" circle for now.
2. **`/notes/`:** the same wall as `/`.
3. **Pictures:** resized copies, at most 1200px wide; the original when
   enlarged.
4. **Theme folder:** `themes/mlatus/`.
5. **Mockups:** keep `mockups/` for now.
6. **Branch:** build on a new branch, `new-theme`, and merge into `main` only
   when you approve.
7. **Notes per batch:** 24 on the wall and on tag pages. Page numbers that
   no longer exist redirect to the wall or tag page they belonged to.

There are no open questions left.
