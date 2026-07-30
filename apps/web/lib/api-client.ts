
import type { ApiMessage, AuthResponse, TokenPair } from "./types";

const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const INTERNAL_BASE = process.env.INTERNAL_API_URL ?? PUBLIC_BASE;

const ACCESS_TOKEN_KEY = "zehno_access_token";
const USER_KEY = "zehno_user";

export const isServer = typeof window === "undefined";
export const apiBaseUrl = () => (isServer ? INTERNAL_BASE : PUBLIC_BASE);

export const tokenStore = {
  get(): string | null {
    if (isServer) return null;
    try {
      return window.localStorage.getItem(ACCESS_TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string | null) {
    if (isServer) return;
    try {
      if (token) window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
      else window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    } catch {
    }
  },
  getUser<T>(): T | null {
    if (isServer) return null;
    try {
      const raw = window.localStorage.getItem(USER_KEY);
      return raw ? (JSON.parse(raw) as T) : null;
    } catch {
      return null;
    }
  },
  setUser(user: unknown | null) {
    if (isServer) return;
    try {
      if (user) window.localStorage.setItem(USER_KEY, JSON.stringify(user));
      else window.localStorage.removeItem(USER_KEY);
    } catch {
    }
  },
  clear() {
    this.set(null);
    this.setUser(null);
  },
};

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  get isAuthError() {
    return this.status === 401;
  }

  get isForbidden() {
    return this.status === 403;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  auth?: boolean;
  revalidate?: number | false;
  tags?: string[];
  _retried?: boolean;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const base = apiBaseUrl().replace(/\/$/, "");
  const url = new URL(`${base}${path.startsWith("/") ? path : `/${path}`}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (isServer) return null;
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    try {
      const response = await fetch(buildUrl("/auth/refresh"), {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!response.ok) {
        tokenStore.clear();
        return null;
      }
      const tokens = (await response.json()) as TokenPair;
      tokenStore.set(tokens.access_token);
      return tokens.access_token;
    } catch {
      return null;
    } finally {
      setTimeout(() => {
        refreshPromise = null;
      }, 0);
    }
  })();

  return refreshPromise;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    body,
    query,
    auth = true,
    revalidate,
    tags,
    headers: extraHeaders,
    _retried,
    ...rest
  } = options;

  const headers = new Headers(extraHeaders as HeadersInit);
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

  if (!isFormData && body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (auth) {
    const token = tokenStore.get();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const init: RequestInit & { next?: { revalidate?: number | false; tags?: string[] } } = {
    ...rest,
    headers,
    credentials: "include",
  };

  if (body !== undefined) {
    init.body = isFormData ? (body as FormData) : JSON.stringify(body);
  }
  if (revalidate !== undefined || tags) {
    init.next = { revalidate, tags };
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), init);
  } catch (error) {
    throw new ApiError(
      0,
      "network_error",
      "Serverga ulanib bo'lmadi. Internet aloqasini tekshiring.",
      error,
    );
  }

  if (response.status === 401 && auth && !_retried && !isServer) {
    const token = await refreshAccessToken();
    if (token) {
      return request<T>(path, { ...options, _retried: true });
    }
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json().catch(() => null)
    : await response.text();

  if (!response.ok) {
    const error = (payload as { error?: { code: string; message: string; details?: unknown } })
      ?.error;
    throw new ApiError(
      response.status,
      error?.code ?? "http_error",
      error?.message ?? `So'rov muvaffaqiyatsiz (${response.status})`,
      error?.details,
    );
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PUT", body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};

export const authApi = {
  async login(login: string, password: string): Promise<AuthResponse> {
    const result = await api.post<AuthResponse>("/auth/login", { login, password }, { auth: false });
    tokenStore.set(result.tokens.access_token);
    tokenStore.setUser(result.user);
    return result;
  },

  async register(payload: {
    full_name: string;
    email: string;
    password: string;
    phone?: string;
    role?: "student" | "teacher";
    organization_name?: string;
  }): Promise<AuthResponse> {
    const result = await api.post<AuthResponse>("/auth/register", payload, { auth: false });
    tokenStore.set(result.tokens.access_token);
    tokenStore.setUser(result.user);
    return result;
  },

  async logout(): Promise<void> {
    try {
      await api.post<ApiMessage>("/auth/logout", {});
    } finally {
      tokenStore.clear();
    }
  },

  me: () => api.get<import("./types").User>("/auth/me"),
};
