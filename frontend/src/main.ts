import { createApp } from "vue";
import { createPinia } from "pinia";
import router from "@/router";
import { i18n, setLocale } from "@/i18n";
import { useBrandingStore } from "@/stores/branding";
import { usePrefsStore } from "@/stores/prefs";
import App from "@/App.vue";

import "@/styles/main.css";

const RELOAD_GUARD = "fateh.chunk-reload";

/**
 * Recover from a stale entry bundle.
 *
 * The entry is served under a stable `index.js` name, so a cached copy can
 * outlive the chunk hashes it imports. When that happens every dynamic import
 * 404s and the app dies on boot. One forced reload refetches the entry and
 * fixes it; the sessionStorage guard stops that turning into a reload loop if
 * the failure is something else.
 */
function isChunkLoadFailure(reason: unknown): boolean {
  const message = String((reason as Error)?.message || reason || "");
  return (
    message.includes("Failed to fetch dynamically imported module") ||
    message.includes("error loading dynamically imported module") ||
    message.includes("Importing a module script failed")
  );
}

function installChunkReloadGuard(): void {
  window.addEventListener("unhandledrejection", (event) => {
    if (!isChunkLoadFailure(event.reason)) return;
    try {
      if (sessionStorage.getItem(RELOAD_GUARD)) return;
      sessionStorage.setItem(RELOAD_GUARD, "1");
    } catch {
      return; // no storage, no guard — better to show the error than loop
    }
    event.preventDefault();
    location.reload();
  });

  window.addEventListener("load", () => {
    try {
      sessionStorage.removeItem(RELOAD_GUARD);
    } catch {
      /* ignore */
    }
  });
}

async function bootstrap() {
  installChunkReloadGuard();

  const app = createApp(App);
  const pinia = createPinia();
  app.use(pinia);
  app.use(router);
  app.use(i18n);

  const prefs = usePrefsStore();
  prefs.apply();
  setLocale(prefs.locale);

  const branding = useBrandingStore();
  branding.apply();
  void branding.load();

  app.mount("#app");
}

void bootstrap();
