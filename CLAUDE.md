# Mlatus' notes

A Hugo site with its own theme (`themes/mlatus`, specified in `SPEC.md`),
published to https://xekri-mlatus.github.io/ by GitHub Actions on every push
to `main`. Notes are mostly in Russian, sometimes in English or German.

The site is a wall of whole notes, like a Telegram channel. Note titles are
never shown anywhere (pages, browser tabs, feeds, link previews); where
something needs a name, the theme uses the start of the note's text. Every
current address must keep working: `scripts/check_site.py` checks this.

## Publishing a note

The author drops a draft into a dated folder, `content/notes/YYYY-MM-DD-name/`.
It can be any mix of text, Markdown, images and other files with arbitrary
names. Preparing it for publication means turning the folder into a finished
note:

- **Layout.** A note with images is a folder with `index.md` next to its
  images. A note with no files is a single `content/notes/YYYY-MM-DD-name.md`.
  Remove the draft's leftover files once their content is in the note.
- **Front matter.** Write it by hand, not with `hugo new`: the archetype adds
  `draft` and `status` fields that published notes don't use.

  ```yaml
  ---
  title: "Название заметки"   # in the note's language; never shown on the site
  slug: name                  # the folder name without the date
  date: 2026-11-03T04:45:00+03:00
  tags: [languages, learning]
  cover:
    image: collage.jpg        # or the only image
    alt: "Коллаж из 5 картинок заметки"
  ---
  ```

  - `title`: still required (the collage script and commit messages use
    it), but readers never see it.
  - `date`: when the note was written (the draft's file times are a good
    guide), always `+03:00`. The site shows it as written.
  - `tags`: reuse the existing ones (`grep -rh "^tags:" content/notes`). Add
    `"Long reads"` only when the text runs to 250 words or more. The site
    shows tags as hashtags (`#longreads`).
  - `cover`: only for notes with images. It's the picture in link previews
    and the small square in search results and under neighbouring notes. A
    note with one image uses it as the cover, with the same alt text as in
    the text.
  - Older notes have `cover.hiddenInSingle`, `description` or `<!--more-->`
    from the previous theme. The new theme ignores them; don't add them.
- **Images.** Rename them to short descriptive names (`gehen.jpg`,
  `tablet.jpg`), and give each alt text in the note's language that says
  what it shows (search finds notes by these descriptions too). Use
  `![alt](name.jpg)`, or `{{< figure src="name.jpg" alt="…" width="300" >}}`
  for tall pictures such as phone screenshots and book covers (the figure is
  centred). Place each image next to the text it belongs to. Images with no
  text between them become an album on the wall and show two to a row on the
  note's page.
- **Collage.** Notes with two or more images get a collage as their cover.
  After adding or changing images, run from the repository root:

  ```bash
  python scripts/make_collages.py
  ```

  It sets `cover.image` and `cover.alt` itself (the note needs a `cover:`
  block already). Tiles keep the top of each picture; list images whose
  middle should show in `collageCentre: [name.jpg]`. Look at the resulting
  `collage.jpg`.
- **Text.** Fix typos, grammar and punctuation (em dashes `—`, `т. п.`), but
  keep the author's wording and voice, including the English phrases mixed
  into Russian text. Splitting a long paragraph to make room for an image is
  fine; rewriting is not.
- **Check.** Run `hugo server` (the `hugo` entry in `.claude/launch.json`)
  and look at the note on the wall at `/` and on its page at
  `/notes/<slug>/`. Then run the site checks:

  ```bash
  python scripts/check_site.py
  ```

## The theme

- Templates, CSS and JavaScript are in `themes/mlatus/`; `SPEC.md` says how
  every page should look and behave. Keep the two in step.
- `content_test/` holds formatting samples (the Markdown field guide). Preview
  them with the `hugo-test-content` entry in `.claude/launch.json`, which
  renders in memory so it can't overwrite the main preview's `public/`.
- `mockups/` holds the design mockups the theme was built from, and
  `mockups/current-urls.txt` the addresses `check_site.py` keeps working.

## Git

Commit straight to `main`. A new note's subject is `Add note "<title>"`,
with a short body on what the note is and anything else that changed.
Pushing publishes the site within a minute.
