// Two reasons this worker precaches an explicit file list on install instead
// of relying only on "cache whatever gets fetched":
//
// 1. The page shell (index.html, app.js, this file, the classic
//    <script src="vendor/pyodide/pyodide.js"> tag) is fetched as part of the
//    very first navigation, before registration (which only happens on the
//    page's "load" event) has even started. A service worker can't
//    retroactively intercept requests that happened before it existed.
//
// 2. Pyodide resolves its own runtime files and any package named by string
//    (numpy, Pillow, pillow-heif, and their transitive deps cffi/pycparser)
//    against its lock file using its own internal loader, not the page's
//    fetch(). Verified by testing: none of those ever show up in Cache
//    Storage even after the page reports "Ready" and idling well past that,
//    while a package loaded by direct URL (the patina wheel) is caught fine.
//    So the runtime fetch handler below genuinely cannot see requests for
//    anything in this list; the only way to get them offline-ready is to
//    fetch them ourselves.
//
// If the vendored Pyodide/numpy/Pillow/pillow-heif versions are ever
// upgraded, this list needs updating to match the new filenames.
//
// Bump CACHE_NAME when shipping a real update so old assets don't stick
// around forever once you're back online.
const CACHE_NAME = "patina-v3";
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./app.js",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./pkg/manifest.json",
  "./vendor/pyodide/pyodide.js",
  "./vendor/pyodide/pyodide.mjs",
  "./vendor/pyodide/pyodide.asm.mjs",
  "./vendor/pyodide/pyodide.asm.wasm",
  "./vendor/pyodide/pyodide-lock.json",
  "./vendor/pyodide/python_stdlib.zip",
  "./vendor/pyodide/numpy-2.4.6-cp314-cp314-pyemscripten_2026_0_wasm32.whl",
  "./vendor/pyodide/pillow-12.2.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl",
  "./vendor/pyodide/pillow_heif-1.3.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl",
  "./vendor/pyodide/cffi-2.0.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl",
  "./vendor/pyodide/pycparser-3.0-py3-none-any.whl",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)));
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
        // Large assets (the wasm runtime, the numpy/Pillow wheels) can take
        // real time to write into Cache Storage. Without waitUntil, the
        // browser is free to suspend this worker the instant the response
        // above is handed back to the page, silently dropping the write
        // before it finishes, so the asset never actually ends up cached.
        if (response.ok) event.waitUntil(cache.put(req, response.clone()));
        return response;
      } catch (err) {
        if (cached) return cached;
        throw err;
      }
    })
  );
});
