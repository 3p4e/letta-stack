/* DocEngine Studio service worker: network-first for API, cache-first for shell. */
const SHELL = "docengine-studio-v1";
const ASSETS = ["/", "/index.html", "/styles.css", "/app.js", "/icon.svg", "/manifest.webmanifest"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== self.location.origin) return;
  // API is never cached: a stale verdict or status must not be replayed.
  if (url.pathname.startsWith("/api") || url.pathname.startsWith("/mcp")) return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request).then((r) => r || caches.match("/index.html")))
  );
});
