// Sribuu PWA Service Worker v1.1 — with Notification Support
const CACHE_NAME = 'sribuu-v2';

// Assets to cache immediately on install
const PRECACHE_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/pwa/icon-192.png',
  '/static/pwa/icon-512.png',
];

// Install: cache core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: network-first, fallback to cache
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip API calls (always fresh)
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache successful responses
        if (response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, clone);
          });
        }
        return response;
      })
      .catch(() => {
        // Offline: serve from cache
        return caches.match(event.request).then((cached) => {
          return cached || new Response('Offline', { status: 503 });
        });
      })
  );
});

// ── Push Notification: Receive push from server ──
self.addEventListener('push', (event) => {
  if (!event.data) return;

  try {
    const data = event.data.json();
    const title = data.title || 'Sribuu';
    const options = {
      body: data.body || '',
      icon: '/static/pwa/icon-192.png',
      badge: '/static/pwa/icon-192.png',
      vibrate: [200, 100, 200],
      data: data.data || {},
      actions: data.actions || [],
      requireInteraction: true,
    };

    event.waitUntil(
      self.registration.showNotification(title, options)
    );
  } catch (e) {
    console.warn('SW: Failed to show push notification', e);
  }
});

// ── Show Notification (from client-side) ──
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    const { title, body, tag, data } = event.data.payload || {};
    self.registration.showNotification(title || 'Sribuu', {
      body: body || '',
      icon: '/static/pwa/icon-192.png',
      badge: '/static/pwa/icon-192.png',
      vibrate: [200, 100, 200],
      tag: tag || 'sribuu-notification',
      data: data || {},
      requireInteraction: true,
    });
  }
});

// ── Notification Click: Open app ──
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const urlToOpen = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      // If already open, focus the window
      for (const client of windowClients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(urlToOpen);
          return client.focus();
        }
      }
      // Otherwise open new window
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});
