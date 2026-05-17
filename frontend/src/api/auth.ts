import { call, setCredentials } from "./client";
import type { Profile } from "@/types";

/**
 * Login uses Frappe's standard `/api/method/login` endpoint — works for both
 * the web PWA AND the Capacitor native shell when the shell loads the live
 * site via `server.url`. Cookies are stored by the WebView same as a browser
 * tab, so no PIN / API-key dance is needed.
 *
 * The legacy `auth.pin_login` flow (token auth) stays available on the
 * server for a future air-gapped Capacitor build with bundled webDir.
 */
export async function login(email: string, password: string): Promise<Profile> {
  await call("login", { body: { usr: email, pwd: password } });
  return me();
}

export async function me(): Promise<Profile> {
  return call<Profile>("fateh_support.api.auth.me", { method: "GET" });
}

export async function ping(): Promise<{ user: string; ts: string }> {
  return call("fateh_support.api.auth.ping", { method: "GET" });
}

export async function logout(): Promise<void> {
  try {
    await call("fateh_support.api.auth.logout");
  } catch {
    /* ignore */
  }
  setCredentials(null);
}
