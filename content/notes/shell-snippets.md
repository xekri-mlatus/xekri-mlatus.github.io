---
title: "Shell Snippets I Keep Reaching For"
date: 2026-08-02T18:40:00+03:00
lastmod: 2026-10-12T10:00:00+03:00
tags: [code, shell, git, reference]
description: "Small commands for Bash, PowerShell and Git that I'd otherwise look up every single time."
ShowToc: true
---

A running list. When I search for the same command a third time, it goes here.

<!--more-->

## Files and folders

Find the ten largest files under the current folder:

```bash
du -ah . 2>/dev/null | sort -rh | head -n 10
```

Rename every `.jpeg` to `.jpg` in one go:

```bash
for f in *.jpeg; do
  mv -- "$f" "${f%.jpeg}.jpg"
done
```

The same in PowerShell, because I switch between machines:

```powershell
Get-ChildItem *.jpeg | Rename-Item -NewName { $_.Name -replace '\.jpeg$', '.jpg' }
```

## Git

Undo the last commit but keep the changes staged — for when I commit too early:

```bash
git reset --soft HEAD~1
```

See which branches have already been merged, so they can be deleted:

```bash
git branch --merged main | grep -v '^\*\|main'
```

A few aliases from my `~/.gitconfig`. The highlighted line is the one I use most:

```ini {hl_lines=[3]}
[alias]
    st = status --short --branch
    lg = log --oneline --graph --decorate -20
    amend = commit --amend --no-edit
    unstage = restore --staged
```

## Quick scripts

Serve the current folder over HTTP — handy for checking a static build:

```bash
python -m http.server 8000
```

Count words in every Markdown file, which is how I keep my
[writing log](/notes/writing-log-2026/):

```python {linenos=true}
from pathlib import Path

total = 0
for path in sorted(Path("content").rglob("*.md")):
    words = len(path.read_text(encoding="utf-8").split())
    total += words
    print(f"{words:>6}  {path}")

print(f"{total:>6}  total")
```

{{< collapse summary="Why not just use shell history?" >}}
I do, with `Ctrl` + `R`. But history is per-machine and full of typos, and it
doesn't tell me *why* a command works. A note does.
{{< /collapse >}}
