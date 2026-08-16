import { apiBase, fatehGlobal } from "@/utils/platform";

const CRED_KEY = "fateh.token";

interface Creds {
  apiKey: string;
  apiSecret: string;
}

let _cachedCreds: Creds | null = null;

export function setCredentials(creds: Creds | null): void {
  _cachedCreds = creds;
  try {
    if (creds) {
      localStorage.setItem(CRED_KEY, JSON.stringify(creds));
    } else {
      localStorage.removeItem(CRED_KEY);
    }
  } catch {
    /* ignore */
  }
}

export function getCredentials(): Creds | null {
  if (_cachedCreds) return _cachedCreds;
  try {
    const raw = localStorage.getItem(CRED_KEY);
    if (raw) {
      _cachedCreds = JSON.parse(raw) as Creds;
      return _cachedCreds;
    }
  } catch {
    /* ignore */
  }
  return null;
}

// Token learned at runtime (from login / auth.csrf). Wins over everything
// else, because Frappe rotates the session — and therefore the token — on
// login, which leaves the value baked into the page at render time dead.
let _csrfToken: string | null = null;

export function setCsrfToken(token: string | null | undefined): void {
  if (token) _csrfToken = token;
}

/** Drop the learned token — logout rotates the session and invalidates it. */
export function clearCsrfToken(): void {
  _csrfToken = null;
}

function getCsrfToken(): string | null {
  if (_csrfToken) return _csrfToken;
  const m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  if (m) return decodeURIComponent(m[1]);
  const g = fatehGlobal();
  return g.csrf_token || null;
}

/** Ask the server for the current session's token. GET → never CSRF-gated. */
async function refreshCsrfToken(): Promise<boolean> {
  try {
    // Must carry the session cookie. Omitting it made the server answer as
    // Guest and hand back a Guest token, so the replay failed exactly like
    // the original request — two 400s a second apart, and no way out of it.
    const res = await fetch(buildUrl("fateh_support.api.auth.csrf"), {
      method: "GET",
      headers: { Accept: "application/json" },
      credentials: "include",
    });
    if (!res.ok) return false;
    const data = (await res.json()) as { message?: { csrf_token?: string } };
    const token = data?.message?.csrf_token;
    if (!token || token === _csrfToken) return false;
    _csrfToken = token;
    return true;
  } catch {
    return false;
  }
}

function isCsrfFailure(status: number, payload: unknown): boolean {
  if (status !== 400) return false;
  const p = (payload || {}) as Record<string, unknown>;
  if (p.exc_type === "CSRFTokenError") return true;
  return JSON.stringify(p).includes("CSRFToken");
}

function buildUrl(method: string): string {
  const base = apiBase();
  return `${base}/api/method/${method}`;
}

/**
 * Send whatever credentials we actually hold — never branch on "native".
 *
 * The Android shell is a remote-URL WebView, so it authenticates with the
 * same session cookie as a browser tab and needs the same CSRF header. The
 * old code assumed native meant API-key auth, returned only an Authorization
 * header, and fell back to `{}` when no key was stored — so every POST from
 * the APK went out with no CSRF token and Frappe answered 400.
 *
 * Sending both is safe: Frappe ignores the CSRF header on token-authenticated
 * requests, and ignores the Authorization header when it isn't set.
 */
function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};

  const creds = getCredentials();
  if (creds) headers.Authorization = `token ${creds.apiKey}:${creds.apiSecret}`;

  const csrf = getCsrfToken();
  if (csrf) headers["X-Frappe-CSRF-Token"] = csrf;

  return headers;
}

export interface CallOptions {
  method?: "GET" | "POST";
  params?: Record<string, unknown>;
  body?: unknown;
  signal?: AbortSignal;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function buildQuery(params?: Record<string, unknown>): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  if (!entries.length) return "";
  return "?" + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join("&");
}

function stripHtml(s: string): string {
  return s
    .replace(/<\/?[^>]+(>|$)/g, "")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\s+/g, " ")
    .trim();
}

function cleanExceptionLine(s: string): string {
  // "frappe.exceptions.ValidationError: ..." -> "..."
  const m = /:\s*(.+)$/s.exec(s);
  if (m) return m[1].trim();
  return s.trim();
}

function parseFrappeError(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "Request failed";
  const p = payload as Record<string, unknown>;

  // 1. Try _server_messages first — usually the user-facing text
  if (Array.isArray(p._server_messages)) {
    try {
      const msgs = (p._server_messages as string[])
        .map((raw) => {
          try {
            const obj = JSON.parse(raw) as { message?: string };
            return obj.message || raw;
          } catch {
            return raw;
          }
        })
        .map((m) => stripHtml(String(m)))
        .filter(Boolean);
      if (msgs.length) return msgs.join(" • ");
    } catch {
      /* ignore */
    }
  }

  // 2. Exception line
  if (typeof p.exception === "string" && p.exception.trim()) {
    return cleanExceptionLine(stripHtml(p.exception));
  }

  // 3. Plain message
  if (typeof p.message === "string") return stripHtml(p.message);

  return "Request failed";
}

export async function call<T = unknown>(method: string, opts: CallOptions = {}): Promise<T> {
  const httpMethod = opts.method || "POST";
  const url = httpMethod === "GET" ? buildUrl(method) + buildQuery(opts.params) : buildUrl(method);

  const attempt = async (): Promise<{ res: Response; data: unknown }> => {
    const headers: Record<string, string> = {
      Accept: "application/json",
      ...authHeaders(),
    };
    const fetchInit: RequestInit = {
      method: httpMethod,
      headers,
      signal: opts.signal,
    };
    // The APK is a remote-URL WebView on the same origin as the API, so it
    // relies on the session cookie exactly as a browser tab does.
    fetchInit.credentials = "include";
    if (httpMethod === "POST") {
      headers["Content-Type"] = "application/json";
      fetchInit.body = JSON.stringify(opts.body ?? opts.params ?? {});
    }

    let res: Response;
    try {
      res = await fetch(url, fetchInit);
    } catch (err) {
      // Network error, offline, CORS reject, service-worker abort, etc.
      const raw = (err as Error)?.message || "";
      throw new ApiError(raw ? `Network error: ${raw}` : "Network error. Check your connection.", 0);
    }
    let data: unknown = null;
    try {
      data = await res.json();
    } catch {
      /* response not JSON — fall through */
    }
    return { res, data };
  };

  let { res, data } = await attempt();

  // A 400 on an unsafe method is Frappe's CSRF rejection. The token we hold
  // goes stale the moment the session rotates (login above all), and nothing
  // pushes the new one to us — so fetch a fresh one and replay once. If the
  // token came back unchanged this was a genuine 400; don't retry.
  if (!res.ok && httpMethod === "POST" && (isCsrfFailure(res.status, data) || res.status === 400)) {
    if (await refreshCsrfToken()) {
      ({ res, data } = await attempt());
    }
  }

  if (!res.ok) {
    const msg = parseFrappeError(data) || `HTTP ${res.status}`;
    throw new ApiError(msg, res.status);
  }
  return (data as { message: T } | null)?.message as T;
}

export function logout(): void {
  setCredentials(null);
}
