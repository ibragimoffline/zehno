"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Award,
  BookOpen,
  CheckCircle2,
  Download,
  ExternalLink,
  RefreshCw,
  TrendingUp,
  Users,
} from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { StatCard } from "@/components/layout/dashboard-shell";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Alert, EmptyState, Progress, Skeleton } from "@/components/ui/misc";
import { ApiError, api, apiBaseUrl, tokenStore } from "@/lib/api-client";
import type { B2BDashboard, EmployeeProgress, Page } from "@/lib/types";
import { formatDateTime, formatRelative } from "@/lib/utils";

export default function B2BDashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["b2b-dashboard"],
    queryFn: () => api.get<B2BDashboard>("/b2b/dashboard"),
  });

  const { data: employees } = useQuery({
    queryKey: ["b2b-employees", 1],
    queryFn: () => api.get<Page<EmployeeProgress>>("/b2b/employees", { query: { per_page: 8 } }),
  });

  const [syncing, setSyncing] = React.useState(false);

  const syncNow = async () => {
    setSyncing(true);
    try {
      await api.post("/b2b/crm/sync-now");
      toast.success("Sinxronizatsiya navbatga qo'yildi");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Sinxronlanmadi");
    } finally {
      setSyncing(false);
    }
  };

  const downloadReport = () => {
    // CSV export uchun to'g'ridan-to'g'ri havola (Authorization header bilan fetch)
    const token = tokenStore.get();
    fetch(`${apiBaseUrl()}/b2b/reports/csv`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      credentials: "include",
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Hisobot yuklanmadi");
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "zehno-hisobot.csv";
        link.click();
        URL.revokeObjectURL(url);
      })
      .catch(() => toast.error("Hisobotni yuklab bo'lmadi"));
  };

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, index) => (
          <Skeleton key={index} className="h-28" />
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <EmptyState
        title="Tashkilot topilmadi"
        description="Hisobingiz hech qanday tashkilotga bog'lanmagan. Administratorga murojaat qiling."
        className="rounded-xl border"
      />
    );
  }

  const seatsLeft = data.seats_purchased ? data.seats_purchased - data.seats_used : null;

  return (
    <div className="space-y-6">
      {/* Sarlavha */}
      <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-semibold">{data.organization_name}</h2>
          <p className="text-sm text-muted-foreground">
            {data.employees_count} xodim · {data.active_courses} faol kurs
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={downloadReport}>
            <Download /> CSV hisobot
          </Button>
          {data.crm_sync_enabled ? (
            <Button size="sm" loading={syncing} onClick={syncNow}>
              <RefreshCw /> CRM sinxron
            </Button>
          ) : null}
        </div>
      </div>

      {/* KPI */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Xodimlar" value={data.employees_count} icon={Users} tone="primary" />
        <StatCard
          label="Yozilishlar"
          value={data.enrollments_total}
          hint={`${data.active_courses} kurs bo'yicha`}
          icon={BookOpen}
        />
        <StatCard
          label="O'rtacha progress"
          value={`${data.avg_progress}%`}
          icon={TrendingUp}
          tone="warning"
        />
        <StatCard
          label="Tugatganlar"
          value={data.completed_total}
          hint={`${data.certificates_total} sertifikat`}
          icon={CheckCircle2}
          tone="success"
        />
      </div>

      {/* O'rinlar (seats) */}
      {data.seats_purchased > 0 ? (
        <div className="rounded-xl border bg-card p-5">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-semibold">Litsenziya o&apos;rinlari</h3>
            <Badge variant={seatsLeft && seatsLeft > 0 ? "secondary" : "destructive"}>
              {data.seats_used} / {data.seats_purchased} band
            </Badge>
          </div>
          <Progress
            value={(data.seats_used / data.seats_purchased) * 100}
            size="lg"
            showLabel
          />
          {seatsLeft !== null ? (
            <p className="mt-2 text-sm text-muted-foreground">
              {seatsLeft > 0
                ? `${seatsLeft} ta bo'sh o'rin qoldi`
                : "Barcha o'rinlar band — qo'shimcha o'rin sotib olish uchun bog'laning"}
            </p>
          ) : null}
        </div>
      ) : null}

      {/* CRM holati */}
      {data.crm_sync_enabled ? (
        <Alert variant="success" title="CRM integratsiyasi faol">
          Oxirgi muvaffaqiyatli sinxronizatsiya:{" "}
          {data.crm_last_sync_at ? formatRelative(data.crm_last_sync_at) : "hali bo'lmagan"}
          {data.crm_last_sync_at ? ` (${formatDateTime(data.crm_last_sync_at)})` : ""}
        </Alert>
      ) : (
        <Alert variant="info" title="CRM ulanmagan">
          Bitrix24 yoki EspoCRM ulash uchun tashkilot sozlamalariga o&apos;ting — progress va
          sertifikat holati avtomatik CRM&apos;ga yozib boriladi.
        </Alert>
      )}

      {/* Xodimlar jadvali */}
      <div className="rounded-xl border bg-card">
        <div className="flex items-center justify-between border-b p-5">
          <h3 className="font-semibold">Xodimlar progressi</h3>
          <ButtonLink href="/b2b/employees" variant="ghost" size="sm">
            Barchasi <ExternalLink />
          </ButtonLink>
        </div>

        {employees && employees.items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Xodim</th>
                  <th className="px-5 py-3">Kurslar</th>
                  <th className="w-48 px-5 py-3">O&apos;rtacha progress</th>
                  <th className="px-5 py-3">Sertifikat</th>
                  <th className="px-5 py-3">Oxirgi faollik</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {employees.items.map((employee) => (
                  <tr key={employee.user_id}>
                    <td className="px-5 py-3">
                      <p className="font-medium">{employee.full_name}</p>
                      <p className="text-xs text-muted-foreground">{employee.email}</p>
                    </td>
                    <td className="px-5 py-3">
                      {employee.courses_completed} / {employee.courses_total}
                    </td>
                    <td className="px-5 py-3">
                      <Progress value={employee.avg_progress} showLabel size="sm" />
                    </td>
                    <td className="px-5 py-3">
                      {employee.certificates > 0 ? (
                        <span className="flex items-center gap-1.5 text-secondary">
                          <Award className="size-4" /> {employee.certificates}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {formatRelative(employee.last_activity)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={Users}
            title="Xodimlar hali yozilmagan"
            description="CSV fayl orqali bir vaqtda ko'p xodimni kursga yozishingiz mumkin."
            action={<ButtonLink href="/b2b/enroll">Kursga yozish</ButtonLink>}
          />
        )}
      </div>
    </div>
  );
}
