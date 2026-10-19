// App assets only; never store user documents.
const CACHE = "wordcraft-pwa-__BUILD_VERSION__";
const PRECACHE = __PRECACHE_ASSETS__;
const assetUrls = new Set(PRECACHE.map(asset => new URL(asset, self.registration.scope).href));
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key =>
    key.startsWith("wordcraft-pwa-") && key !== CACHE).map(key => caches.delete(key))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (!url.href.startsWith(self.registration.scope) || url.origin !== self.location.origin) return;
  if (url.search || /\.(docx?|odt|rtf|pdf|txt|md|html)$/i.test(url.pathname)) return;
  const navigation = event.request.mode === "navigate";
  if (!navigation && !assetUrls.has(url.href)) return;
  event.respondWith(navigation
    ? fetch(event.request).catch(() => caches.match("./index.html"))
    : caches.match(event.request).then(hit => hit || fetch(event.request)));
});
