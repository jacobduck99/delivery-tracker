
// DEV SW: never cache, always fetch fresh
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return; // let POSTs pass through
  event.respondWith(fetch(event.request));
});
