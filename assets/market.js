/* Market report numbers. Pure functions of the history rows; every number on market.html comes from here. */
(function () {
  const dayNum = d => { const [y, m, dd] = d.split("-").map(Number); return Date.UTC(y, m - 1, dd) / 86400000; };
  const countBy = (rows, key) => { const m = new Map(); rows.forEach(r => { const k = key(r); if (k) m.set(k, (m.get(k) || 0) + 1); }); return m; };
  const sortedEntries = m => [...m.entries()].sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0);
  function median(a) { if (!a.length) return null; const s = [...a].sort((x, y) => x - y), n = s.length; return n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2; }

  function compute(rows) {
    let lastRun = ""; rows.forEach(r => { if (r.last_seen > lastRun) lastRun = r.last_seen; });
    const notFirst = rows.filter(r => !r.first_run);
    const open = rows.filter(r => r.status === "open");
    const removed = rows.filter(r => r.status === "removed");
    const daysOpen = removed.filter(r => !r.first_run).map(r => dayNum(r.removed_date) - dayNum(r.first_seen));
    const cohort = notFirst.filter(r => lastRun && dayNum(lastRun) - dayNum(r.first_seen) >= 7);
    const quick = cohort.filter(r => r.status === "removed" && dayNum(r.removed_date) - dayNum(r.first_seen) <= 7);
    const locs = [...countBy(open, r => r.location).entries()].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1)).slice(0, 10);
    const emps = [...countBy(open, r => r.employer).entries()].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
    return {
      lastRun,
      newAll: sortedEntries(countBy(notFirst, r => r.first_seen)),
      newRole: sortedEntries(countBy(notFirst.filter(r => r.in_role), r => r.first_seen)),
      removedPerDay: sortedEntries(countBy(removed, r => r.removed_date)),
      openByEmployer: emps,
      daysOpen: { n: daysOpen.length, median: median(daysOpen), values: daysOpen },
      quick: { cohort: cohort.length, removedWithin7: quick.length, share: cohort.length ? quick.length / cohort.length : null },
      topLocations: locs,
    };
  }
  window.JWMarket = { compute, median };
})();
