import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { usePrefsStore } from "@/stores/prefs";

describe("prefs store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    document.documentElement.setAttribute("dir", "ltr");
    document.documentElement.setAttribute("lang", "en");
  });

  it("defaults to english", () => {
    const prefs = usePrefsStore();
    expect(prefs.locale).toBe("en");
    expect(prefs.dir).toBe("ltr");
  });

  it("toggles to arabic and flips dir", () => {
    const prefs = usePrefsStore();
    prefs.toggle();
    expect(prefs.locale).toBe("ar");
    expect(document.documentElement.dir).toBe("rtl");
    expect(localStorage.getItem("fateh.locale")).toBe("ar");
  });

  it("apply persists and updates html attributes", () => {
    const prefs = usePrefsStore();
    prefs.setLocale("ar");
    prefs.apply();
    expect(document.documentElement.lang).toBe("ar");
    expect(document.documentElement.dir).toBe("rtl");
  });
});
