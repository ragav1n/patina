// Cache-first, cache-as-you-go: every same-origin GET the app makes (the
// page shell, the Pyodide runtime, the numpy/Pillow/pillow-heif packages,
// the patina wheel) gets cached the first time it's fetched. After that
// first successful load over Wi-Fi, everything the app needs is already in
// the cache, so it keeps working with no network at all.
//
// Bump CACHE_NAME when shipping a real update so old assets don't stick
// around forever once you're back online.
const CACHE_NAME = "patina-v1";

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(req);
      if (cached) return cached;
      try {
        const response = await fetch(req);
        if (response.ok) cache.put(req, response.clone());
        return response;
      } catch (err) {
        if (cached) return cached;
        throw err;
      }
    })
  );
});
