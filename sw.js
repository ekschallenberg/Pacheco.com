/* Service worker: app shell is cached for offline use; data files are network-first so they stay fresh,
   falling back to the last copy that loaded when the computer is offline. */
const VERSION = "v1";
const SHELL = `shell-${VERSION}`, DATA = `data-${VERSION}`;
const SHELL_FILES = ["./", "index.html", "browse.html", "market.html", "manifest.webmanifest",
  "assets/style.css", "assets/app.js", "assets/market.js", "assets/charts.js", "assets/icon-192.png", "assets/icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => ![SHELL, DATA].includes(k)).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  const isData = new URL(req.url).pathname.includes("/data/");
  e.respondWith((async () => {
    const cache = await caches.open(isData ? DATA : SHELL);
    if (isData) {
      try { const r = await fetch(req); if (r.ok) cache.put(req, r.clone()); return r; }
      catch (err) { const hit = await cache.match(req); if (hit) return hit; throw err; }
    }
    // shell: network first (so deploys show up), cached copy when offline
    try { const r = await fetch(req); if (r.ok) cache.put(req, r.clone()); return r; }
    catch (err) { return (await cache.match(req)) || (await cache.match("index.html")); }
  })());
});
