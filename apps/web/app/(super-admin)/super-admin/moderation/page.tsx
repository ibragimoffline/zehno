"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ExternalLink, ShieldCheck, X } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { EmptyState, Modal, Pagination, TableSkeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { CourseAdminSummary, Page } from "@/lib/types";
import { LEVEL_LABELS, formatDateTime, formatPrice } from "@/lib/utils";

export default function ModerationPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = React.useState(1);
  const [rejectTarget, setRejectTarget] = React.useState<CourseAdminSummary | null>(null);
  const [reason, setReason] = React.useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["moderation", page],
    queryFn: () =>
      api.get<Page<CourseAdminSummary>>("/admin/moderation/pending-courses", {
        query: { page, per_page: 10 },
      }),
  });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["moderation"] });
    await queryClient.invalidateQueries({ queryKey: ["admin-kpi"] });
    await queryClient.invalidateQueries({ queryKey: ["admin-kpi-badge"] });
  };

  const approve = useMutation({
    mutationFn: (courseId: string) => api.post(`/admin/moderation/${courseId}/approve`),
    onSuccess: async () => {
      toast.success("Kurs tasdiqlandi va nashr etildi");
      await invalidate();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Xatolik"),
  });

  const reject = useMutation({
    mutationFn: (courseId: string) =>
      api.post(`/admin/moderation/${courseId}/reject`, { reason }),
    onSuccess: async () => {
      toast.success("Kurs rad etildi, ustozga xabar yuborildi");
      setRejectTarget(null);
      setReason("");
      await invalidate();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Xatolik"),
  });

  if (isLoading) return <TableSkeleton rows={4} cols={4} />;

  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="Moderatsiya navbati bo'sh"
        description="Barcha kurslar ko'rib chiqilgan. Yangi kurs yuborilganda shu yerda paydo bo'ladi."
        className="rounded-xl border bg-card"
      />
    );
  }

  return (
    <div className="space-y-4">
      {data.items.map((course) => (
        <div key={course.id} className="rounded-xl border bg-card p-5">
          <div className="flex flex-col gap-4 sm:flex-row">
            {course.cover_url ? (
              <img
                src={course.cover_url}
                alt={course.title}
                className="h-24 w-40 shrink-0 rounded-lg object-cover"
              />
            ) : null}

            <div className="min-w-0 flex-1">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge variant="warning">Moderatsiyada</Badge>
                <Badge variant="muted">{LEVEL_LABELS[course.level]}</Badge>
                <Badge variant="outline">{course.lessons_count} dars</Badge>
              </div>

              <h3 className="text-lg font-semibold">{course.title}</h3>
              {course.subtitle ? (
                <p className="mt-1 text-sm text-muted-foreground">{course.subtitle}</p>
              ) : null}

              <dl className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
                <div className="flex gap-2">
                  <dt className="text-muted-foreground">Ustoz:</dt>
                  <dd className="font-medium">{course.owner?.full_name ?? "—"}</dd>
                </div>
                <div className="flex gap-2">
                  <dt className="text-muted-foreground">Narx:</dt>
                  <dd className="font-medium">
                    {formatPrice(course.discount_price ?? course.price, course.currency)}
                  </dd>
                </div>
                <div className="flex gap-2">
                  <dt className="text-muted-foreground">Yuborilgan:</dt>
                  <dd>{formatDateTime(course.submitted_at)}</dd>
                </div>
                <div className="flex gap-2">
                  <dt className="text-muted-foreground">Kategoriya:</dt>
                  <dd>{course.category?.name ?? "—"}</dd>
                </div>
              </dl>
            </div>

            <div className="flex shrink-0 flex-col gap-2 sm:w-40">
              <ButtonLink
                href={`/courses/${course.slug}`}
                target="_blank"
                variant="outline"
                size="sm"
              >
                <ExternalLink /> Ko&apos;rish
              </ButtonLink>
              <Button
                size="sm"
                loading={approve.isPending}
                onClick={() => approve.mutate(course.id)}
              >
                <Check /> Tasdiqlash
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setRejectTarget(course);
                  setReason("");
                }}
              >
                <X /> Rad etish
              </Button>
            </div>
          </div>
        </div>
      ))}

      <Pagination page={data.page} pages={data.pages} onChange={setPage} />

      <Modal
        open={Boolean(rejectTarget)}
        onClose={() => setRejectTarget(null)}
        title="Kursni rad etish"
        footer={
          <>
            <Button variant="outline" onClick={() => setRejectTarget(null)}>
              Bekor qilish
            </Button>
            <Button
              variant="destructive"
              loading={reject.isPending}
              disabled={reason.trim().length < 5}
              onClick={() => rejectTarget && reject.mutate(rejectTarget.id)}
            >
              Rad etish
            </Button>
          </>
        }
      >
        <p className="mb-3 text-sm text-muted-foreground">
          <strong className="text-foreground">{rejectTarget?.title}</strong> — rad etish sababini
          yozing. Sabab ustozga ko&apos;rinadi va Telegram orqali yuboriladi.
        </p>
        <Textarea
          rows={4}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="Masalan: 3-modulning video sifati past, ovoz eshitilmaydi. Qayta yuklab, moderatsiyaga yuboring."
        />
      </Modal>
    </div>
  );
}
