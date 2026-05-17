import { createApp } from "vue";
import { createPinia } from "pinia";
import router from "@/router";
import { i18n, setLocale } from "@/i18n";
import { useBrandingStore } from "@/stores/branding";
import { usePrefsStore } from "@/stores/prefs";
import App from "@/App.vue";

import "@/styles/main.css";

async function bootstrap() {
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
