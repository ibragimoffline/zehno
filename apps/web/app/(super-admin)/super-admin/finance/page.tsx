"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, DollarSign, Wallet, X } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/input";
import { EmptyState, Pagination, TableSkeleton, Tabs } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { Order, Page } from "@/lib/types";
import { ORDER_STATUS_LABELS, formatDateTime, formatPrice } from "@/lib/utils";

interface PayoutRow {
  id: string;
  amount: string;
  currency: string;
  status: string;
  admin_comment?: string | null;
  requested_at: string;
  reviewed_at?: string | null;
}

export default function AdminFinancePage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = React.useState("orders");
  const [page, setPage] = React.useState(1);
  const [orderStatus, setOrderStatus] = React.useState("");

  const orders = useQuery({
    queryKey: ["admin-orders", page, orderStatus],
    queryFn: () =>
      api.get<Page<Order>>("/admin/finance/orders", {
        query: { page, per_page: 20, order_status: orderStatus || undefined },
      }),
    enabled: tab === "orders",
  });

  const payouts = useQuery({
    queryKey: ["admin-payouts", page],
    queryFn: () =>
      api.get<Page<PayoutRow>>("/admin/finance/payouts", { query: { page, per_page: 20 } }),
    enabled: tab === "payouts",
  });

  const review = useMutation({
    mutationFn: ({ payoutId, status }: { payoutId: string; status: string }) =>
      api.patch(`/admin/finance/payouts/${payoutId}`, undefined, {
        query: { new_status: status },
      }),
    onSuccess: async () => {
      toast.success("Payout holati yangilandi");
      await queryClient.invalidateQueries({ queryKey: ["admin-payouts"] });
      await queryClient.invalidateQueries({ queryKey: ["admin-kpi-badge"] });
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Xatolik"),
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
          { id: "orders", label: "Buyurtmalar" },
          { id: "payouts", label: "Payout so'rovlari" },
        ]}
      />

      {tab === "orders" ? (
        <>
          <Select
            value={orderStatus}
            onChange={(event) => {
              setOrderStatus(event.target.value);
              setPage(1);
            }}
            className="sm:w-56"
            aria-label="Holat bo'yicha filtr"
          >
            <option value="">Barcha holatlar</option>
            {Object.entries(ORDER_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>

          {orders.isLoading ? (
            <TableSkeleton rows={8} cols={5} />
          ) : orders.data && orders.data.items.length > 0 ? (
            <>
              <div className="overflow-x-auto rounded-xl border bg-card">
                <table className="w-full text-sm">
                  <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-5 py-3">Buyurtma</th>
                      <th className="px-5 py-3">Kurslar</th>
                      <th className="px-5 py-3">Summa</th>
                      <th className="px-5 py-3">Holat</th>
                      <th className="px-5 py-3">Sana</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {orders.data.items.map((order) => (
                      <tr key={order.id}>
                        <td className="px-5 py-3 font-mono text-xs">{order.order_number}</td>
                        <td className="px-5 py-3">
                          <ul className="space-y-0.5">
                            {order.items.map((item) => (
                              <li key={item.id} className="truncate">
                                {item.course_title}
                              </li>
                            ))}
                          </ul>
                        </td>
                        <td className="px-5 py-3 font-semibold">
                          {formatPrice(order.total, order.currency)}
                        </td>
                        <td className="px-5 py-3">
                          <StatusBadge
                            status={order.status}
                            label={ORDER_STATUS_LABELS[order.status] ?? order.status}
                          />
                        </td>
                        <td className="px-5 py-3 text-muted-foreground">
                          {formatDateTime(order.paid_at ?? order.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <Pagination page={orders.data.page} pages={orders.data.pages} onChange={setPage} />
            </>
          ) : (
            <EmptyState
              icon={DollarSign}
              title="Buyurtmalar yo'q"
              className="rounded-xl border bg-card"
            />
          )}
        </>
      ) : payouts.isLoading ? (
        <TableSkeleton rows={6} cols={5} />
      ) : payouts.data && payouts.data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border bg-card">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Summa</th>
                  <th className="px-5 py-3">Holat</th>
                  <th className="px-5 py-3">So&apos;rov</th>
                  <th className="px-5 py-3">Izoh</th>
                  <th className="px-5 py-3 text-right">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {payouts.data.items.map((row) => (
                  <tr key={row.id}>
                    <td className="px-5 py-3 font-semibold">
                      {formatPrice(row.amount, row.currency)}
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={row.status} label={row.status} />
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {formatDateTime(row.requested_at)}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">{row.admin_comment ?? "—"}</td>
                    <td className="px-5 py-3">
                      {row.status === "pending" ? (
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            loading={review.isPending}
                            onClick={() => review.mutate({ payoutId: row.id, status: "paid" })}
                          >
                            <Check /> To&apos;landi
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => review.mutate({ payoutId: row.id, status: "rejected" })}
                          >
                            <X /> Rad etish
                          </Button>
                        </div>
                      ) : (
                        <span className="block text-right text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination page={payouts.data.page} pages={payouts.data.pages} onChange={setPage} />
        </>
      ) : (
        <EmptyState
          icon={Wallet}
          title="Payout so'rovlari yo'q"
          className="rounded-xl border bg-card"
        />
      )}
    </div>
  );
}
