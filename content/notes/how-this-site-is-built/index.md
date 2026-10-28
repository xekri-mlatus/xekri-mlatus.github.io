---
title: "How This Site Is Built"
date: 2026-10-27T21:00:00+03:00
tags: [meta, hugo, web]
description: "Hugo, the PaperMod theme, page bundles and GitHub Pages — the whole setup in one note."
ShowToc: true
TocOpen: true
---

People sometimes ask how this site works. The short answer: it's a folder of
Markdown files that a program turns into a website. Here's the longer one.

<!--more-->

## The pipeline

![Diagram: content/ goes into Hugo with the PaperMod theme, which produces public/, which GitHub Pages serves](pipeline.svg)

Everything starts as plain text in the `content/` folder. [Hugo](https://gohugo.io/)
reads it, applies the [PaperMod](https://github.com/adityatelange/hugo-PaperMod)
theme, and writes a complete static website to `public/`. There's no database
and no server-side code — just files.

## Writing a note

A new note is one command:

```bash
hugo new notes/my-new-note.md
```

That creates a file with some front matter at the top. A typical note looks like this:

```yaml
---
title: "A Weekend in the Hills"
date: 2026-09-14T19:30:00+03:00
tags: [walks, travel, photos]
description: "Two days, one ridge loop, and a cold lake."
cover:
  image: cover.jpg
  caption: "The view from the second ridge."
ShowToc: true
---
```

The `description` appears under the title and in search results, `tags` group
notes together, and `ShowToc` adds the table of contents you can see above.

## Page bundles for images

When a note has images, I make it a folder instead of a single file. Hugo calls
this a *page bundle*:

```text
content/notes/weekend-in-the-hills/
├── index.md          ← the note itself
├── cover.jpg         ← cover image
├── lake-at-night.jpg
└── trail-map.svg
```

Images in the folder can be referenced by file name alone, and they move
together with the note if I ever rename it.

## Finding things

PaperMod provides everything I need for navigation out of the box:

- [Archive](/archives/) — every note, grouped by year and month.
- [Tags](/tags/) — every tag, each with its own page and RSS feed.
- [Search](/search/) — instant search across all notes. It runs entirely in your
  browser using a small index that Hugo builds alongside the site.

## Publishing

I run the site locally with `hugo server` while writing, and it reloads on every
save. To publish, I push to GitHub, and a GitHub Actions workflow builds the site
and deploys `public/` to GitHub Pages.

> The best part of a static site is what it doesn't have: no updates to apply,
> no logins to protect, and nothing to break at 3 a.m.
