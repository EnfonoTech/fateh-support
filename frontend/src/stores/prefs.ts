import { defineStore } from "pinia";

const LOCALE_KEY = "fateh.locale";

interface State {
  locale: "en" | "ar";
}

function initialLocale(): "en" | "ar" {
  try {
    const stored = localStorage.getItem(LOCALE_KEY);
    if (stored === "ar" || stored === "en") return stored;
  } catch {
    /* ignore */
  }
  return "en";
}

export const usePrefsStore = defineStore("prefs", {
  state: (): State => ({ locale: initialLocale() }),
  getters: {
    dir: (s) => (s.locale === "ar" ? "rtl" : "ltr"),
  },
  actions: {
    setLocale(locale: "en" | "ar") {
      this.locale = locale;
      try {
        localStorage.setItem(LOCALE_KEY, locale);
      } catch {
        /* ignore */
      }
      document.documentElement.setAttribute("lang", locale);
      document.documentElement.setAttribute("dir", locale === "ar" ? "rtl" : "ltr");
    },
    apply() {
      this.setLocale(this.locale);
    },
    toggle() {
      this.setLocale(this.locale === "ar" ? "en" : "ar");
    },
  },
});
