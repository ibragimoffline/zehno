"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, Search, ShieldCheck, Users } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { Avatar, EmptyState, Pagination, TableSkeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { AdminUserRow, Page, UserRole } from "@/lib/types";
import { ROLE_LABELS, formatDate } from "@/lib/utils";

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = React.useState("");
  const [role, setRole] = React.useState<string>("");
  const [page, setPage] = React.useState(1);
  const [query, setQuery] = React.useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users", query, role, page],
    queryFn: () =>
      api.get<Page<AdminUserRow>>("/admin/users", {
        query: { search: query || undefined, role: role || undefined, page, per_page: 20 },
      }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["admin-users"] });

  const changeRole = useMutation({
    mutationFn: ({ userId, newRole }: { userId: string; newRole: UserRole }) =>
      api.patch(`/admin/users/${userId}/role`, { role: newRole }),
    onSuccess: async () => {
      toast.success("Rol o'zgartirildi");
      await invalidate();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Xatolik"),
  });

  const toggleBlock = useMutation({
    mutationFn: ({ userId, blocked }: { userId: string; blocked: boolean }) =>
      api.patch(`/admin/users/${userId}/block`, { is_blocked: blocked }),
    onSuccess: async (_, variables) => {
      toast.success(variables.blocked ? "Foydalanuvchi bloklandi" : "Blokdan chiqarildi");
      await invalidate();
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
            placeholder="Ism, email yoki telefon bo'yicha qidirish"
            className="pl-9"
          />
        </div>

        <Select
          value={role}
          onChange={(event) => {
            setRole(event.target.value);
            setPage(1);
          }}
          className="sm:w-52"
          aria-label="Rol bo'yicha filtr"
        >
          <option value="">Barcha rollar</option>
          {Object.entries(ROLE_LABELS).map(([value, label]) => (
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
        <TableSkeleton rows={8} cols={5} />
      ) : data && data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border bg-card">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40 text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-5 py-3">Foydalanuvchi</th>
                  <th className="px-5 py-3">Rol</th>
                  <th className="px-5 py-3">Kurslar</th>
                  <th className="px-5 py-3">Ro&apos;yxatdan o&apos;tgan</th>
                  <th className="px-5 py-3">Holat</th>
                  <th className="px-5 py-3 text-right">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((user) => (
                  <tr key={user.id}>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2.5">
                        <Avatar name={user.full_name} src={user.avatar_url} size={32} />
                        <div className="min-w-0">
                          <p className="truncate font-medium">{user.full_name}</p>
                          <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <Select
                        value={user.role}
                        onChange={(event) =>
                          changeRole.mutate({
                            userId: user.id,
                            newRole: event.target.value as UserRole,
                          })
                        }
                        className="h-8 w-40 text-xs"
                        aria-label={`${user.full_name} roli`}
                      >
                        {Object.entries(ROLE_LABELS).map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </Select>
                    </td>
                    <td className="px-5 py-3 tabular-nums">{user.courses_count}</td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-5 py-3">
                      {user.is_blocked ? (
                        <Badge variant="destructive">Bloklangan</Badge>
                      ) : user.is_active ? (
                        <Badge variant="success">Faol</Badge>
                      ) : (
                        <Badge variant="muted">Nofaol</Badge>
                      )}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <Button
                        size="sm"
                        variant={user.is_blocked ? "outline" : "ghost"}
                        onClick={() =>
                          toggleBlock.mutate({ userId: user.id, blocked: !user.is_blocked })
                        }
                      >
                        {user.is_blocked ? (
                          <>
                            <ShieldCheck /> Blokdan chiqarish
                          </>
                        ) : (
                          <>
                            <Ban className="text-destructive" /> Bloklash
                          </>
                        )}
                      </Button>
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
          title="Foydalanuvchi topilmadi"
          description="Qidiruv shartlarini o'zgartirib ko'ring."
          className="rounded-xl border bg-card"
        />
      )}
    </div>
  );
}
