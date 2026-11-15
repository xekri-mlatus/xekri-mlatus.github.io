// Shared pieces of the page mockups: theme, header, dates, albums, tiles, masonry, lightbox.

const SITE_NAME = "Mlatus' notes";
const CURRENT_YEAR = 2026;
// The demo has no feed of its own, so RSS links go to the live site's notes feed.
const RSS = "https://xekri-mlatus.github.io/notes/index.xml";
const MONTHS = ["January", "February", "March", "April", "May", "June", "July",
  "August", "September", "October", "November", "December"];

// ---------- theme: follows the system unless the visitor picked one ----------
function storedTheme() { try { return localStorage.getItem("theme"); } catch { return null; } }
function applyTheme(t) {
  if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
}
applyTheme(storedTheme());
function isDark() {
  const t = document.documentElement.dataset.theme;
  return t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
}
function toggleTheme() {
  const t = isDark() ? "light" : "dark";
  applyTheme(t);
  try { localStorage.setItem("theme", t); } catch {}
  document.querySelector(".theme").textContent = isDark() ? "☀" : "☾";
}

// ---------- header and footer ----------
function renderHeader(current) {
  const links = [["Notes", "tiles.html"], ["Tags", "tags.html"], ["Search", "search.html"], ["About", "about.html"]];
  const header = document.createElement("header");
  header.className = "top";
  header.innerHTML = `<div class="top-inner">
    <a class="brand" href="tiles.html"><div class="avatar">M</div>
      <div><div class="name">${SITE_NAME}</div><div class="sub">${NOTES.length} notes</div></div></a>
    <nav>${links.map(([n, h]) => `<a href="${h}"${n === current ? ' class="cur"' : ""}>${n}</a>`).join("")}</nav>
    <button class="theme" title="Switch light / dark">${isDark() ? "☀" : "☾"}</button>
  </div>`;
  document.body.prepend(header);
  header.querySelector(".theme").addEventListener("click", toggleTheme);

  const foot = document.createElement("footer");
  foot.className = "site-foot";
  foot.innerHTML = `<a href="about.html">Mlatus</a> · <a href="${RSS}">RSS</a>`;
  document.body.append(foot);
}

// "/" anywhere jumps to search, unless you're typing.
document.addEventListener("keydown", e => {
  if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
  if (e.target.closest("input, textarea, [contenteditable]")) return;
  if (location.pathname.endsWith("search.html")) { document.querySelector("#q")?.focus(); e.preventDefault(); return; }
  e.preventDefault();
  location.href = "search.html";
});

// ---------- dates (taken from the string, so the +03:00 time stays as written) ----------
function parts(iso) {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return { y, m, d, time: iso.length > 10 ? iso.slice(11, 16) : "" };
}
function shortDate(iso, withTime = true) {
  const { y, m, d, time } = parts(iso);
  let s = `${d} ${MONTHS[m - 1].slice(0, 3)}`;
  if (y !== CURRENT_YEAR) s += ` ${y}`;
  return withTime && time ? `${s}, ${time}` : s;
}
function longDate(iso) {
  const { y, m, d, time } = parts(iso);
  return `${d} ${MONTHS[m - 1]} ${y}` + (time ? `, ${time}` : "");
}

