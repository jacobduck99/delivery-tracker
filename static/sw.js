
// /static/sw.js

// ---- version & cache names ----
const VERSION       = 'v8';                  // bump on every change
const STATIC_CACHE  = `static-${VERSION}`;
const RUNTIME_CACHE = `runtime-${VERSION}`;

// ---- static files to precache (no auth pages here) ----
// Don't precache /index (it may redirect to /login). We'll cache it at runtime.
const STATIC_ASSETS = [
  '/offline.html',
  '/static/manifest.webmanifest',
  '/static/css/base.css',
  '/static/css/index.css',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

// ---- install: precache static assets ----
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(STATIC_CACHE).then((c) => c.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});

// ---- activate: clean old caches ----
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== STATIC_CACHE && k !== RUNTIME_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
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

  // ---- Navigations: network-first, then runtime cache, then offline.html ----
  if (isHTML) {
    event.respondWith(
      (async () => {
        try {
          const net = await fetch(req, { credentials: 'include' });

          // Only cache successful (200 OK) pages; ignore redirects
          if (net.ok && net.status === 200) {
            const cache = await caches.open(RUNTIME_CACHE);

            // Normalize keys so DevTools shows /index nicely
            let key = url.pathname;
            if (key === '/') key = '/index';
            if (key === '/index/') key = '/index';

            await cache.put(key, net.clone());
          }

          return net;
        } catch {
          // Offline path: try exact path in runtime, then /index, then offline.html
          const runtime = await caches.open(RUNTIME_CACHE);
          const staticC = await caches.open(STATIC_CACHE);

          return (
            (await runtime.match(url.pathname)) ||
            (await runtime.match('/index')) ||
            (await staticC.match('/offline.html')) ||
            new Response('Offline', { status: 503 })
          );
        }
      })()
    );
    return;
  }

  // ---- Static assets & other GETs: cache-first, then network (and stash) ----
  event.respondWith(
    (async () => {
      const cached = await caches.match(req);
      if (cached) return cached;

      try {
        const net = await fetch(req);
        const copy = net.clone();
        const cache = await caches.open(RUNTIME_CACHE);
        cache.put(req, copy);
        return net;
      } catch {
        // No cached asset & network failed
        return new Response('', { status: 504 });
      }
    })()
  );
});
