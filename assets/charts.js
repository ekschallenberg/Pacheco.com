/* Tiny inline-SVG chart helpers (no libraries, so the site works offline). */
(function () {
  const NS = "http://www.w3.org/2000/svg", W = 760;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const nice = v => { const p = Math.pow(10, Math.floor(Math.log10(Math.max(v, 1)))); const f = v / p; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p; };

  /* series: [{label, color, points:[[x,y],...]}] over a shared ordered x list. Bars for one series, grouped otherwise. */
  function columns(xs, series, opts = {}) {
    const H = 240, L = 40, R = 8, T = 10, B = 34, iw = W - L - R, ih = H - T - B;
    if (!xs.length) return '<div class="empty">No data yet.</div>';
    const max = nice(Math.max(1, ...series.flatMap(s => s.points.map(p => p[1]))));
    const band = iw / xs.length, bw = Math.min(40, (band * 0.8) / series.length);
    let g = "";
    for (let i = 0; i <= 4; i++) {
      const y = T + ih - (ih * i) / 4;
      g += `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" stroke="currentColor" opacity=".12"/><text x="${L - 6}" y="${y + 4}" text-anchor="end">${Math.round((max * i) / 4).toLocaleString('en-US')}</text>`;
    }
    xs.forEach((x, i) => {
      const cx = L + band * (i + 0.5);
      series.forEach((s, k) => {
        const v = (s.points.find(p => p[0] === x) || [0, 0])[1];
        const h = (ih * v) / max, bx = cx - (bw * series.length) / 2 + k * bw;
        g += `<rect x="${bx}" y="${T + ih - h}" width="${bw - 1}" height="${h}" fill="${s.color}" rx="2"><title>${esc(x)}: ${v.toLocaleString('en-US')} (${esc(s.label)})</title></rect>`;
      });
      if (xs.length <= 12 || i % Math.ceil(xs.length / 10) === 0)
        g += `<text x="${cx}" y="${H - 14}" text-anchor="middle">${esc(opts.xFmt ? opts.xFmt(x) : x)}</text>`;
    });
    const legend = series.length > 1 ? `<div class="legend">${series.map(s => `<span><i style="background:${s.color}"></i>${esc(s.label)}</span>`).join("")}</div>` : "";
    return `${legend}<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.label || "chart")}">${g}</svg>`;
  }

  /* items: [[label, value], ...] drawn as horizontal bars */
  function hbars(items, opts = {}) {
    if (!items.length) return '<div class="empty">No data yet.</div>';
    const rowH = 24, L = 190, R = 50, H = items.length * rowH + 8, iw = W - L - R, max = Math.max(1, ...items.map(i => i[1]));
    let g = "";
    items.forEach(([label, v], i) => {
      const y = 4 + i * rowH, w = (iw * v) / max;
      g += `<text x="${L - 8}" y="${y + 15}" text-anchor="end">${esc(label.length > 30 ? label.slice(0, 29) + "…" : label)}</text>` +
        `<rect x="${L}" y="${y + 3}" width="${w}" height="${rowH - 8}" fill="${opts.color || "var(--chart)"}" rx="2"><title>${esc(label)}: ${v.toLocaleString('en-US')}</title></rect>` +
        `<text x="${L + w + 6}" y="${y + 15}">${v.toLocaleString("en-US")}</text>`;
    });
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.label || "chart")}">${g}</svg>`;
  }
  window.JWCharts = { columns, hbars };
})();
