"use client";

import { useQuery } from "@tanstack/react-query";
import { Users } from "lucide-react";
import * as React from "react";

import { Progress } from "@/components/ui/misc";
import { StatusBadge } from "@/components/ui/badge";
import { Select } from "@/components/ui/input";
import { EmptyState, Pagination, TableSkeleton } from "@/components/ui/misc";
import { api } from "@/lib/api-client";
import type { CourseAdminSummary, Page } from "@/lib/types";
import { ENROLLMENT_STATUS_LABELS, formatDate } from "@/lib/utils";

interface EnrollmentRow {
  id: string;
  user_id: string;
  course_id: string;
  status: string;
  progress_percent: number;
  enrolled_at: string;
  completed_at?: string | null;
  user_name?: string | null;
  user_email?: string | null;
  course_title?: string | null;
}

export default function TeacherStudentsPage() {
  const [courseId, setCourseId] = React.useState("");
  const [page, setPage] = React.useState(1);

  const { data: courses } = useQuery({
    queryKey: ["teacher-courses", "all", 1],
    queryFn: () =>
      api.get<Page<CourseAdminSummary>>("/teacher/courses", { query: { per_page: 100 } }),
  });

  // Ustoz faqat o'z kurslaridagi talabalarni ko'radi (backend RBAC bilan cheklaydi)
  const { data, isLoading } = useQuery({
    queryKey: ["teacher-students", courseId, page],
    queryFn: () =>
      api.get<Page<EnrollmentRow>>("/teacher/students", {
        query: { course_id: courseId || undefined, page, per_page: 20 },
      }),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Select
          value={courseId}
          onChange={(event) => {
            setCourseId(event.target.value);
            setPage(1);
          }}
          className="sm:w-80"
          aria-label="Kurs bo'yicha filtr"
        >
          <option value="">Barcha kurslar</option>
          {courses?.items.map((course) => (
            <option key={course.id} value={course.id}>
              {course.title}
            </option>
          ))}
        </Select>
      </div>

      {isLoading ? (
        <TableSkeleton rows={6} cols={5} />
      ) : data && data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border bg-card">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Talaba</th>
                  <th className="px-5 py-3">Kurs</th>
                  <th className="px-5 py-3 w-48">Progress</th>
                  <th className="px-5 py-3">Holat</th>
                  <th className="px-5 py-3">Yozilgan</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((row) => (
                  <tr key={row.id}>
                    <td className="px-5 py-3">
                      <p className="font-medium">{row.user_name ?? "—"}</p>
                      <p className="text-xs text-muted-foreground">{row.user_email}</p>
                    </td>
                    <td className="px-5 py-3">{row.course_title ?? "—"}</td>
                    <td className="px-5 py-3">
                      <Progress value={row.progress_percent} showLabel size="sm" />
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge
                        status={row.status}
                        label={ENROLLMENT_STATUS_LABELS[row.status] ?? row.status}
                      />
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {formatDate(row.enrolled_at)}
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
          icon={Users}
          title="Hali talabalar yo'q"
          description="Kurs nashr etilib, birinchi sotuvdan keyin talabalar shu yerda ko'rinadi."
          className="rounded-xl border border-dashed bg-card"
        />
      )}
    </div>
  );
}
