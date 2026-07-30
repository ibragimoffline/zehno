"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Award,
  BookOpen,
  Building2,
  DollarSign,
  GraduationCap,
  ShieldQuestion,
  TrendingUp,
  UserPlus,
  Users,
  Wallet,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { StatCard } from "@/components/layout/dashboard-shell";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState, Skeleton } from "@/components/ui/misc";
import { api } from "@/lib/api-client";
import type { ActivityItem, PlatformKpi, RevenuePoint } from "@/lib/types";
import { formatCompact, formatNumber, formatPrice, formatRelative } from "@/lib/utils";

const ACTIVITY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  user_registered: UserPlus,
  course_created: BookOpen,
  order_paid: DollarSign,
};

export default function SuperAdminDashboard() {
  const { data: kpi, isLoading } = useQuery({
    queryKey: ["admin-kpi"],
    queryFn: () => api.get<PlatformKpi>("/admin/dashboard"),
  });

  const { data: revenue = [] } = useQuery({
    queryKey: ["admin-revenue"],
    queryFn: () => api.get<RevenuePoint[]>("/admin/dashboard/revenue", { query: { days: 30 } }),
  });

  const { data: activity = [] } = useQuery({
    queryKey: ["admin-activity"],
    queryFn: () => api.get<ActivityItem[]>("/admin/dashboard/activity", { query: { limit: 12 } }),
  });

  const chartData = revenue.map((point) => ({
    date: point.date.slice(5),
    revenue: Number(point.revenue),
    commission: Number(point.commission),
  }));

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 8 }).map((_, index) => (
          <Skeleton key={index} className="h-28" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Jami daromad"
          value={formatCompact(kpi?.revenue_total)}
          hint={`bu oy: ${formatCompact(kpi?.revenue_month)}`}
          icon={DollarSign}
          tone="success"
        />
        <StatCard
          label="Platforma komissiyasi"
          value={formatCompact(kpi?.commission_total)}
          icon={Wallet}
          tone="primary"
        />
        <StatCard
          label="Foydalanuvchilar"
          value={formatNumber(kpi?.users_total)}
          hint={`+${kpi?.users_new_week ?? 0} bu hafta`}
          icon={Users}
          tone="primary"
        />
        <StatCard
          label="Konversiya"
          value={`${kpi?.conversion_percent ?? 0}%`}
          hint="to'langan / jami buyurtma"
          icon={TrendingUp}
          tone="warning"
        />
        <StatCard
          label="Faol talabalar"
          value={formatNumber(kpi?.students_active)}
          icon={GraduationCap}
        />
        <StatCard
          label="Nashr etilgan kurslar"
          value={formatNumber(kpi?.courses_published)}
          hint={`${kpi?.courses_pending ?? 0} moderatsiyada`}
          icon={BookOpen}
        />
        <StatCard
          label="Tashkilotlar"
          value={formatNumber(kpi?.organizations_total)}
          hint={`${kpi?.teachers_total ?? 0} ustoz`}
          icon={Building2}
        />
        <StatCard
          label="Sertifikatlar"
          value={formatNumber(kpi?.certificates_total)}
          hint={`${kpi?.completions_total ?? 0} kurs tugatilgan`}
          icon={Award}
          tone="success"
        />
      </div>

      {(kpi?.courses_pending ?? 0) > 0 || (kpi?.pending_payouts ?? 0) > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {(kpi?.courses_pending ?? 0) > 0 ? (
            <div className="flex items-center justify-between gap-3 rounded-xl border border-accent/40 bg-accent/10 p-5">
              <div className="flex items-center gap-3">
                <ShieldQuestion className="size-5 shrink-0 text-accent-foreground" />
                <div>
                  <p className="font-semibold">{kpi?.courses_pending} kurs moderatsiyada</p>
                  <p className="text-sm text-muted-foreground">Ko&apos;rib chiqish kutilmoqda</p>
                </div>
              </div>
              <ButtonLink href="/super-admin/moderation" size="sm">
                Ko&apos;rish
              </ButtonLink>
            </div>
          ) : null}

          {(kpi?.pending_payouts ?? 0) > 0 ? (
            <div className="flex items-center justify-between gap-3 rounded-xl border border-primary/40 bg-primary/10 p-5">
              <div className="flex items-center gap-3">
                <Wallet className="size-5 shrink-0 text-primary" />
                <div>
                  <p className="font-semibold">{kpi?.pending_payouts} payout so&apos;rovi</p>
                  <p className="text-sm text-muted-foreground">Tasdiqlash kutilmoqda</p>
                </div>
              </div>
              <ButtonLink href="/super-admin/finance" size="sm">
                Ko&apos;rish
              </ButtonLink>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
        <div className="rounded-xl border bg-card p-5">
          <h2 className="mb-4 text-lg font-semibold">Daromad (30 kun)</h2>

          {chartData.length > 0 ? (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    stroke="hsl(var(--muted-foreground))"
                    tickFormatter={(value) => formatCompact(value)}
                  />
                  <Tooltip
                    formatter={(value: number) => formatPrice(value)}
                    contentStyle={{
                      borderRadius: 10,
                      border: "1px solid hsl(var(--border))",
                      background: "hsl(var(--card))",
                      fontSize: 13,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="revenue" name="Daromad" fill="#2563EB" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="commission" name="Komissiya" fill="#10B981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState
              icon={TrendingUp}
              title="Hali to'lovlar yo'q"
              description="Birinchi to'lovdan keyin grafik shu yerda ko'rinadi."
            />
          )}
        </div>

        <div className="rounded-xl border bg-card">
          <div className="border-b p-5">
            <h2 className="text-lg font-semibold">So&apos;nggi faoliyat</h2>
          </div>

          <ul className="max-h-[22rem] divide-y overflow-y-auto scrollbar-thin">
            {activity.length > 0 ? (
              activity.map((item, index) => {
                const Icon = ACTIVITY_ICONS[item.type] ?? BookOpen;
                return (
                  <li key={`${item.type}-${index}`} className="flex items-start gap-3 p-4">
                    <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                      <Icon className="size-4 text-muted-foreground" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{item.title}</p>
                      {item.subtitle ? (
                        <p className="truncate text-xs text-muted-foreground">{item.subtitle}</p>
                      ) : null}
                      <p className="mt-0.5 text-2xs text-muted-foreground">
                        {formatRelative(item.created_at)}
                      </p>
                    </div>
                  </li>
                );
              })
            ) : (
              <li className="p-8 text-center text-sm text-muted-foreground">
                Faoliyat qaydlari yo&apos;q
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
