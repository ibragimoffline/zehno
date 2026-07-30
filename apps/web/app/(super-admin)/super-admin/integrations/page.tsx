"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  CreditCard,
  Database,
  Plug,
  RefreshCw,
  Users,
  Video,
} from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, EmptyState, TableSkeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { IntegrationHealth, IntegrationKind, IntegrationStatus } from "@/lib/types";
import { formatRelative } from "@/lib/utils";

const KIND_ICONS: Record<IntegrationKind, React.ComponentType<{ className?: string }>> = {
  video: Video,
  payment: CreditCard,
  crm: Users,
  notification: Bell,
  storage: Database,
};

const KIND_LABELS: Record<IntegrationKind, string> = {
  video: "Video hosting",
  payment: "To'lov tizimi",
  crm: "CRM",
  notification: "Bildirishnoma",
  storage: "Fayl saqlash",
};

const HEALTH_LABELS: Record<IntegrationHealth, string> = {
  ok: "Faol",
  degraded: "Sekinlashgan",
  error: "Xatolik",
  disabled: "O'chirilgan",
};

const HEALTH_DOT: Record<IntegrationHealth, string> = {
  ok: "bg-secondary",
  degraded: "bg-accent-500",
  error: "bg-destructive",
  disabled: "bg-muted-foreground",
};

export default function IntegrationsPage() {
  const queryClient = useQueryClient();

  const { data = [], isLoading } = useQuery({
    queryKey: ["admin-integrations"],
    queryFn: () => api.get<IntegrationStatus[]>("/admin/integrations"),
    refetchInterval: 60_000,
  });

  const healthcheck = useMutation({
    mutationFn: () => api.post<IntegrationStatus[]>("/admin/integrations/healthcheck"),
    onSuccess: async (result) => {
      const failed = result.filter((item) => item.health === "error").length;
      if (failed > 0) toast.warning(`${failed} ta integratsiyada xatolik aniqlandi`);
      else toast.success("Barcha integratsiyalar tekshirildi");
      await queryClient.invalidateQueries({ queryKey: ["admin-integrations"] });
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.message : "Tekshirib bo'lmadi"),
  });

  const problems = data.filter((item) => item.health === "error");

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Integratsiyalar monitoringi</h2>
          <p className="text-sm text-muted-foreground">
            Har bir tashqi xizmat adapter orqali ulanadi — `.env` dagi provayderni almashtirish
            biznes-logikani o&apos;zgartirmaydi
          </p>
        </div>

        <Button loading={healthcheck.isPending} onClick={() => healthcheck.mutate()}>
          <RefreshCw /> Hammasini tekshirish
        </Button>
      </div>

      {problems.length > 0 ? (
        <Alert variant="error" title={`${problems.length} ta integratsiyada xatolik`}>
          <ul className="mt-1.5 space-y-0.5 text-sm">
            {problems.map((item) => (
              <li key={item.provider}>
                • <strong>{item.display_name}</strong>: {item.last_error_message ?? "noma'lum xato"}
              </li>
            ))}
          </ul>
        </Alert>
      ) : null}

      {isLoading ? (
        <TableSkeleton rows={5} cols={5} />
      ) : data.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border bg-card">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-5 py-3">Integratsiya</th>
                <th className="px-5 py-3">Turi</th>
                <th className="px-5 py-3">Holat</th>
                <th className="px-5 py-3">Oxirgi muvaffaqiyat</th>
                <th className="px-5 py-3">Xatolik</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.map((item) => {
                const Icon = KIND_ICONS[item.kind] ?? Plug;
                return (
                  <tr key={item.provider}>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2.5">
                        <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                          <Icon className="size-4 text-muted-foreground" />
                        </span>
                        <div>
                          <p className="font-medium">{item.display_name}</p>
                          <p className="font-mono text-xs text-muted-foreground">
                            {item.provider}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {KIND_LABELS[item.kind] ?? item.kind}
                    </td>
                    <td className="px-5 py-3">
                      <span className="flex items-center gap-2">
                        <span
                          className={`size-2.5 rounded-full ${HEALTH_DOT[item.health]}`}
                          aria-hidden
                        />
                        {HEALTH_LABELS[item.health]}
                        {item.consecutive_failures > 0 ? (
                          <Badge variant="destructive">{item.consecutive_failures}×</Badge>
                        ) : null}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {item.last_success_at ? formatRelative(item.last_success_at) : "—"}
                    </td>
                    <td className="max-w-xs px-5 py-3">
                      {item.last_error_message ? (
                        <span className="line-clamp-2 text-xs text-destructive">
                          {item.last_error_message}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          icon={Plug}
          title="Integratsiyalar topilmadi"
          description="Adapterlar `.env` sozlamalari asosida yuklanadi."
          className="rounded-xl border bg-card"
        />
      )}

      <Alert variant="info" title="Provayderni qanday almashtirish">
        <code className="font-mono text-xs">
          VIDEO_PROVIDER=peertube | kinescope | bunny &nbsp;·&nbsp; PAYMENT_PROVIDER=payme | click
          &nbsp;·&nbsp; CRM_PROVIDER=bitrix24 | espocrm
        </code>
        <p className="mt-1.5 text-xs text-muted-foreground">
          `.env` faylini o&apos;zgartirib API konteynerini qayta ishga tushirish yetarli.
        </p>
      </Alert>
    </div>
  );
}
