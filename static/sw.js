
// Version your cache so you can invalidate old files on deploy
const VERSION = 'v1';
const STATIC_CACHE = `static-${VERSION}`;

// Files to make available offline (your "app shell")
const APP_SHELL = [
  '/',             // home (redirects to /index for authed users)
  '/index',        // main UI
  '/configuration',// run setup
  '/offline.html'  // simple offline page
];

// Install: pre-cache the app shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(APP_SHELL))
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

// Fetch: 
// 1) For page navigations (HTML), try network first, fall back to offline page.
// 2) For everything else, just let the network happen for now (simple).
self.addEventListener('fetch', event => {
  const req = event.request;

  // Only handle GET requests
  if (req.method !== 'GET') return;

  // If this is a navigation (the browser asking for an HTML page)
  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        // Try the live network
        return await fetch(req);
      } catch {
        // If offline, show the offline page we cached
        const cache = await caches.open(STATIC_CACHE);
        const offline = await cache.match('/offline.html');
        return offline || new Response('Offline', { status: 503 });
      }
    })());
  }
});
