export function isNative(): boolean {
  try {
    return !!window.Capacitor && window.Capacitor.isNativePlatform?.() === true;
  } catch {
    return false;
  }
}

export function apiBase(): string {
  // Web: same-origin, cookies used. Native: read from VITE_API_BASE at build time.
  if (isNative()) {
    return (import.meta.env.VITE_API_BASE as string | undefined) || "";
  }
  return "";
}

export function fatehGlobal() {
  // Frappe template renders `window.FatehBoot = {...}`. The `__FATEH__` form
  // is the legacy name kept for backwards compatibility.
  return (window as any).FatehBoot || window.__FATEH__ || {};
}
