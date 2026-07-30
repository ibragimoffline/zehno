"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, EmptyState, Pagination, TableSkeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { B2BDashboard, CrmSyncLog, Page } from "@/lib/types";
import { formatDateTime, formatRelative } from "@/lib/utils";

const EVENT_LABELS: Record<string, string> = {
  enrollment_created: "Yangi yozilish",
  progress_updated: "Progress yangilandi",
  contact_sync: "Kontakt sinxroni",
  company_sync: "Kompaniya sinxroni",
};

const STATUS_LABELS: Record<string, string> = {
  success: "Muvaffaqiyatli",
  failed: "Xatolik",
  pending: "Kutilmoqda",
};

export default function B2BCrmPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = React.useState(1);

  const { data: dashboard } = useQuery({
    queryKey: ["b2b-dashboard"],
    queryFn: () => api.get<B2BDashboard>("/b2b/dashboard"),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["crm-logs", page],
    queryFn: () => api.get<Page<CrmSyncLog>>("/b2b/crm/logs", { query: { page, per_page: 25 } }),
  });

  const sync = useMutation({
    mutationFn: () => api.post("/b2b/crm/sync-now"),
    onSuccess: async () => {
      toast.success("Sinxronizatsiya navbatga qo'yildi");
      setTimeout(() => queryClient.invalidateQueries({ queryKey: ["crm-logs"] }), 2500);
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Xatolik"),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">CRM sinxronizatsiyasi</h2>
          <p className="text-sm text-muted-foreground">
            Talabalar progressi CRM&apos;dagi Contact kartochkasiga yozib boriladi
          </p>
        </div>

        <Button
          loading={sync.isPending}
          disabled={!dashboard?.crm_sync_enabled}
          onClick={() => sync.mutate()}
        >
          <RefreshCw /> Hozir sinxronlash
        </Button>
      </div>

      {dashboard?.crm_sync_enabled ? (
        <Alert variant="success" title="Integratsiya faol">
          Oxirgi muvaffaqiyatli sinxron:{" "}
          {dashboard.crm_last_sync_at
            ? `${formatRelative(dashboard.crm_last_sync_at)} (${formatDateTime(dashboard.crm_last_sync_at)})`
            : "hali bo'lmagan"}
        </Alert>
      ) : (
        <Alert variant="warning" title="CRM ulanmagan">
          Tashkilot sozlamalarida <code className="font-mono">crm_sync_enabled</code> ni yoqib,
          Bitrix24 webhook URL yoki EspoCRM API kalitini kiritish kerak. Backend `.env` da{" "}
          <code className="font-mono">CRM_PROVIDER=bitrix24</code> bo&apos;lishi shart.
        </Alert>
      )}

      {isLoading ? (
        <TableSkeleton rows={8} cols={5} />
      ) : data && data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border bg-card">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Hodisa</th>
                  <th className="px-5 py-3">Provayder</th>
                  <th className="px-5 py-3">Holat</th>
                  <th className="px-5 py-3">Tashqi ID</th>
                  <th className="px-5 py-3">Vaqt</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((log) => (
                  <tr key={log.id}>
                    <td className="px-5 py-3">{EVENT_LABELS[log.event_type] ?? log.event_type}</td>
                    <td className="px-5 py-3 font-mono text-xs">{log.provider}</td>
                    <td className="px-5 py-3">
                      <StatusBadge
                        status={log.status}
                        label={STATUS_LABELS[log.status] ?? log.status}
                      />
                      {log.error_message ? (
                        <p className="mt-1 line-clamp-2 text-xs text-destructive">
                          {log.error_message}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs text-muted-foreground">
                      {log.external_id ?? "—"}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {formatDateTime(log.synced_at ?? log.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination page={data.page} pages={data.pages} onChange={setPage} />
        </>
      ) : (
        <EmptyState
          icon={RefreshCw}
          title="Sinxronizatsiya loglari yo'q"
          description="CRM ulangandan keyin har bir hodisa shu yerda qayd etiladi."
          className="rounded-xl border bg-card"
        />
      )}
    </div>
  );
}
