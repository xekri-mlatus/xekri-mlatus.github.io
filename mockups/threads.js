// Threads mockup: notes that continue other notes.
// In the real site each continuation would say `continues: <slug>` in its front
// matter; Hugo works out the reverse ("Continued") links by itself.

const CONTINUES = {
  "mi-klama-le-zarci": "toaq",
  "toaq-and-german": "mi-klama-le-zarci",
  "penguins-escalation": "penguins-for-greenland",
};

const bySlug = Object.fromEntries(NOTES.map(n => [n.slug, n]));
const prevOf = n => bySlug[CONTINUES[n.slug]];
// Usually one, but two notes may continue the same note; oldest first.
const nextsOf = n => NOTES.filter(m => CONTINUES[m.slug] === n.slug).reverse();

// The whole thread a note belongs to, in reading order (a straight chain; a
// branch follows its oldest continuation).
function threadOf(n) {
  let first = n;
  while (prevOf(first)) first = prevOf(first);
  const chain = [first];
  for (let m = nextsOf(first)[0]; m; m = nextsOf(m)[0]) chain.push(m);
  return chain;
}

// A note's label: the start of its text, else its picture's description, else its date.
function label(n, max = 90) {
  const s = (n.text || n.alts[0] || "").replace(/\s+/g, " ").trim();
  if (!s) return longDate(n.date);
  return s.length > max ? s.slice(0, max).replace(/\s+\S*$/, "") + "…" : s;
}

// A Telegram-style quote of the note `m`. Newer above, older below, as on
// the wall: `dir` is "next" (at the top of a note) or "prev" (at the bottom). `newTab` on the wall, where every link to a
// note's page opens in a new tab, as the date does.
function quote(m, dir, newTab) {
  const kind = dir === "next" ? "↑ Next" : "↓ Previous";
  return `<a class="reply ${dir}" href="${threadNoteUrl(m)}"${newTab ? ' target="_blank" rel="noopener"' : ""}>
    ${m.thumb ? `<img src="${m.thumb}" alt="">` : ""}
    <span class="r-text"><span class="r-kind">${kind} · ${shortDate(m.date, false)}</span>
      <span class="r-label">${esc(label(m))}</span></span></a>`;
}
function quotesAbove(n, newTab) { return nextsOf(n).reverse().map(m => quote(m, "next", newTab)).join(""); }
function quotesBelow(n, newTab) { const p = prevOf(n); return p ? quote(p, "prev", newTab) : ""; }

// A tile on the wall, as on the live site (every picture of a run, two to a
// row), with the thread quotes added.
function threadTile(n) {
  const el = document.createElement("article");
  el.className = "card";
  el.innerHTML = `${quotesAbove(n, true)}<div class="body">${n.html}</div>${quotesBelow(n, true)}
    <div class="foot"><div class="tags">${n.tags.map(t => `<a href="${tagUrl(t)}">#${t}</a>`).join("")}</div>
      <a class="when" href="${threadNoteUrl(n)}" target="_blank" rel="noopener" title="Open the note in a new tab">${shortDate(n.date)}</a></div>`;
  galleryize(el.querySelector(".body"));
  fixLinks(el);
  return el;
}

// The mockup's note page is thread-note.html, so links into note.html (in the
// notes' own text too) are pointed there.
const threadNoteUrl = n => `thread-note.html?slug=${n.slug}`;
function fixLinks(root) {
  root.querySelectorAll('a[href^="note.html"]').forEach(a =>
    a.setAttribute("href", a.getAttribute("href").replace(/^note\.html/, "thread-note.html")));
}
