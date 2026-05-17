import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useBrandingStore } from "@/stores/branding";

vi.mock("@/api/branding", () => ({
  getBranding: vi.fn(async () => ({
    brand_name: "RMAX Trading",
    brand_primary_color: "#ff0000",
    brand_secondary_color: "#000000",
    brand_logo: "https://example.com/logo.png",
    vapid_public_key: "",
  })),
}));

describe("branding store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    document.documentElement.removeAttribute("style");
    document.title = "";
  });

  it("applies CSS variables from server response", async () => {
    const branding = useBrandingStore();
    await branding.load();
    expect(branding.loaded).toBe(true);
    expect(document.documentElement.style.getPropertyValue("--brand-primary")).toBe("#ff0000");
    expect(document.documentElement.style.getPropertyValue("--brand-logo-url")).toContain("logo.png");
    expect(document.title).toBe("RMAX Trading");
  });
});
