"use client";

import { Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { Alert } from "@/components/ui/misc";
import { ApiError } from "@/lib/api-client";
import { useAuth } from "@/lib/hooks/use-auth";

function LoginForm() {
  const { login, user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next");

  const [form, setForm] = React.useState({ login: "", password: "" });
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (user) router.replace(next || destinationFor(user.role));
  }, [user, next, router]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const authenticated = await login(form.login.trim(), form.password);
      toast.success(`Xush kelibsiz, ${authenticated.full_name}!`);
      router.push(next || destinationFor(authenticated.role));
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "Kirishda xatolik yuz berdi. Qayta urinib ko'ring.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl">Tizimga kirish</h1>
      <p className="mt-1.5 text-sm text-muted-foreground">
        Hisobingiz yo&apos;qmi?{" "}
        <Link href="/register" className="font-medium text-primary hover:underline">
          Ro&apos;yxatdan o&apos;ting
        </Link>
      </p>

      {error ? (
        <Alert variant="error" className="mt-5">
          {error}
        </Alert>
      ) : null}

      <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
        <Field label="Email yoki telefon" htmlFor="login" required>
          <Input
            name="login"
            autoComplete="username"
            placeholder="siz@example.com"
            value={form.login}
            onChange={(event) => setForm((prev) => ({ ...prev, login: event.target.value }))}
            required
          />
        </Field>

        <Field label="Parol" htmlFor="password" required>
          <div className="relative">
            <Input
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder="••••••••"
              className="pr-10"
              value={form.password}
              onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1.5 text-muted-foreground hover:text-foreground"
              aria-label={showPassword ? "Parolni yashirish" : "Parolni ko'rsatish"}
            >
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
        </Field>

        <div className="flex justify-end">
          <Link href="/forgot-password" className="text-sm text-primary hover:underline">
            Parolni unutdingizmi?
          </Link>
        </div>

        <Button type="submit" full size="lg" loading={loading}>
          Kirish
        </Button>
      </form>

      <div className="mt-8 rounded-lg border border-dashed p-4">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Demo hisoblar (seed)
        </p>
        <ul className="space-y-1 font-mono text-xs text-muted-foreground">
          <li>talaba@zehno.uz / Talaba12345!</li>
          <li>ustoz@zehno.uz / Ustoz12345!</li>
          <li>hr@demotech.uz / Manager12345!</li>
          <li>admin@zehno.uz / Admin12345!</li>
        </ul>
      </div>
    </div>
  );
}

function destinationFor(role: string): string {
  switch (role) {
    case "admin":
      return "/super-admin";
    case "teacher":
    case "org_admin":
      return "/teacher/courses";
    case "b2b_manager":
      return "/b2b/dashboard";
    default:
      return "/dashboard";
  }
}

export default function LoginPage() {
  return (
    <React.Suspense fallback={<div className="h-64 animate-pulse rounded-xl bg-muted" />}>
      <LoginForm />
    </React.Suspense>
  );
}
