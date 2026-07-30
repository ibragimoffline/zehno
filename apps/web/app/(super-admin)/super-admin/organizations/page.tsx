"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BadgeCheck, Building2, Search } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { EmptyState, Pagination, TableSkeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { Organization, Page } from "@/lib/types";
import { ORGANIZATION_TYPE_LABELS, formatDate } from "@/lib/utils";

export default function AdminOrganizationsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = React.useState("");
  const [query, setQuery] = React.useState("");
  const [type, setType] = React.useState("");
  const [page, setPage] = React.useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-organizations", query, type, page],
    queryFn: () =>
      api.get<Page<Organization>>("/admin/organizations", {
        query: { search: query || undefined, type: type || undefined, page, per_page: 20 },
      }),
  });

  const verify = useMutation({
    mutationFn: ({ orgId, verified }: { orgId: string; verified: boolean }) =>
      api.patch(`/admin/organizations/${orgId}/verify`, undefined, {
        query: { is_verified: verified },
      }),
    onSuccess: async () => {
      toast.success("Tashkilot holati yangilandi");
      await queryClient.invalidateQueries({ queryKey: ["admin-organizations"] });
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Xatolik"),
  });

  return (
    <div className="space-y-5">
      <form
        className="flex flex-col gap-3 sm:flex-row"
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
            placeholder="Tashkilot nomi bo'yicha qidirish"
            className="pl-9"
          />
        </div>

        <Select
          value={type}
          onChange={(event) => {
            setType(event.target.value);
            setPage(1);
          }}
          className="sm:w-52"
          aria-label="Turi bo'yicha filtr"
        >
          <option value="">Barcha turlar</option>
          {Object.entries(ORGANIZATION_TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>

        <Button type="submit" variant="outline">
          Qidirish
        </Button>
      </form>

      {isLoading ? (
        <TableSkeleton rows={6} cols={5} />
      ) : data && data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border bg-card">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Tashkilot</th>
                  <th className="px-5 py-3">Turi</th>
                  <th className="px-5 py-3">A&apos;zolar</th>
                  <th className="px-5 py-3">CRM</th>
                  <th className="px-5 py-3">Yaratilgan</th>
                  <th className="px-5 py-3 text-right">Tasdiq</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((org) => (
                  <tr key={org.id}>
                    <td className="px-5 py-3">
                      <p className="font-medium">{org.name}</p>
                      <p className="font-mono text-xs text-muted-foreground">{org.slug}</p>
                    </td>
                    <td className="px-5 py-3">
                      <Badge variant="muted">
                        {ORGANIZATION_TYPE_LABELS[org.type] ?? org.type}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 tabular-nums">
                      {org.members_count ?? 0}
                      {org.seats_purchased ? ` / ${org.seats_purchased} o'rin` : ""}
                    </td>
                    <td className="px-5 py-3">
                      {org.crm_sync_enabled ? (
                        <Badge variant="success">{org.crm_provider ?? "ulangan"}</Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {formatDate(org.created_at)}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {org.is_verified ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => verify.mutate({ orgId: org.id, verified: false })}
                        >
                          <BadgeCheck className="text-secondary" /> Tasdiqlangan
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          loading={verify.isPending}
                          onClick={() => verify.mutate({ orgId: org.id, verified: true })}
                        >
                          Tasdiqlash
                        </Button>
                      )}
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
          icon={Building2}
          title="Tashkilotlar topilmadi"
          className="rounded-xl border bg-card"
        />
      )}
    </div>
  );
}
