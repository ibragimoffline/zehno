"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Banknote, TrendingUp, Users, Wallet } from "lucide-react";
import * as React from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { toast } from "sonner";

import { StatCard } from "@/components/layout/dashboard-shell";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { EmptyState, Modal, Skeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { EarningsPoint, EarningsSummary, Page } from "@/lib/types";
import { formatCompact, formatDate, formatPrice } from "@/lib/utils";

interface PayoutRow {
  id: string;
  amount: string;
  currency: string;
  status: string;
  admin_comment?: string | null;
  requested_at: string;
  reviewed_at?: string | null;
}

const PAYOUT_STATUS_LABELS: Record<string, string> = {
  pending: "Kutilmoqda",
  approved: "Tasdiqlangan",
  paid: "To'langan",
  rejected: "Rad etilgan",
};

export default function EarningsPage() {
  const queryClient = useQueryClient();
  const [payoutOpen, setPayoutOpen] = React.useState(false);
  const [amount, setAmount] = React.useState("");

  const { data: summary, isLoading } = useQuery({
    queryKey: ["earnings"],
    queryFn: () => api.get<EarningsSummary>("/teacher/earnings"),
  });

  const { data: chart = [] } = useQuery({
    queryKey: ["earnings-chart"],
    queryFn: () => api.get<EarningsPoint[]>("/teacher/earnings/chart", { query: { days: 30 } }),
  });

  const { data: payouts } = useQuery({
    queryKey: ["payouts"],
    queryFn: () => api.get<Page<PayoutRow>>("/teacher/payouts"),
  });

  const requestPayout = useMutation({
    mutationFn: () => api.post("/teacher/payouts", { amount }),
    onSuccess: async () => {
      toast.success("Pul yechish so'rovi yuborildi");
      setPayoutOpen(false);
      setAmount("");
      await queryClient.invalidateQueries({ queryKey: ["payouts"] });
      await queryClient.invalidateQueries({ queryKey: ["earnings"] });
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.message : "So'rov yuborilmadi"),
  });

  const available = summary
    ? Number(summary.net_total) - Number(summary.paid_out) - Number(summary.pending_payout)
    : 0;

  const chartData = chart.map((point) => ({
    date: point.date.slice(5),
    net: Number(point.net),
    gross: Number(point.gross),
  }));

  return (
    <div className="space-y-6">
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Sof daromad"
            value={formatCompact(summary?.net_total)}
            hint="komissiya ushlangandan keyin"
            icon={Wallet}
            tone="success"
          />
          <StatCard
            label="Umumiy sotuv"
            value={formatCompact(summary?.gross_total)}
            hint={`${summary?.sales_count ?? 0} ta sotuv`}
            icon={TrendingUp}
            tone="primary"
          />
          <StatCard
            label="Platforma komissiyasi"
            value={formatCompact(summary?.commission_total)}
            hint="15%"
            icon={Banknote}
          />
          <StatCard
            label="Talabalar"
            value={summary?.students_count ?? 0}
            icon={Users}
            tone="warning"
          />
        </div>
      )}

      <div className="flex flex-col items-start justify-between gap-4 rounded-xl border bg-card p-5 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm text-muted-foreground">Yechish uchun mavjud</p>
          <p className="mt-1 text-3xl font-bold">{formatPrice(available)}</p>
          {summary && Number(summary.pending_payout) > 0 ? (
            <p className="mt-1 text-xs text-muted-foreground">
              {formatPrice(summary.pending_payout)} so&apos;rov ko&apos;rib chiqilmoqda
            </p>
          ) : null}
        </div>
        <Button size="lg" disabled={available <= 0} onClick={() => setPayoutOpen(true)}>
          Pul yechish
        </Button>
      </div>

      <div className="rounded-xl border bg-card p-5">
        <h2 className="mb-4 text-lg font-semibold">Oxirgi 30 kun daromadi</h2>

        {chartData.length > 0 ? (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="netGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10B981" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                </defs>
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
                <Area
                  type="monotone"
                  dataKey="net"
                  name="Sof daromad"
                  stroke="#10B981"
                  strokeWidth={2}
                  fill="url(#netGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <EmptyState
            icon={TrendingUp}
            title="Hali sotuv yo'q"
            description="Kurs nashr etilgach va birinchi sotuvdan keyin grafik shu yerda ko'rinadi."
          />
        )}
      </div>

      <div className="rounded-xl border bg-card">
        <div className="border-b p-5">
          <h2 className="text-lg font-semibold">Pul yechish so&apos;rovlari</h2>
        </div>

        {payouts && payouts.items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Summa</th>
                  <th className="px-5 py-3">Holat</th>
                  <th className="px-5 py-3">So&apos;rov sanasi</th>
                  <th className="px-5 py-3">Ko&apos;rib chiqilgan</th>
                  <th className="px-5 py-3">Izoh</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {payouts.items.map((row) => (
                  <tr key={row.id}>
                    <td className="px-5 py-3 font-semibold">{formatPrice(row.amount)}</td>
                    <td className="px-5 py-3">
                      <StatusBadge
                        status={row.status === "paid" ? "paid" : row.status}
                        label={PAYOUT_STATUS_LABELS[row.status] ?? row.status}
                      />
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {formatDate(row.requested_at)}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {formatDate(row.reviewed_at)}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">{row.admin_comment ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={Wallet}
            title="So'rovlar yo'q"
            description="Balansingizda pul paydo bo'lgach «Pul yechish» tugmasidan foydalanasiz."
          />
        )}
      </div>

      <Modal
        open={payoutOpen}
        onClose={() => setPayoutOpen(false)}
        title="Pul yechish so'rovi"
        footer={
          <>
            <Button variant="outline" onClick={() => setPayoutOpen(false)}>
              Bekor qilish
            </Button>
            <Button
              loading={requestPayout.isPending}
              disabled={!amount || Number(amount) <= 0 || Number(amount) > available}
              onClick={() => requestPayout.mutate()}
            >
              So&apos;rov yuborish
            </Button>
          </>
        }
      >
        <Field
          label="Summa (UZS)"
          htmlFor="payout-amount"
          hint={`Mavjud: ${formatPrice(available)}`}
          required
        >
          <Input
            type="number"
            min={0}
            max={available}
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            placeholder="500000"
          />
        </Field>
        <p className="mt-3 text-xs text-muted-foreground">
          So&apos;rov super-admin tomonidan ko&apos;rib chiqiladi. To&apos;lov rekvizitlarini
          Sozlamalar bo&apos;limida ko&apos;rsatib qo&apos;yishni unutmang.
        </p>
      </Modal>
    </div>
  );
}
