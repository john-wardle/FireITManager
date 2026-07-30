const cacheName = "fireit-mobile-shell-v3";
const shellFiles = [
    "/mobile/",
    "/mobile/index.html",
    "/mobile/styles.css",
    "/mobile/app.js",
    "/mobile/manifest.webmanifest",
    "/mobile/icon.svg"
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(cacheName)
            .then((cache) => cache.addAll(shellFiles))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(keys
                .filter((key) => key !== cacheName)
                .map((key) => caches.delete(key))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (event) => {
    const request = event.request;
    const url = new URL(request.url);

    if (request.method !== "GET" || !url.pathname.startsWith("/mobile/")) {
        return;
    }

    event.respondWith(
        caches.match(request)
            .then((cached) => cached ?? fetch(request)
                .then((response) => {
                    const copy = response.clone();
                    caches.open(cacheName).then((cache) => cache.put(request, copy));
                    return response;
                }))
            .catch(() => caches.match("/mobile/index.html"))
    );
});
