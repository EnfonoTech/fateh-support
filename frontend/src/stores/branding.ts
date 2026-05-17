import { defineStore } from "pinia";
import { getBranding } from "@/api/branding";
import { fatehGlobal } from "@/utils/platform";
import type { BrandConfig } from "@/types";
import { setDefaultCurrency } from "@/utils/format";

interface State {
  config: BrandConfig;
  loaded: boolean;
}

function defaultConfig(): BrandConfig {
  const g = fatehGlobal();
  return {
    brand_name: g.brand?.name || "Fateh Trading",
    brand_primary_color: g.brand?.primary || "#2563EB",
    brand_secondary_color: "#334155",
    vapid_public_key: g.vapid_public_key,
    default_currency: "SAR",
  };
}

export const useBrandingStore = defineStore("branding", {
  state: (): State => ({ config: defaultConfig(), loaded: false }),
  actions: {
    apply() {
      const root = document.documentElement;
      root.style.setProperty("--brand-primary", this.config.brand_primary_color);
      root.style.setProperty("--brand-secondary", this.config.brand_secondary_color);
      if (this.config.brand_logo) {
        root.style.setProperty("--brand-logo-url", `url("${this.config.brand_logo}")`);
      }
      document.title = this.config.brand_name;
      if (this.config.default_currency) {
        setDefaultCurrency(this.config.default_currency);
      }
    },
    async load() {
      try {
        this.config = { ...this.config, ...(await getBranding()) };
        this.loaded = true;
        this.apply();
      } catch {
        this.apply();
      }
    },
  },
});
