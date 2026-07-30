"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Tag, Trash2 } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select } from "@/components/ui/input";
import { EmptyState, Modal, TableSkeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { Coupon, CourseAdminSummary, Page } from "@/lib/types";
import { formatDate, formatPrice } from "@/lib/utils";

export default function CouponsPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = React.useState(false);
  const [form, setForm] = React.useState({
    code: "",
    type: "percent",
    value: "10",
    course_id: "",
    max_redemptions: "",
    expires_at: "",
  });

  const { data, isLoading } = useQuery({
    queryKey: ["coupons"],
    queryFn: () => api.get<Page<Coupon>>("/teacher/coupons"),
  });

  const { data: courses } = useQuery({
    queryKey: ["teacher-courses", "coupon-picker"],
    queryFn: () =>
      api.get<Page<CourseAdminSummary>>("/teacher/courses", { query: { per_page: 100 } }),
  });

  const create = useMutation({
    mutationFn: () =>
      api.post<Coupon>("/teacher/coupons", {
        code: form.code.trim() || undefined,
        type: form.type,
        value: form.value,
        course_id: form.course_id || undefined,
        max_redemptions: form.max_redemptions ? Number(form.max_redemptions) : undefined,
        expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : undefined,
      }),
    onSuccess: async (coupon) => {
      toast.success(`Kupon yaratildi: ${coupon.code}`);
      setOpen(false);
      setForm({ code: "", type: "percent", value: "10", course_id: "", max_redemptions: "", expires_at: "" });
      await queryClient.invalidateQueries({ queryKey: ["coupons"] });
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Yaratilmadi"),
  });

  const remove = useMutation({
    mutationFn: (couponId: string) => api.delete(`/teacher/coupons/${couponId}`),
    onSuccess: async () => {
      toast.success("Kupon o'chirildi");
      await queryClient.invalidateQueries({ queryKey: ["coupons"] });
    },
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Chegirma kuponlari</h2>
          <p className="text-sm text-muted-foreground">
            Foizli yoki summaviy chegirma kodlari yaratib, sotuvni oshiring
          </p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus /> Kupon yaratish
        </Button>
      </div>

      {isLoading ? (
        <TableSkeleton rows={4} cols={5} />
      ) : data && data.items.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border bg-card">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-5 py-3">Kod</th>
                <th className="px-5 py-3">Chegirma</th>
                <th className="px-5 py-3">Ishlatilgan</th>
                <th className="px-5 py-3">Muddat</th>
                <th className="px-5 py-3">Holat</th>
                <th className="px-5 py-3 text-right">Amal</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.items.map((coupon) => (
                <tr key={coupon.id}>
                  <td className="px-5 py-3">
                    <code className="rounded bg-muted px-2 py-1 font-mono text-xs font-bold">
                      {coupon.code}
                    </code>
                  </td>
                  <td className="px-5 py-3 font-medium">
                    {coupon.type === "percent"
                      ? `${Number(coupon.value)}%`
                      : formatPrice(coupon.value)}
                  </td>
                  <td className="px-5 py-3 tabular-nums">
                    {coupon.redemptions_count}
                    {coupon.max_redemptions ? ` / ${coupon.max_redemptions}` : ""}
                  </td>
                  <td className="px-5 py-3 text-muted-foreground">
                    {coupon.expires_at ? formatDate(coupon.expires_at) : "cheksiz"}
                  </td>
                  <td className="px-5 py-3">
                    {coupon.is_active ? (
                      <Badge variant="success">Faol</Badge>
                    ) : (
                      <Badge variant="muted">O&apos;chirilgan</Badge>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {coupon.is_active ? (
                      <Button
                        size="icon-sm"
                        variant="ghost"
                        onClick={() => remove.mutate(coupon.id)}
                        aria-label="Kuponni o'chirish"
                      >
                        <Trash2 className="text-destructive" />
                      </Button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          icon={Tag}
          title="Hali kupon yo'q"
          description="Chegirma kodi yaratib, kursingizni tezroq sotishni boshlang."
          action={<Button onClick={() => setOpen(true)}>Kupon yaratish</Button>}
          className="rounded-xl border border-dashed bg-card"
        />
      )}

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Yangi kupon"
        footer={
          <>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Bekor qilish
            </Button>
            <Button loading={create.isPending} onClick={() => create.mutate()}>
              Yaratish
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Field
            label="Kupon kodi"
            htmlFor="coupon-code"
            hint="Bo'sh qoldirsangiz avtomatik generatsiya qilinadi"
          >
            <Input
              value={form.code}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, code: event.target.value.toUpperCase() }))
              }
              placeholder="YANGIYIL2026"
              className="font-mono uppercase"
            />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Turi" htmlFor="coupon-type">
              <Select
                value={form.type}
                onChange={(event) => setForm((prev) => ({ ...prev, type: event.target.value }))}
              >
                <option value="percent">Foizli (%)</option>
                <option value="fixed">Summaviy (so&apos;m)</option>
              </Select>
            </Field>

            <Field
              label={form.type === "percent" ? "Chegirma (%)" : "Chegirma (so'm)"}
              htmlFor="coupon-value"
              required
            >
              <Input
                type="number"
                min={1}
                max={form.type === "percent" ? 100 : undefined}
                value={form.value}
                onChange={(event) => setForm((prev) => ({ ...prev, value: event.target.value }))}
              />
            </Field>
          </div>

          <Field
            label="Kurs"
            htmlFor="coupon-course"
            hint="Bo'sh qoldirsangiz barcha kurslaringizga tegishli bo'ladi"
          >
            <Select
              value={form.course_id}
              onChange={(event) => setForm((prev) => ({ ...prev, course_id: event.target.value }))}
            >
              <option value="">Barcha kurslarim</option>
              {courses?.items.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.title}
                </option>
              ))}
            </Select>
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Maksimal foydalanish" htmlFor="coupon-max" hint="Ixtiyoriy">
              <Input
                type="number"
                min={1}
                value={form.max_redemptions}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, max_redemptions: event.target.value }))
                }
                placeholder="100"
              />
            </Field>

            <Field label="Amal qilish muddati" htmlFor="coupon-expires" hint="Ixtiyoriy">
              <Input
                type="date"
                value={form.expires_at}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, expires_at: event.target.value }))
                }
              />
            </Field>
          </div>
        </div>
      </Modal>
    </div>
  );
}
