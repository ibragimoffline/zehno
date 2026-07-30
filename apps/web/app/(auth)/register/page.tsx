"use client";

import { Eye, EyeOff, GraduationCap, User } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { Alert } from "@/components/ui/misc";
import { ApiError } from "@/lib/api-client";
import { useAuth } from "@/lib/hooks/use-auth";
import { cn } from "@/lib/utils";

type Role = "student" | "teacher";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();

  const [role, setRole] = React.useState<Role>("student");
  const [form, setForm] = React.useState({
    full_name: "",
    email: "",
    phone: "",
    password: "",
    organization_name: "",
  });
  const [showPassword, setShowPassword] = React.useState(false);
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const validate = () => {
    const next: Record<string, string> = {};
    if (form.full_name.trim().length < 2) next.full_name = "Ism kamida 2 belgidan iborat bo'lsin";
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email)) next.email = "Email formati noto'g'ri";
    if (form.password.length < 8) next.password = "Parol kamida 8 belgidan iborat bo'lsin";
    else if (!/\d/.test(form.password) || !/[a-zA-Z]/.test(form.password)) {
      next.password = "Parolda kamida bitta harf va bitta raqam bo'lishi kerak";
    }
    if (form.phone && !/^\+?\d{9,15}$/.test(form.phone.replace(/[\s\-()]/g, ""))) {
      next.phone = "Masalan: +998901234567";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!validate()) return;

    setLoading(true);
    try {
      const user = await register({
        full_name: form.full_name.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        phone: form.phone.trim() || undefined,
        role,
        organization_name:
          role === "teacher" && form.organization_name.trim()
            ? form.organization_name.trim()
            : undefined,
      });
      toast.success("Ro'yxatdan o'tdingiz! Xush kelibsiz.");
      router.push(user.role === "student" ? "/dashboard" : "/teacher/courses");
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Ro'yxatdan o'tishda xatolik yuz berdi. Qayta urinib ko'ring.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl">Ro&apos;yxatdan o&apos;tish</h1>
      <p className="mt-1.5 text-sm text-muted-foreground">
        Hisobingiz bormi?{" "}
        <Link href="/login" className="font-medium text-primary hover:underline">
          Kirish
        </Link>
      </p>

      {/* Rol tanlash */}
      <div className="mt-5 grid grid-cols-2 gap-2" role="radiogroup" aria-label="Rol tanlash">
        {(
          [
            { value: "student", label: "O'quvchiman", icon: User },
            { value: "teacher", label: "Ustozman", icon: GraduationCap },
          ] as const
        ).map((option) => (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={role === option.value}
            onClick={() => setRole(option.value)}
            className={cn(
              "flex flex-col items-center gap-2 rounded-xl border p-4 text-sm font-medium transition-colors",
              role === option.value
                ? "border-primary bg-primary/5 text-primary"
                : "hover:bg-muted",
            )}
          >
            <option.icon className="size-5" />
            {option.label}
          </button>
        ))}
      </div>

      {error ? (
        <Alert variant="error" className="mt-5">
          {error}
        </Alert>
      ) : null}

      <form onSubmit={submit} className="mt-5 space-y-4" noValidate>
        <Field label="To'liq ism" htmlFor="full_name" error={errors.full_name} required>
          <Input
            name="full_name"
            autoComplete="name"
            placeholder="Aziz Karimov"
            value={form.full_name}
            onChange={(event) => setForm((prev) => ({ ...prev, full_name: event.target.value }))}
            required
          />
        </Field>

        <Field label="Email" htmlFor="email" error={errors.email} required>
          <Input
            name="email"
            type="email"
            autoComplete="email"
            placeholder="siz@example.com"
            value={form.email}
            onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            required
          />
        </Field>

        <Field
          label="Telefon"
          htmlFor="phone"
          error={errors.phone}
          hint="Ixtiyoriy — to'lov va eslatmalar uchun"
        >
          <Input
            name="phone"
            type="tel"
            autoComplete="tel"
            placeholder="+998 90 123 45 67"
            value={form.phone}
            onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
          />
        </Field>

        {role === "teacher" ? (
          <Field
            label="O'quv markaz / maktab nomi"
            htmlFor="organization_name"
            hint="Ixtiyoriy — jamoa bilan ishlaydigan bo'lsangiz"
          >
            <Input
              name="organization_name"
              placeholder="Zehno Academy"
              value={form.organization_name}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, organization_name: event.target.value }))
              }
            />
          </Field>
        ) : null}

        <Field
          label="Parol"
          htmlFor="password"
          error={errors.password}
          hint="Kamida 8 belgi, harf va raqam"
          required
        >
          <div className="relative">
            <Input
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
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

        <Button type="submit" full size="lg" loading={loading}>
          {role === "teacher" ? "Ustoz sifatida boshlash" : "Ro'yxatdan o'tish"}
        </Button>
      </form>
    </div>
  );
}
