import { call } from "./client";
import type { BrandConfig } from "@/types";

export function getBranding(): Promise<BrandConfig> {
  return call<BrandConfig>("fateh_support.api.branding.get", { method: "GET" });
}
