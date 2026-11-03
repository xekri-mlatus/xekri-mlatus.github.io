# Mlatus' notes

A Hugo site (PaperMod theme), published to https://xekri-mlatus.github.io/ by
GitHub Actions on every push to `main`. Notes are mostly in Russian, sometimes
in English or German.

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
  title: "Название заметки"   # in the note's language
  slug: name                  # the folder name without the date
  date: 2026-11-03T04:45:00+03:00
  tags: [languages, learning]
  cover:
    image: collage.jpg        # or the only image
    alt: "Коллаж из 5 картинок заметки"
    hiddenInSingle: true  # already shown in the text
  ---
  ```

  - `date`: when the note was written (the draft's file times are a good
    guide), always `+03:00`.
  - `tags`: reuse the existing ones (`grep -rh "^tags:" content/notes`). Add
    `"Long reads"` only when the text runs to 250 words or more.
  - `cover`: only for notes with images. A note with one image uses it as
    the cover, with the same alt text as in the text.
  - Optional: `description` for the list preview, `<!--more-->` to cut it.
- **Images.** Rename them to short descriptive names (`gehen.jpg`,
  `tablet.jpg`), and give each alt text in the note's language that says
  what it shows. Use `![alt](name.jpg)`, or
  `{{< figure src="name.jpg" alt="…" width="300" >}}` for tall pictures such
  as phone screenshots and book covers (the figure is centred). Place each
  image next to the text it belongs to.
- **Collage.** Notes with two or more images get a collage as their list
  preview. After adding or changing images, run from the repository root:

  ```bash
  python scripts/make_collages.py
  ```

  It sets `cover.image` and `cover.alt` itself. Tiles keep the top of each
  picture; list images whose middle should show in
  `collageCentre: [name.jpg]`. Look at the resulting `collage.jpg`.
- **Text.** Fix typos, grammar and punctuation (em dashes `—`, `т. п.`), but
  keep the author's wording and voice, including the English phrases mixed
  into Russian text. Splitting a long paragraph to make room for an image is
  fine; rewriting is not.
- **Check.** Build with `hugo` (or run `hugo server`, as in
  `.claude/launch.json`) and open the note at `/notes/<slug>/`.

## Git

Commit straight to `main`. A new note's subject is `Add note "<title>"`,
with a short body on what the note is and anything else that changed.
Pushing publishes the site within a minute.
