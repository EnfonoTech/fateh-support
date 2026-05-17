import { apiBase, fatehGlobal, isNative } from "@/utils/platform";

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

function getCsrfToken(): string | null {
  // Cookie wins — Frappe rotates the value on login/logout, and a stale
  // server-injected token fails CSRF on every subsequent request.
  const m = document.cookie.match(/csrf_token=([^;]+)/);
  if (m) return decodeURIComponent(m[1]);
  const g = fatehGlobal();
  return g.csrf_token || null;
}

function buildUrl(method: string): string {
  const base = apiBase();
  return `${base}/api/method/${method}`;
}

function authHeaders(): Record<string, string> {
  if (isNative()) {
    const c = getCredentials();
    return c ? { Authorization: `token ${c.apiKey}:${c.apiSecret}` } : {};
  }
  const csrf = getCsrfToken();
  return csrf ? { "X-Frappe-CSRF-Token": csrf } : {};
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
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...authHeaders(),
  };
  const fetchInit: RequestInit = {
    method: httpMethod,
    headers,
    signal: opts.signal,
  };
  if (!isNative()) {
    fetchInit.credentials = "include";
  }
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
  if (!res.ok) {
    const msg = parseFrappeError(data) || `HTTP ${res.status}`;
    throw new ApiError(msg, res.status);
  }
  return (data as { message: T } | null)?.message as T;
}

export function logout(): void {
  setCredentials(null);
}
