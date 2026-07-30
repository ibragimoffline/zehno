"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { ApiError, authApi, tokenStore } from "@/lib/api-client";
import type { User, UserRole } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (login: string, password: string) => Promise<User>;
  register: (payload: {
    full_name: string;
    email: string;
    password: string;
    phone?: string;
    role?: "student" | "teacher";
    organization_name?: string;
  }) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  hasRole: (...roles: UserRole[]) => boolean;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const cached = tokenStore.getUser<User>();
    if (cached) setUser(cached);

    let cancelled = false;
    (async () => {
      try {
        const fresh = await authApi.me();
        if (!cancelled) {
          setUser(fresh);
          tokenStore.setUser(fresh);
        }
      } catch (error) {
        if (!cancelled && error instanceof ApiError && error.isAuthError) {
          tokenStore.clear();
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = React.useCallback(async (loginValue: string, password: string) => {
    const result = await authApi.login(loginValue, password);
    setUser(result.user);
    return result.user;
  }, []);

  const register = React.useCallback<AuthContextValue["register"]>(async (payload) => {
    const result = await authApi.register(payload);
    setUser(result.user);
    return result.user;
  }, []);

  const logout = React.useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  const refresh = React.useCallback(async () => {
    try {
      const fresh = await authApi.me();
      setUser(fresh);
      tokenStore.setUser(fresh);
    } catch {
      setUser(null);
    }
  }, []);

  const hasRole = React.useCallback(
    (...roles: UserRole[]) => (user ? roles.includes(user.role) : false),
    [user],
  );

  const value = React.useMemo(
    () => ({ user, loading, login, register, logout, refresh, hasRole }),
    [user, loading, login, register, logout, refresh, hasRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth faqat <AuthProvider> ichida ishlatiladi");
  }
  return context;
}

export function useRequireAuth(roles?: UserRole[], redirectTo = "/login") {
  const { user, loading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (loading) return;
    if (!user) {
      const next = typeof window !== "undefined" ? window.location.pathname : "/";
      router.replace(`${redirectTo}?next=${encodeURIComponent(next)}`);
      return;
    }
    if (roles && roles.length > 0 && !roles.includes(user.role)) {
      router.replace("/403");
    }
  }, [user, loading, roles, router, redirectTo]);

  return { user, loading, authorized: Boolean(user && (!roles || roles.includes(user.role))) };
}
