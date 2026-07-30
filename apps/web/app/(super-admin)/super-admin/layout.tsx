"use client";

import {
  Building2,
  DollarSign,
  FileClock,
  LayoutDashboard,
  Plug,
  ShieldCheck,
  ShieldQuestion,
  Sliders,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { DashboardShell, type SidebarItem } from "@/components/layout/dashboard-shell";
import { Spinner } from "@/components/ui/misc";
import { api } from "@/lib/api-client";
import { useRequireAuth } from "@/lib/hooks/use-auth";
import type { PlatformKpi } from "@/lib/types";

export default function SuperAdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, authorized } = useRequireAuth(["admin"]);

  const { data: kpi } = useQuery({
    queryKey: ["admin-kpi-badge"],
    queryFn: () => api.get<PlatformKpi>("/admin/dashboard"),
    enabled: authorized,
    refetchInterval: 60_000,
  });

  if (loading || !authorized) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <Spinner className="size-7 text-white" />
      </div>
    );
  }

  const items: SidebarItem[] = [
    { href: "/super-admin", label: "Dashboard", icon: LayoutDashboard, exact: true },
    {
      href: "/super-admin/moderation",
      label: "Moderatsiya",
      icon: ShieldQuestion,
      badge: kpi?.courses_pending,
    },
    { href: "/super-admin/users", label: "Foydalanuvchilar", icon: Users },
    { href: "/super-admin/organizations", label: "Tashkilotlar", icon: Building2 },
    {
      href: "/super-admin/finance",
      label: "Moliya",
      icon: DollarSign,
      badge: kpi?.pending_payouts,
    },
    { href: "/super-admin/integrations", label: "Integratsiyalar", icon: Plug },
    { href: "/super-admin/logs", label: "Loglar", icon: FileClock },
    { href: "/super-admin/settings", label: "Tizim sozlamalari", icon: Sliders },
  ];

  return (
    <DashboardShell
      theme="admin"
      items={items}
      title="Super-admin panel"
      subtitle={`${user?.email} · platforma boshqaruvi`}
      brand={
        <Link href="/super-admin" className="flex items-center gap-2">
          <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ShieldCheck className="size-5" />
          </span>
          <span>
            <span className="block font-bold leading-tight">Zehno.uz</span>
            <span className="block text-2xs font-semibold uppercase tracking-widest text-primary">
              Admin
            </span>
          </span>
        </Link>
      }
    >
      {children}
    </DashboardShell>
  );
}
