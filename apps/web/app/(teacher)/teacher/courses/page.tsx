"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Eye, Pencil, Send, Star, Trash2, Users } from "lucide-react";
import Link from "next/link";
import * as React from "react";
import { toast } from "sonner";

import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { EmptyState, Modal, Pagination, TableSkeleton, Tabs } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { CourseAdminSummary, Page } from "@/lib/types";
import { COURSE_STATUS_LABELS, formatDate, formatNumber, formatPrice } from "@/lib/utils";

const TABS = [
  { id: "all", label: "Barchasi" },
  { id: "draft", label: "Qoralama" },
  { id: "pending", label: "Moderatsiyada" },
  { id: "published", label: "Nashr etilgan" },
  { id: "rejected", label: "Rad etilgan" },
];

export default function TeacherCoursesPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = React.useState("all");
  const [page, setPage] = React.useState(1);
  const [deleteTarget, setDeleteTarget] = React.useState<CourseAdminSummary | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["teacher-courses", tab, page],
    queryFn: () =>
      api.get<Page<CourseAdminSummary>>("/teacher/courses", {
        query: { status: tab === "all" ? undefined : tab, page, per_page: 12 },
      }),
  });

  const submitMutation = useMutation({
    mutationFn: (courseId: string) =>
      api.post<CourseAdminSummary>(`/teacher/courses/${courseId}/submit`),
    onSuccess: async () => {
      toast.success("Kurs moderatsiyaga yuborildi");
      await queryClient.invalidateQueries({ queryKey: ["teacher-courses"] });
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Yuborilmadi");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (courseId: string) => api.delete(`/teacher/courses/${courseId}`),
    onSuccess: async () => {
      toast.success("Kurs o'chirildi");
      setDeleteTarget(null);
      await queryClient.invalidateQueries({ queryKey: ["teacher-courses"] });
    },
    onError: (error) => {
      // Talabalari bor kurs arxivlanadi — backend `archived_instead` kodini qaytaradi
      if (error instanceof ApiError && error.code === "archived_instead") {
        toast.warning(error.message);
        setDeleteTarget(null);
        void queryClient.invalidateQueries({ queryKey: ["teacher-courses"] });
        return;
      }
      toast.error(error instanceof ApiError ? error.message : "O'chirilmadi");
    },
  });

  return (
    <div>
      <Tabs active={tab} onChange={(id) => { setTab(id); setPage(1); }} tabs={TABS} className="mb-5" />

      {isLoading ? (
        <TableSkeleton rows={5} cols={5} />
      ) : data && data.items.length > 0 ? (
        <>
          <div className="space-y-3">
            {data.items.map((course) => (
              <div
                key={course.id}
                className="flex flex-col gap-4 rounded-xl border bg-card p-4 sm:flex-row sm:items-center"
              >
                <Link
                  href={`/teacher/courses/${course.id}`}
                  className="hidden w-32 shrink-0 overflow-hidden rounded-lg bg-muted sm:block"
                >
                  {course.cover_url ? (
                    <img
                      src={course.cover_url}
                      alt={course.title}
                      className="aspect-video size-full object-cover"
                    />
                  ) : (
                    <span className="flex aspect-video items-center justify-center text-muted-foreground">
                      <BookOpen className="size-6" />
                    </span>
                  )}
                </Link>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge
                      status={course.status}
                      label={COURSE_STATUS_LABELS[course.status] ?? course.status}
                    />
                    {course.is_bestseller ? <Badge variant="accent">Bestseller</Badge> : null}
                  </div>

                  <Link
                    href={`/teacher/courses/${course.id}`}
                    className="mt-1.5 block truncate font-semibold hover:text-primary"
                  >
                    {course.title}
                  </Link>

                  <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <span>{course.lessons_count} dars</span>
                    <span className="flex items-center gap-1">
                      <Users className="size-3.5" /> {formatNumber(course.students_count)}
                    </span>
                    {course.rating_count > 0 ? (
                      <span className="flex items-center gap-1">
                        <Star className="size-3.5 fill-accent-500 text-accent-500" />
                        {course.rating_avg.toFixed(1)} ({course.rating_count})
                      </span>
                    ) : null}
                    <span>{formatDate(course.updated_at)}</span>
                  </div>

                  {course.status === "rejected" && course.rejection_reason ? (
                    <p className="mt-2 rounded-lg bg-destructive/5 px-3 py-2 text-xs text-destructive">
                      Rad etish sababi: {course.rejection_reason}
                    </p>
                  ) : null}
                </div>

                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  <span className="mr-2 font-semibold">
                    {formatPrice(course.discount_price ?? course.price, course.currency)}
                  </span>

                  {course.status === "published" ? (
                    <ButtonLink
                      href={`/courses/${course.slug}`}
                      size="icon-sm"
                      variant="outline"
                      aria-label="Ko'rish"
                    >
                      <Eye />
                    </ButtonLink>
                  ) : null}

                  <ButtonLink
                    href={`/teacher/courses/${course.id}`}
                    size="icon-sm"
                    variant="outline"
                    aria-label="Tahrirlash"
                  >
                    <Pencil />
                  </ButtonLink>

                  {course.status === "draft" || course.status === "rejected" ? (
                    <Button
                      size="sm"
                      loading={submitMutation.isPending}
                      onClick={() => submitMutation.mutate(course.id)}
                    >
                      <Send /> Moderatsiyaga
                    </Button>
                  ) : null}

                  <Button
                    size="icon-sm"
                    variant="ghost"
                    onClick={() => setDeleteTarget(course)}
                    aria-label="O'chirish"
                  >
                    <Trash2 className="text-destructive" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <Pagination page={data.page} pages={data.pages} onChange={setPage} className="mt-7" />
        </>
      ) : (
        <EmptyState
          icon={BookOpen}
          title="Hali kurs yaratmadingiz"
          description="Bosqichma-bosqich usta orqali birinchi kursingizni 15 daqiqada yarating."
          action={<ButtonLink href="/teacher/courses/new">Kurs yaratish</ButtonLink>}
          className="rounded-xl border border-dashed bg-card"
        />
      )}

      {/* O'chirish tasdig'i */}
      <Modal
        open={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        title="Kursni o'chirish"
        footer={
          <>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Bekor qilish
            </Button>
            <Button
              variant="destructive"
              loading={deleteMutation.isPending}
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
            >
              O&apos;chirish
            </Button>
          </>
        }
      >
        <p className="text-sm text-muted-foreground">
          <strong className="text-foreground">{deleteTarget?.title}</strong> kursini o&apos;chirmoqchimisiz?
          Agar kursda talabalar bo&apos;lsa, u o&apos;chirilmaydi — arxivlanadi.
        </p>
      </Modal>
    </div>
  );
}
