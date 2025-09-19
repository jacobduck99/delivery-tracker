
// /static/sw.js

// ---- version & cache names ----
const VERSION       = 'v9'; // bump on every change
const STATIC_CACHE  = `static-${VERSION}`;
const RUNTIME_CACHE = `runtime-${VERSION}`;

// ---- static files to precache (no auth pages here) ----
const STATIC_ASSETS = [
  '/offline.html',
  '/static/manifest.webmanifest',
  '/static/css/base.css',
  '/static/css/index.css',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

// ---- helpers ----
function fetchWithSwTimeout(req, ms = 3000, opts = {}) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), ms);
  return fetch(req, { ...opts, signal: ctrl.signal }).finally(() => clearTimeout(id));
}

// ---- install: precache static assets ----
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(STATIC_CACHE).then((c) => c.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});

// ---- activate: clean old caches + enable navigation preload ----
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter((k) => k !== STATIC_CACHE && k !== RUNTIME_CACHE)
        .map((k) => caches.delete(k))
    );

    if (self.registration.navigationPreload) {
      await self.registration.navigationPreload.enable();
    }
    await self.clients.claim();
  })());
});

// ---- fetch handler ----
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle same-origin GETs
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;

  // Never intercept auth/API routes
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname === '/login' ||
    url.pathname === '/logout' ||
    url.pathname === '/signup'
  ) {
    return;
  }

  const isHTML =
    req.mode === 'navigate' ||
    req.destination === 'document' ||
    (req.headers.get('accept') || '').includes('text/html');

  // ---- Navigations: network-first (3s timeout, uses preload) -> cache -> /index -> offline.html ----
  if (isHTML) {
    event.respondWith((async () => {
      try {
        // Use navigation preload if available for faster TTFB
        const preload = await event.preloadResponse;
        const net = preload || await fetchWithSwTimeout(req, 3000, { credentials: 'include' });

        if (net.ok && net.status === 200) {
          const cache = await caches.open(RUNTIME_CACHE);

          // Cache by exact Request (keeps query)…
          await cache.put(req, net.clone());

          // …and also by normalized path for SPA route fallback
          let key = url.pathname;
          if (key === '/') key = '/index';
          if (key === '/index/') key = '/index';
          await cache.put(new Request(key), net.clone());
        }

        return net;
      } catch {
        const runtime = await caches.open(RUNTIME_CACHE);
        const staticC = await caches.open(STATIC_CACHE);

        return (
          (await runtime.match(req)) ||
          (await runtime.match(new Request(url.pathname))) ||
          (await runtime.match('/index')) ||
          (await staticC.match('/offline.html')) ||
          new Response('Offline', { status: 503 })
        );
      }
    })());
    return;
  }

  // ---- Static assets & other GETs: cache-first, then network (and stash) ----
  event.respondWith((async () => {
    const cached = await caches.match(req);
    if (cached) return cached;

    try {
      const net = await fetch(req);
      const cache = await caches.open(RUNTIME_CACHE);
      await cache.put(req, net.clone());
      return net;
    } catch {
      return new Response('', { status: 504 });
    }
  })());
});
