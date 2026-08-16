// Fateh Trading service worker.
//
// Served as a real static file from `www/` so it arrives with a JavaScript
// MIME type and a root path. Both matter:
//
//   * A browser refuses to register a worker served as octet-stream, which is
//     what Frappe's binary response returns no matter what Content-Type the
//     endpoint sets — the dynamic `api.pwa.sw` endpoint could never have been
//     registered even once it stopped crashing.
//   * A worker may only claim a scope at or below its own path. Living at the
//     site root gives it a max scope of `/`, so it can claim `/fateh/` with
//     no Service-Worker-Allowed header at all.
//
// The filename deliberately avoids the substring `sw.js`. damage_pwa ships a
// global `after_request` hook that stamps `Service-Worker-Allowed:
// /damage-pwa/` onto ANY response whose path contains `/sw` or `sw.js` — so a
// worker named `fateh-sw.js` got another app's scope bolted onto it and was
// refused. Renaming is the change that touches only this app; the substring
// match in damage_pwa is the real defect and will bite the next PWA too.
//
// Nothing here needs the VAPID key: the page subscribes (it reads the key from
// window.FatehBoot) and this worker only renders what the server pushes.

self.BRAND_NAME = "Fateh Trading";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (err) {
    data = { body: event.data ? event.data.text() : "" };
  }
  const title = data.title || self.BRAND_NAME;
  const opts = {
    body: data.body || "",
    icon: data.icon || "/assets/fateh_support/frontend/icons/icon-192.png",
    badge: "/assets/fateh_support/frontend/icons/icon-192.png",
    data: data.data || {},
    tag: data.tag || "fateh_support",
  };
  event.waitUntil(self.registration.showNotification(title, opts));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || "/fateh/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const c of clients) {
        if ("focus" in c) {
          c.navigate(target);
          return c.focus();
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(target);
    })
  );
});
