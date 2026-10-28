---
title: "A Field Guide to Markdown on This Site"
date: 2026-07-18T11:00:00+03:00
tags: [writing, markdown, reference]
description: "Every kind of formatting this site supports, with examples — mostly so I remember how to write them."
ShowToc: true
TocOpen: false
---

This note is a reference for myself: each section shows one kind of formatting
and how it renders here.

<!--more-->

## Text

Plain paragraphs are just text. You can use **bold**, *italic*, ***both***,
~~strikethrough~~, and `inline code`. Links look like [this one](https://gohugo.io/),
and a bare address such as https://example.org becomes a link automatically.

Straight quotes become "curly" ones, and two hyphens -- like that -- become a dash.

## Headings

Headings from `##` down to `####` appear in the table of contents at the top of
the page. Hover over any heading to get a link straight to it.

### A third-level heading

#### A fourth-level heading

## Lists

Unordered:

- Notes
- Drafts
  - Half-finished drafts
  - Abandoned drafts
- Ideas

Ordered:

1. Write it down.
2. Leave it for a week.
3. Rewrite it.

A checklist:

- [x] Pick a theme
- [x] Write the first notes
- [ ] Add a custom domain

## Quotes

> Write what should not be forgotten.
>
> — Isabel Allende

## Tables

Columns can be aligned left, centre or right:

| Format     | Good for         | Example                 |
| :--------- | :--------------: | ----------------------: |
| List       | Steps, options   | Packing lists           |
| Table      | Comparisons      | Reading list            |
| Code block | Commands, config | [Shell snippets](/notes/shell-snippets/) |

## Code

Fenced code blocks get syntax highlighting and a **copy** button:

```javascript
const greet = (name) => `Hello, ${name}!`;
console.log(greet("garden"));
```

## Definitions

Markdown
: A lightweight markup language for formatting plain text.

Page bundle
: A folder holding a note and its images together.

## Footnotes

Footnotes are useful for asides that would interrupt the sentence.[^1] They're
collected at the bottom of the page.[^2]

## Images

Images use the same syntax as links, with an `!` in front. See
[A Weekend in the Hills](/notes/weekend-in-the-hills/) for a cover image,
a captioned figure and an inline photo.

## Collapsible sections

{{< collapse summary="Click to expand" >}}
Hidden content goes here — good for long lists or spoilers.
It can contain **any** Markdown.
{{< /collapse >}}

---

That's everything. A horizontal rule, like the one above, is three dashes on
their own line.

[^1]: Like this one.
[^2]: And this one.
