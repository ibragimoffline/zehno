"use client";

import { useQuery } from "@tanstack/react-query";
import { Award, Search, Users } from "lucide-react";
import * as React from "react";

import { Button, ButtonLink } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState, Pagination, Progress, TableSkeleton } from "@/components/ui/misc";
import { api } from "@/lib/api-client";
import type { EmployeeProgress, Page } from "@/lib/types";
import { formatRelative } from "@/lib/utils";

export default function B2BEmployeesPage() {
  const [search, setSearch] = React.useState("");
  const [query, setQuery] = React.useState("");
  const [page, setPage] = React.useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["b2b-employees-list", query, page],
    queryFn: () =>
      api.get<Page<EmployeeProgress>>("/b2b/employees", {
        query: { search: query || undefined, page, per_page: 25 },
      }),
  });

  return (
    <div className="space-y-5">
      <form
        className="flex gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          setQuery(search.trim());
          setPage(1);
        }}
      >
        <div className="relative flex-1">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Xodim ismi yoki emaili"
            className="pl-9"
          />
        </div>
        <Button type="submit" variant="outline">
          Qidirish
        </Button>
      </form>

      {isLoading ? (
        <TableSkeleton rows={8} cols={5} />
      ) : data && data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border bg-card">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Xodim</th>
                  <th className="px-5 py-3">Kurslar</th>
                  <th className="w-52 px-5 py-3">Progress</th>
                  <th className="px-5 py-3">Sertifikat</th>
                  <th className="px-5 py-3">Oxirgi faollik</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((employee) => (
                  <tr key={employee.user_id}>
                    <td className="px-5 py-3">
                      <p className="font-medium">{employee.full_name}</p>
                      <p className="text-xs text-muted-foreground">{employee.email}</p>
                    </td>
                    <td className="px-5 py-3 tabular-nums">
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

          <Pagination page={data.page} pages={data.pages} onChange={setPage} />
        </>
      ) : (
        <EmptyState
          icon={Users}
          title="Xodimlar topilmadi"
          description="CSV orqali xodimlarni kursga yozib, ularning progressini kuzatishni boshlang."
          action={<ButtonLink href="/b2b/enroll">Kursga yozish</ButtonLink>}
          className="rounded-xl border bg-card"
        />
      )}
    </div>
  );
}