const noteUrl = n => `note.html?slug=${n.slug}`;
const tagUrl = t => `tag.html?t=${encodeURIComponent(t)}`;
const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// ---------- runs of images ----------
// A block holds only images: a figure, or a paragraph of nothing but <img> and line breaks.
function imagesOf(el) {
  if (el.tagName === "FIGURE") return [...el.querySelectorAll("img")];
  if (el.tagName !== "P") return null;
  const imgs = el.querySelectorAll("img");
  if (!imgs.length) return null;
  const rest = el.cloneNode(true);
  rest.querySelectorAll("img, br").forEach(x => x.remove());
  return rest.textContent.trim() ? null : [...imgs];
}
// Groups images that follow each other; `make(imgs)` returns the element that replaces them.
function groupImages(body, make) {
  const blocks = [...body.children];
  let run = [], first = null;
  const flush = () => {
    if (run.length >= 2) {
      const el = make(run.map(i => i.cloneNode()));
      first.before(el);
      blocks.filter(b => b.dataset.inRun).forEach(b => b.remove());
    }
    blocks.forEach(b => delete b.dataset.inRun);
    run = []; first = null;
  };
  blocks.forEach(b => {
    const imgs = imagesOf(b);
    if (imgs) { if (!first) first = b; b.dataset.inRun = "1"; run.push(...imgs); }
    else flush();
  });
  flush();
}
// On the wall: an album of up to four tiles, "+N" leading to the note.
function albumize(body, url) {
  groupImages(body, imgs => {
    const n = imgs.length, el = document.createElement("div");
    el.className = "album " + (n === 2 ? "n2" : n === 3 ? "n3" : "n4");
    imgs.slice(0, 4).forEach((img, i) => {
      if (i === 3 && n > 4) {
        const a = document.createElement("a");
        a.className = "plus"; a.href = url; a.target = "_blank"; a.rel = "noopener";
        a.append(img, Object.assign(document.createElement("span"), { textContent: `+${n - 4}` }));
        el.append(a);
      } else el.append(img);
    });
    return el;
  });
}
// On a note's page: every image, two to a row.
function galleryize(body) {
  groupImages(body, imgs => { const el = document.createElement("div"); el.className = "gallery"; el.append(...imgs); return el; });
}

// ---------- a tile on the wall ----------
function tile(n) {
  const el = document.createElement("article");
  el.className = "card";
  el.innerHTML = `<div class="body">${n.html}</div>
    <div class="foot"><div class="tags">${n.tags.map(t => `<a href="${tagUrl(t)}">#${t}</a>`).join("")}</div>
      <a class="when" href="${noteUrl(n)}" target="_blank" rel="noopener" title="Open the note in a new tab">${shortDate(n.date)}</a></div>`;
  albumize(el.querySelector(".body"), noteUrl(n));
  return el;
}

// ---------- masonry: at most three columns, each post where it sits highest ----------
function masonry(wall, tiles, minWidth = 420, maxCols = 3) {
  const lay = () => {
    const cs = getComputedStyle(wall);
    const gap = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--gap"));
    const pad = parseFloat(cs.paddingLeft), inner = wall.clientWidth - 2 * pad;
    const n = Math.max(1, Math.min(maxCols, Math.floor((inner + gap) / (minWidth + gap))));
    const colW = (inner - gap * (n - 1)) / n, heights = new Array(n).fill(0);
    wall.style.minHeight = wall.offsetHeight + "px";  // keep the scroll position while re-placing
    tiles.forEach(t => {
      if (!t.parentNode) wall.append(t);
      t.style.width = colW + "px";
      const c = heights.indexOf(Math.min(...heights));
      t.style.left = pad + c * (colW + gap) + "px";
      t.style.top = parseFloat(cs.paddingTop) + heights[c] + "px";
      heights[c] += t.offsetHeight + gap;
    });
    wall.style.height = Math.max(...heights) - gap + parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom) + "px";
    wall.style.minHeight = "";
  };
  let timer;
  const later = () => { clearTimeout(timer); timer = setTimeout(lay, 100); };
  window.addEventListener("resize", later);
  tiles.forEach(t => t.querySelectorAll("img").forEach(i => i.complete || i.addEventListener("load", later)));
  lay();
}

// ---------- lightbox ----------
document.addEventListener("click", e => {
  const img = e.target.closest(".body img");
  if (!img || img.closest("a")) return;
  let lb = document.querySelector(".lb");
  if (!lb) {
    lb = Object.assign(document.createElement("div"), { className: "lb" });
    lb.append(document.createElement("img"));
    lb.addEventListener("click", () => lb.classList.remove("on"));
    document.body.append(lb);
  }
  lb.querySelector("img").src = img.src;
  lb.classList.add("on");
});
document.addEventListener("keydown", e => { if (e.key === "Escape") document.querySelector(".lb")?.classList.remove("on"); });

// ---------- tags ----------
function tagCounts() {
  const counts = {};
  NOTES.forEach(n => n.tags.forEach(t => counts[t] = (counts[t] || 0) + 1));
  return Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}
const plural = (k, one, many) => `${k} ${k === 1 ? one : many}`;
