"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save, Sliders, ToggleLeft } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { Alert, EmptyState, Skeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";

interface SystemSetting {
  key: string;
  value: Record<string, unknown> | null;
  description?: string | null;
  is_public: boolean;
}

export default function AdminSettingsPage() {
  const queryClient = useQueryClient();

  const { data = [], isLoading } = useQuery({
    queryKey: ["admin-settings"],
    queryFn: () => api.get<SystemSetting[]>("/admin/settings"),
  });

  const save = useMutation({
    mutationFn: (payload: SystemSetting) =>
      api.put("/admin/settings", {
        key: payload.key,
        value: payload.value ?? {},
        description: payload.description,
        is_public: payload.is_public,
      }),
    onSuccess: async () => {
      toast.success("Sozlama saqlandi");
      await queryClient.invalidateQueries({ queryKey: ["admin-settings"] });
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Saqlanmadi"),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-40" />
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <EmptyState
        icon={Sliders}
        title="Sozlamalar topilmadi"
        description="Seed skripti ishga tushirilganda boshlang'ich sozlamalar yaratiladi."
        className="rounded-xl border bg-card"
      />
    );
  }

  return (
    <div className="max-w-3xl space-y-5">
      <Alert variant="info" title="Diqqat">
        Bu bo&apos;limdagi qiymatlar platforma xatti-harakatiga bevosita ta&apos;sir qiladi
        (komissiya foizi, feature flaglar). O&apos;zgartirishlar darhol kuchga kiradi.
      </Alert>

      {data.map((setting) => (
        <SettingCard key={setting.key} setting={setting} onSave={(next) => save.mutate(next)} />
      ))}
    </div>
  );
}

function SettingCard({
  setting,
  onSave,
}: {
  setting: SystemSetting;
  onSave: (setting: SystemSetting) => void;
}) {
  const [value, setValue] = React.useState<Record<string, unknown>>(setting.value ?? {});

  const entries = Object.entries(value);
  const isFlags = entries.every(([, item]) => typeof item === "boolean");

  return (
    <div className="rounded-xl border bg-card p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="flex items-center gap-2 font-semibold">
            <code className="font-mono text-sm">{setting.key}</code>
            {setting.is_public ? <Badge variant="muted">ochiq</Badge> : null}
          </h2>
          {setting.description ? (
            <p className="mt-0.5 text-sm text-muted-foreground">{setting.description}</p>
          ) : null}
        </div>

        <Button size="sm" onClick={() => onSave({ ...setting, value })}>
          <Save /> Saqlash
        </Button>
      </div>

      {isFlags ? (
        <div className="grid gap-2 sm:grid-cols-2">
          {entries.map(([key, flag]) => (
            <label
              key={key}
              className="flex cursor-pointer items-center justify-between gap-3 rounded-lg border p-3 text-sm"
            >
              <span className="flex items-center gap-2">
                <ToggleLeft className="size-4 text-muted-foreground" />
                <code className="font-mono text-xs">{key}</code>
              </span>
              <input
                type="checkbox"
                checked={Boolean(flag)}
                onChange={(event) =>
                  setValue((prev) => ({ ...prev, [key]: event.target.checked }))
                }
                className="size-4 accent-primary"
              />
            </label>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {entries.map(([key, item]) => (
            <Field key={key} label={key} htmlFor={`${setting.key}-${key}`}>
              <Input
                value={
                  typeof item === "object" && item !== null
                    ? JSON.stringify(item)
                    : String(item ?? "")
                }
                onChange={(event) => {
                  const raw = event.target.value;
                  const parsed =
                    typeof item === "number" && raw !== "" && !Number.isNaN(Number(raw))
                      ? Number(raw)
                      : raw;
                  setValue((prev) => ({ ...prev, [key]: parsed }));
                }}
              />
            </Field>
          ))}
        </div>
      )}
    </div>
  );
}
