"use client";

import { useQuery } from "@tanstack/react-query";
import { FileClock, ShieldQuestion } from "lucide-react";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { EmptyState, Pagination, TableSkeleton, Tabs } from "@/components/ui/misc";
import { api } from "@/lib/api-client";
import type { Page } from "@/lib/types";
import { COURSE_STATUS_LABELS, formatDateTime } from "@/lib/utils";

interface ModerationLogRow {
  id: string;
  action: string;
  from_status?: string | null;
  to_status?: string | null;
  comment?: string | null;
  actor_id?: string | null;
  created_at: string;
}

interface AuditLogRow {
  id: string;
  actor_id?: string | null;
  actor_email?: string | null;
  action: string;
  entity_type?: string | null;
  entity_id?: string | null;
  created_at: string;
}

const ACTION_LABELS: Record<string, string> = {
  submit: "Moderatsiyaga yuborildi",
  approve: "Tasdiqlandi",
  reject: "Rad etildi",
  archive: "Arxivlandi",
};

export default function AdminLogsPage() {
  const [tab, setTab] = React.useState("moderation");
  const [page, setPage] = React.useState(1);

  const moderation = useQuery({
    queryKey: ["moderation-logs", page],
    queryFn: () =>
      api.get<Page<ModerationLogRow>>("/admin/moderation/logs", {
        query: { page, per_page: 25 },
      }),
    enabled: tab === "moderation",
  });

  const audit = useQuery({
    queryKey: ["audit-logs", page],
    queryFn: () => api.get<Page<AuditLogRow>>("/admin/audit-logs", { query: { page, per_page: 25 } }),
    enabled: tab === "audit",
  });

  return (
    <div className="space-y-5">
      <Tabs
        active={tab}
        onChange={(id) => {
          setTab(id);
          setPage(1);
        }}
        tabs={[
          { id: "moderation", label: "Moderatsiya loglari" },
          { id: "audit", label: "Audit log" },
        ]}
      />

      {tab === "moderation" ? (
        moderation.isLoading ? (
          <TableSkeleton rows={8} cols={4} />
        ) : moderation.data && moderation.data.items.length > 0 ? (
          <>
            <div className="overflow-x-auto rounded-xl border bg-card">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-5 py-3">Amal</th>
                    <th className="px-5 py-3">Holat o&apos;zgarishi</th>
                    <th className="px-5 py-3">Izoh</th>
                    <th className="px-5 py-3">Vaqt</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {moderation.data.items.map((row) => (
                    <tr key={row.id}>
                      <td className="px-5 py-3">
                        <Badge
                          variant={
                            row.action === "approve"
                              ? "success"
                              : row.action === "reject"
                                ? "destructive"
                                : "muted"
                          }
                        >
                          {ACTION_LABELS[row.action] ?? row.action}
                        </Badge>
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">
                        {COURSE_STATUS_LABELS[row.from_status ?? ""] ?? row.from_status ?? "—"} →{" "}
                        {COURSE_STATUS_LABELS[row.to_status ?? ""] ?? row.to_status ?? "—"}
                      </td>
                      <td className="max-w-md px-5 py-3">
                        <span className="line-clamp-2 text-muted-foreground">
                          {row.comment ?? "—"}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">
                        {formatDateTime(row.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Pagination
              page={moderation.data.page}
              pages={moderation.data.pages}
              onChange={setPage}
            />
          </>
        ) : (
          <EmptyState
            icon={ShieldQuestion}
            title="Moderatsiya loglari yo'q"
            className="rounded-xl border bg-card"
          />
        )
      ) : audit.isLoading ? (
        <TableSkeleton rows={8} cols={4} />
      ) : audit.data && audit.data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border bg-card">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Amal</th>
                  <th className="px-5 py-3">Kim</th>
                  <th className="px-5 py-3">Obyekt</th>
                  <th className="px-5 py-3">Vaqt</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {audit.data.items.map((row) => (
                  <tr key={row.id}>
                    <td className="px-5 py-3 font-mono text-xs">{row.action}</td>
                    <td className="px-5 py-3">{row.actor_email ?? "—"}</td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {row.entity_type ? `${row.entity_type}:${row.entity_id ?? ""}` : "—"}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {formatDateTime(row.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination page={audit.data.page} pages={audit.data.pages} onChange={setPage} />
        </>
      ) : (
        <EmptyState
          icon={FileClock}
          title="Audit loglari yo'q"
          description="Admin harakatlari shu yerda qayd etiladi."
          className="rounded-xl border bg-card"
        />
      )}
    </div>
  );
}
