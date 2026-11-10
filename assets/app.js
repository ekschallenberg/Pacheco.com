/* Shared by every page: navigation, data loading, CSV parsing, service worker registration. */
(function () {
  const PAGES = [["index.html", "Today"], ["browse.html", "Browse"], ["market.html", "Market"]];
  const here = location.pathname.split("/").pop() || "index.html";
  const nav = document.getElementById("nav");
  if (nav) {
    nav.className = "top";
    nav.innerHTML = '<a class="brand" href="index.html">Job<small>Watcher</small></a>' + PAGES.map(([h, t]) =>
      `<a class="link" href="${h}"${h === here ? ' aria-current="page"' : ""}>${t}</a>`).join("");
  }

  function parseCSV(text) {
    const rows = []; let row = [], field = "", q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) {
        if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else q = false; } else field += c;
      } else if (c === '"') q = true;
      else if (c === ",") { row.push(field); field = ""; }
      else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
      else if (c !== "\r") field += c;
    }
    if (field !== "" || row.length) { row.push(field); rows.push(row); }
    const head = rows.shift() || [];
    return rows.filter(r => r.length === head.length).map(r => Object.fromEntries(head.map((h, i) => [h, r[i]])));
  }

  async function getText(path) {
    const r = await fetch(path, { cache: "no-cache" });
    if (!r.ok) throw new Error(path + " " + r.status);
    return r.text();
  }
  async function loadHistory() {
    return parseCSV(await getText("data/history.csv")).map(r => Object.assign(r, {
      in_role: r.in_role === "true", first_run: r.first_run === "true" }));
  }
  async function loadStatus() { return JSON.parse(await getText("data/status.json")); }
  function esc(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
  function dayNum(d) { const [y, m, dd] = d.split("-").map(Number); return Date.UTC(y, m - 1, dd) / 86400000; }

  const SMALL = new Set(["a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "vs", "per"]);
  /* Capitalize the main words of a heading; leave small words lowercase (except first/after a colon) and keep words that already have capitals (FP&A, USA). */
  function titleCase(text) {
    let startOfClause = true;
    return String(text).split(/(\s+)/).map(tok => {
      if (/^\s*$/.test(tok)) return tok;
      const m = tok.match(/^([^A-Za-z0-9]*)(.*)$/), lead = m[1], word = m[2];
      let out = word;
      if (word && !/[A-Z]/.test(word.slice(1)) && /^[a-z]/.test(word) && (startOfClause || !SMALL.has(word.toLowerCase().replace(/[^a-z]/g, "")))) out = word[0].toUpperCase() + word.slice(1);
      startOfClause = /[:;]$/.test(tok);
      return lead + out;
    }).join("");
  }
  const fmt = n => (n === null || n === undefined || n === "" ? "" : Number(n).toLocaleString("en-US"));
  const ATS = { greenhouse: "Greenhouse", lever: "Lever", ashby: "Ashby" };
  /* "greenhouse-stripe" + employer "Stripe" -> "Greenhouse: Stripe" */
  function sourceLabel(name, employer) {
    const i = name.indexOf("-"), ats = name.slice(0, i), token = name.slice(i + 1);
    return `${ATS[ats] || titleCase(ats)}: ${employer || titleCase(token)}`;
  }

  window.JW = { parseCSV, loadHistory, loadStatus, esc, dayNum, titleCase, fmt, sourceLabel };

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
