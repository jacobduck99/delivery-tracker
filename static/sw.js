
// Version your cache so you can invalidate old files on deploy
const VERSION = 'v2';
const STATIC_CACHE = `static-${VERSION}`;

// ✅ Precache only immutable/static assets (no auth pages, no redirects)
const STATIC_ASSETS = [
  '/offline.html',
  '/static/css/base.css',
  // add your other static files: icons, JS bundles, fonts, manifest, etc.
  // e.g. '/static/icons/icon-192.png', '/static/icons/icon-512.png',
  // '/static/manifest.webmanifest'
];

// Install: pre-cache static assets only
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate: delete old caches when VERSION changes
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== STATIC_CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch strategy:
// - Only handle GETs
// - Navigations (HTML): network-first, offline fallback
// - Everything else: pass-through or cache-first for STATIC_ASSETS
self.addEventListener('fetch', event => {
  const req = event.request;

  // 1) Only handle GET requests
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const isHTML = req.mode === 'navigate' ||
    (req.headers.get('accept') || '').includes('text/html');

  // 2) Don’t touch auth/API endpoints at all (extra safety)
  const bypass = ['/login', '/signup', '/logout', '/api/']
    .some(p => url.pathname.startsWith(p));
  if (bypass) return;

  // 3) Navigations: network-first -> offline fallback
  if (isHTML) {
    event.respondWith((async () => {
      try {
        return await fetch(req);
      } catch {
        const cache = await caches.open(STATIC_CACHE);
        return (await cache.match('/offline.html')) || new Response('Offline', { status: 503 });
      }
    })());
    return;
  }

  // 4) Static assets: cache-first for speed (optional)
  event.respondWith((async () => {
    const cached = await caches.match(req);
    if (cached) return cached;
    const res = await fetch(req);
    // Optionally cache new static responses
    const copy = res.clone();
    caches.open(STATIC_CACHE).then(c => c.put(req, copy));
    return res;
  })());
});


