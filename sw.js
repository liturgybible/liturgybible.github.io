const CACHE_NAME = 'liturgy-bible-v1';
const ASSETS_TO_CACHE = [
    './',
    './index.html',
    './today.html',
    './today-full.html',
    './style.css',
    './script.js',
    './images/liturgy-Bible-horiz.png',
    './images/lb.png',
    './images/favicon_io/android-chrome-512x512.png',
    './images/favicon_io/apple-touch-icon.png',
    './images/favicon_io/favicon-32x32.png',
    './images/favicon_io/favicon-16x16.png',
    './images/favicon_io/site.webmanifest',
    './data_usccb/daily-links.json'
];

// Install Event - Pre-cache core assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('Opened cache');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// Activate Event - Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch Event - Stale-While-Revalidate Strategy
self.addEventListener('fetch', (event) => {
    // Only handle GET requests
    if (event.request.method !== 'GET') return;

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            const fetchPromise = fetch(event.request).then((networkResponse) => {
                // Only cache valid successful responses
                if (networkResponse && networkResponse.status === 200) {
                    const responseToCache = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseToCache);
                    });
                }
                return networkResponse;
            }).catch(() => {
                // If network fails, return cached response if available
                return cachedResponse;
            });

            // Return cached response immediately if it exists, otherwise wait for network
            return cachedResponse || fetchPromise;
        })
    );
});
