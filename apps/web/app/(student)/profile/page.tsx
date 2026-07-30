"use client";

import { useMutation } from "@tanstack/react-query";
import { KeyRound, Send, Trash2, User } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/input";
import { Alert, Avatar, Spinner } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import { useAuth, useRequireAuth } from "@/lib/hooks/use-auth";
import { ROLE_LABELS, formatDate } from "@/lib/utils";

export default function ProfilePage() {
  const { loading, authorized } = useRequireAuth();
  const { user, refresh, logout } = useAuth();

  const [form, setForm] = React.useState({ full_name: "", phone: "", bio: "" });
  const [passwords, setPasswords] = React.useState({ current_password: "", new_password: "" });

  React.useEffect(() => {
    if (!user) return;
    setForm({ full_name: user.full_name, phone: user.phone ?? "", bio: user.bio ?? "" });
  }, [user]);

  const saveProfile = useMutation({
    mutationFn: () =>
      api.patch("/auth/me", {
        full_name: form.full_name,
        phone: form.phone || undefined,
        bio: form.bio || undefined,
      }),
    onSuccess: async () => {
      toast.success("Profil saqlandi");
      await refresh();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Saqlanmadi"),
  });

  const changePassword = useMutation({
    mutationFn: () => api.post("/auth/change-password", passwords),
    onSuccess: async () => {
      toast.success("Parol o'zgartirildi — qaytadan kirishingiz kerak");
      setPasswords({ current_password: "", new_password: "" });
      await logout();
      window.location.href = "/login";
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "O'zgartirilmadi"),
  });

  const linkTelegram = useMutation({
    mutationFn: () =>
      api.post<{ link_code: string; deep_link?: string | null; instructions: string }>(
        "/auth/telegram/link-code",
      ),
    onSuccess: (result) => {
      toast.success(`Kod: ${result.link_code}`, {
        description: result.instructions,
        duration: 12000,
      });
      if (result.deep_link) window.open(result.deep_link, "_blank", "noopener");
    },
  });

  const logoutAll = useMutation({
    mutationFn: () => api.post("/auth/logout-all"),
    onSuccess: () => {
      toast.success("Barcha qurilmalardan chiqildi");
      window.location.href = "/login";
    },
  });

  if (loading || !authorized || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="size-7" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />

      <main id="main-content" className="container-page flex-1 py-8">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* Sarlavha */}
          <div className="flex items-center gap-4 rounded-xl border bg-card p-5">
            <Avatar name={user.full_name} src={user.avatar_url} size={64} />
            <div className="min-w-0">
              <h1 className="truncate text-xl font-semibold">{user.full_name}</h1>
              <p className="truncate text-sm text-muted-foreground">{user.email}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {ROLE_LABELS[user.role]} · {formatDate(user.created_at)} dan beri
              </p>
            </div>
          </div>

          {/* Profil */}
          <section className="rounded-xl border bg-card p-6">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <User className="size-5 text-muted-foreground" /> Shaxsiy ma&apos;lumotlar
            </h2>

            <div className="mt-5 space-y-4">
              <Field label="To'liq ism" htmlFor="full_name" required>
                <Input
                  value={form.full_name}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, full_name: event.target.value }))
                  }
                />
              </Field>

              <Field label="Telefon" htmlFor="phone">
                <Input
                  value={form.phone}
                  onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
                  placeholder="+998901234567"
                />
              </Field>

              <Field label="O'zim haqimda" htmlFor="bio">
                <Textarea
                  rows={3}
                  value={form.bio}
                  onChange={(event) => setForm((prev) => ({ ...prev, bio: event.target.value }))}
                />
              </Field>

              <div className="flex justify-end">
                <Button loading={saveProfile.isPending} onClick={() => saveProfile.mutate()}>
                  Saqlash
                </Button>
              </div>
            </div>
          </section>

          {/* Telegram */}
          <section className="rounded-xl border bg-card p-6">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Send className="size-5 text-muted-foreground" /> Telegram
            </h2>

            {user.telegram_chat_id ? (
              <Alert variant="success" className="mt-4">
                Telegram ulangan — dars eslatmalari, to&apos;lov va sertifikat xabarlarini olasiz.
              </Alert>
            ) : (
              <>
                <p className="mt-3 text-sm text-muted-foreground">
                  Botni ulasangiz kunlik eslatma, to&apos;lov tasdig&apos;i va sertifikat haqida
                  xabar olasiz.
                </p>
                <Button
                  className="mt-4"
                  variant="outline"
                  loading={linkTelegram.isPending}
                  onClick={() => linkTelegram.mutate()}
                >
                  Ulanish kodini olish
                </Button>
              </>
            )}
          </section>

          {/* Xavfsizlik */}
          <section className="rounded-xl border bg-card p-6">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <KeyRound className="size-5 text-muted-foreground" /> Xavfsizlik
            </h2>

            <div className="mt-5 space-y-4">
              <Field label="Joriy parol" htmlFor="current_password" required>
                <Input
                  type="password"
                  autoComplete="current-password"
                  value={passwords.current_password}
                  onChange={(event) =>
                    setPasswords((prev) => ({ ...prev, current_password: event.target.value }))
                  }
                />
              </Field>

              <Field
                label="Yangi parol"
                htmlFor="new_password"
                hint="Kamida 8 belgi, harf va raqam"
                required
              >
                <Input
                  type="password"
                  autoComplete="new-password"
                  value={passwords.new_password}
                  onChange={(event) =>
                    setPasswords((prev) => ({ ...prev, new_password: event.target.value }))
                  }
                />
              </Field>

              <div className="flex flex-wrap justify-between gap-3">
                <Button
                  variant="outline"
                  loading={logoutAll.isPending}
                  onClick={() => logoutAll.mutate()}
                >
                  <Trash2 /> Barcha sessiyalarni yopish
                </Button>
                <Button
                  loading={changePassword.isPending}
                  disabled={!passwords.current_password || passwords.new_password.length < 8}
                  onClick={() => changePassword.mutate()}
                >
                  Parolni o&apos;zgartirish
                </Button>
              </div>
            </div>
          </section>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
