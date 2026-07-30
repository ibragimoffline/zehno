"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Send, User } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/input";
import { Alert } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import { useAuth } from "@/lib/hooks/use-auth";
import type { Organization, User as UserType } from "@/lib/types";

export default function TeacherSettingsPage() {
  const { user, refresh } = useAuth();
  const queryClient = useQueryClient();

  const [profile, setProfile] = React.useState({
    full_name: user?.full_name ?? "",
    phone: user?.phone ?? "",
    bio: user?.bio ?? "",
    avatar_url: user?.avatar_url ?? "",
  });

  React.useEffect(() => {
    if (!user) return;
    setProfile({
      full_name: user.full_name,
      phone: user.phone ?? "",
      bio: user.bio ?? "",
      avatar_url: user.avatar_url ?? "",
    });
  }, [user]);

  const { data: organization } = useQuery({
    queryKey: ["my-organization"],
    queryFn: () => api.get<Organization>("/organizations/me"),
    retry: false,
  });

  const [orgForm, setOrgForm] = React.useState({ name: "", contact_email: "", website: "" });

  React.useEffect(() => {
    if (!organization) return;
    setOrgForm({
      name: organization.name,
      contact_email: organization.contact_email ?? "",
      website: organization.website ?? "",
    });
  }, [organization]);

  const saveProfile = useMutation({
    mutationFn: () =>
      api.patch<UserType>("/auth/me", {
        full_name: profile.full_name,
        phone: profile.phone || undefined,
        bio: profile.bio || undefined,
        avatar_url: profile.avatar_url || undefined,
      }),
    onSuccess: async () => {
      toast.success("Profil saqlandi");
      await refresh();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Saqlanmadi"),
  });

  const saveOrg = useMutation({
    mutationFn: () =>
      api.patch<Organization>(`/organizations/${organization?.id}`, {
        name: orgForm.name,
        contact_email: orgForm.contact_email || undefined,
        website: orgForm.website || undefined,
      }),
    onSuccess: async () => {
      toast.success("Tashkilot ma'lumotlari saqlandi");
      await queryClient.invalidateQueries({ queryKey: ["my-organization"] });
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Saqlanmadi"),
  });

  const linkTelegram = useMutation({
    mutationFn: () =>
      api.post<{ link_code: string; deep_link?: string | null; instructions: string }>(
        "/auth/telegram/link-code",
      ),
    onSuccess: (result) => {
      toast.success(`Kod: ${result.link_code}`, { description: result.instructions, duration: 12000 });
      if (result.deep_link) window.open(result.deep_link, "_blank", "noopener");
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Xatolik"),
  });

  return (
    <div className="max-w-2xl space-y-6">
      {/* Profil */}
      <section className="rounded-xl border bg-card p-6">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <User className="size-5 text-muted-foreground" /> Profil
        </h2>

        <div className="mt-5 space-y-4">
          <Field label="To'liq ism" htmlFor="p-name" required>
            <Input
              value={profile.full_name}
              onChange={(event) =>
                setProfile((prev) => ({ ...prev, full_name: event.target.value }))
              }
            />
          </Field>

          <Field label="Telefon" htmlFor="p-phone">
            <Input
              value={profile.phone}
              onChange={(event) => setProfile((prev) => ({ ...prev, phone: event.target.value }))}
              placeholder="+998901234567"
            />
          </Field>

          <Field
            label="Bio"
            htmlFor="p-bio"
            hint="Kurs sahifasidagi «Ustoz haqida» blokida ko'rinadi"
          >
            <Textarea
              rows={4}
              value={profile.bio}
              onChange={(event) => setProfile((prev) => ({ ...prev, bio: event.target.value }))}
            />
          </Field>

          <Field label="Avatar havolasi" htmlFor="p-avatar">
            <Input
              value={profile.avatar_url}
              onChange={(event) =>
                setProfile((prev) => ({ ...prev, avatar_url: event.target.value }))
              }
              placeholder="https://..."
            />
          </Field>

          <div className="flex justify-end">
            <Button loading={saveProfile.isPending} onClick={() => saveProfile.mutate()}>
              Saqlash
            </Button>
          </div>
        </div>
      </section>

      {/* Tashkilot */}
      {organization ? (
        <section className="rounded-xl border bg-card p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold">
            <Building2 className="size-5 text-muted-foreground" /> Tashkilot
          </h2>

          <div className="mt-5 space-y-4">
            <Field label="Nomi" htmlFor="o-name" required>
              <Input
                value={orgForm.name}
                onChange={(event) => setOrgForm((prev) => ({ ...prev, name: event.target.value }))}
              />
            </Field>

            <Field label="Aloqa emaili" htmlFor="o-email">
              <Input
                type="email"
                value={orgForm.contact_email}
                onChange={(event) =>
                  setOrgForm((prev) => ({ ...prev, contact_email: event.target.value }))
                }
              />
            </Field>

            <Field label="Veb-sayt" htmlFor="o-website">
              <Input
                value={orgForm.website}
                onChange={(event) =>
                  setOrgForm((prev) => ({ ...prev, website: event.target.value }))
                }
                placeholder="https://..."
              />
            </Field>

            <div className="flex justify-end">
              <Button loading={saveOrg.isPending} onClick={() => saveOrg.mutate()}>
                Saqlash
              </Button>
            </div>
          </div>
        </section>
      ) : null}

      {/* Telegram */}
      <section className="rounded-xl border bg-card p-6">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <Send className="size-5 text-muted-foreground" /> Telegram bildirishnomalar
        </h2>

        {user?.telegram_chat_id ? (
          <Alert variant="success" className="mt-4">
            Telegram hisobingiz ulangan — sotuv, moderatsiya va payout xabarlarini shu yerda olasiz.
          </Alert>
        ) : (
          <>
            <p className="mt-3 text-sm text-muted-foreground">
              Botni ulasangiz: yangi sotuv, kurs moderatsiyasi natijasi va payout holati haqida
              darhol xabar olasiz.
            </p>
            <Button
              className="mt-4"
              variant="outline"
              loading={linkTelegram.isPending}
              onClick={() => linkTelegram.mutate()}
            >
              <Send /> Ulanish kodini olish
            </Button>
          </>
        )}
      </section>
    </div>
  );
}
