// Mlatus' notes: light / dark switch, "/" for search, enlarged pictures, albums,
// the masonry wall with "Load older notes", and search. See SPEC.md.
(() => {
  "use strict";
  const root = document.documentElement;

  // ---------- light / dark: follows the system until the visitor picks one ----------
  const isDark = () => root.dataset.theme
    ? root.dataset.theme === "dark"
    : matchMedia("(prefers-color-scheme: dark)").matches;
  document.querySelector(".theme")?.addEventListener("click", () => {
    const theme = isDark() ? "light" : "dark";
    root.dataset.theme = theme;
    try { localStorage.setItem("theme", theme); } catch (e) { /* private mode: just this page */ }
  });

  // ---------- "/" anywhere opens search, unless you're typing ----------
  document.addEventListener("keydown", e => {
    if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.target.closest("input, textarea, select, [contenteditable]")) return;
    e.preventDefault();
    const q = document.getElementById("q");
    if (q) q.focus(); else location.href = document.body.dataset.search;
  });

  // ---------- enlarged pictures (the original, not the resized copy) ----------
  let lightbox;
  document.addEventListener("click", e => {
    const img = e.target.closest(".body img");
    if (!img || img.closest("a")) return;
    if (!lightbox) {
      lightbox = Object.assign(document.createElement("div"), { className: "lb" });
      lightbox.append(document.createElement("img"));
      lightbox.addEventListener("click", () => lightbox.classList.remove("on"));
      document.body.append(lightbox);
    }
    const big = lightbox.querySelector("img");
    big.src = img.dataset.full || img.currentSrc || img.src;
    big.alt = img.alt;
    lightbox.classList.add("on");
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") lightbox?.classList.remove("on"); });

  // ---------- pictures in a row ----------
  // A block holds only pictures: a figure, or a paragraph of nothing but <img> and line breaks.
  function picturesOf(el) {
    if (el.tagName === "FIGURE") return el.querySelector("figcaption") ? null : [...el.querySelectorAll("img")];
    if (el.tagName !== "P") return null;
    const imgs = el.querySelectorAll("img");
    if (!imgs.length) return null;
    const rest = el.cloneNode(true);
    rest.querySelectorAll("img, br").forEach(x => x.remove());
    return rest.textContent.trim() ? null : [...imgs];
  }
  // Replaces each run of two or more pictures with make(pictures).
  function groupPictures(body, make) {
    let run = [], blocks = [];
    const flush = () => {
      if (run.length >= 2) {
        blocks[0].before(make(run));
        blocks.forEach(b => b.remove());
      }
      run = []; blocks = [];
    };
    for (const el of [...body.children]) {
      const imgs = picturesOf(el);
      if (imgs) { run.push(...imgs); blocks.push(el); } else flush();
    }
    flush();
  }
  // On the wall: an album of up to four, the fourth showing "+N" and leading to the note.
  function albums(tile) {
    groupPictures(tile.querySelector(".body"), imgs => {
      const n = imgs.length, album = document.createElement("div");
      album.className = "album " + (n === 2 ? "n2" : n === 3 ? "n3" : "n4");
      imgs.slice(0, 4).forEach((img, i) => {
        img.removeAttribute("style");
        if (i === 3 && n > 4) {
          const more = Object.assign(document.createElement("a"), {
            className: "plus", href: tile.dataset.url, target: "_blank", rel: "noopener",
            title: "Open the note in a new tab",
          });
          more.append(img, Object.assign(document.createElement("span"), { textContent: `+${n - 4}` }));
          album.append(more);
        } else album.append(img);
      });
      return album;
    });
  }
  // On a note's page: every picture, two to a row, uncropped.
  document.querySelectorAll(".note .body").forEach(body => groupPictures(body, imgs => {
    const gallery = document.createElement("div");
    gallery.className = "gallery";
    imgs.forEach(img => img.removeAttribute("style"));
    gallery.append(...imgs);
    return gallery;
  }));

  // ---------- the wall: masonry, at most three columns of 420px or wider ----------
  const wall = document.getElementById("wall");
  if (wall) {
    const MIN_WIDTH = 420, MAX_COLUMNS = 3;
    wall.querySelectorAll(".tile").forEach(albums);
    wall.classList.add("masonry");

    // Each tile goes where it sits highest, leftmost on a tie, so the order
    // still reads left to right, top to bottom.
    const layout = () => {
      const cs = getComputedStyle(wall);
      const gap = parseFloat(getComputedStyle(root).getPropertyValue("--gap")) || 32;
      const padX = parseFloat(cs.paddingLeft), padTop = parseFloat(cs.paddingTop);
      const inner = wall.clientWidth - 2 * padX;
      const n = Math.max(1, Math.min(MAX_COLUMNS, Math.floor((inner + gap) / (MIN_WIDTH + gap))));
      const width = (inner - gap * (n - 1)) / n;
      const heights = new Array(n).fill(0);
      wall.style.minHeight = wall.offsetHeight + "px";  // keep the scroll position while re-placing
      for (const tile of wall.querySelectorAll(".tile")) {
        tile.style.width = width + "px";
        const col = heights.indexOf(Math.min(...heights));
        tile.style.left = padX + col * (width + gap) + "px";
        tile.style.top = padTop + heights[col] + "px";
        heights[col] += tile.offsetHeight + gap;
      }
      wall.style.height = Math.max(...heights) - gap + padTop + parseFloat(cs.paddingBottom) + "px";
      wall.style.minHeight = "";
    };
    let timer;
    const later = () => { clearTimeout(timer); timer = setTimeout(layout, 80); };
    const watch = scope => scope.querySelectorAll("img, iframe").forEach(el => el.addEventListener("load", later));
    watch(wall);
    addEventListener("resize", later);
    layout();

    // "Load older notes": fetch the next page and add its tiles here.
    const older = document.querySelector(".older");
    older?.addEventListener("click", async e => {
      e.preventDefault();
      older.setAttribute("aria-busy", "true");
      try {
        const res = await fetch(older.href);
        if (!res.ok) throw new Error(res.status);
        const doc = new DOMParser().parseFromString(await res.text(), "text/html");
        const tiles = [...doc.querySelectorAll("#wall .tile")];
        tiles.forEach(t => { albums(t); wall.append(t); });
        tiles.forEach(watch);
        layout();
        const next = doc.querySelector(".older");
        if (next) { older.href = next.getAttribute("href"); older.removeAttribute("aria-busy"); }
        else older.parentElement.remove();
      } catch (err) {
        location.href = older.href;  // fall back to opening the next page
      }
    });
  }

  // ---------- search ----------
  const search = document.querySelector(".search[data-index]");
  if (search) {
    const q = document.getElementById("q"), status = document.getElementById("status"), hits = document.getElementById("hits");
    let notes = null;
    const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
    const mark = (s, needle) => esc(s).replace(
      new RegExp(esc(needle).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi"), m => `<mark>${m}</mark>`);
    // About two lines around the first match.
    const snippet = (text, needle) => {
      const i = text.toLowerCase().indexOf(needle.toLowerCase());
      if (i < 0) return text.slice(0, 160) + (text.length > 160 ? "…" : "");
      const from = Math.max(0, i - 60), to = Math.min(text.length, i + needle.length + 100);
      return (from > 0 ? "…" : "") + text.slice(from, to) + (to < text.length ? "…" : "");
    };
    const plural = k => `${k} ${k === 1 ? "note" : "notes"}`;

    const run = () => {
      const needle = q.value.trim();
      history.replaceState(null, "", needle ? `?q=${encodeURIComponent(needle)}` : location.pathname);
      if (!notes) { status.textContent = "Loading…"; return; }
      if (needle.length < 2) {
        status.innerHTML = `Type to search ${plural(notes.length)}. Press <kbd>/</kbd> on any page to come here.`;
        hits.innerHTML = "";
        return;
      }
      // The text first, then the picture descriptions (that's how memes without
      // text are found). Titles are never shown, so they aren't searched. Newest first.
      const low = needle.toLowerCase();
      const found = notes.map(n => {
        if (n.text.toLowerCase().includes(low)) return { n, s: snippet(n.text, needle), pic: false };
        const alt = (n.alts || []).find(a => a.toLowerCase().includes(low));
        return alt ? { n, s: snippet(alt, needle), pic: true } : null;
      }).filter(Boolean);
      status.textContent = found.length ? `${plural(found.length)} found` : "Nothing found.";
      hits.innerHTML = found.map(({ n, s, pic }) => `<a class="hit card" href="${esc(n.url)}">
          ${n.thumb ? `<img src="${esc(n.thumb)}" width="64" height="64" alt="" loading="lazy">` : ""}
          <span style="min-width:0"><span class="d" style="display:block">${esc(n.date)}${pic ? " · in a picture" : ""}</span>
          <span class="s" style="display:block">${mark(s, needle)}</span></span></a>`).join("");
    };

    q.value = new URLSearchParams(location.search).get("q") || "";
    q.addEventListener("input", run);
    run();
    fetch(search.dataset.index)
      .then(r => r.json())
      .then(data => { notes = data; run(); })
      .catch(() => { status.textContent = "Search isn't available right now."; });
  }
})();
