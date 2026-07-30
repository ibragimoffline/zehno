"use client";

import { Building2, FileSpreadsheet, LayoutDashboard, RefreshCw, Users } from "lucide-react";
import Link from "next/link";

import { DashboardShell, type SidebarItem } from "@/components/layout/dashboard-shell";
import { Spinner } from "@/components/ui/misc";
import { useRequireAuth } from "@/lib/hooks/use-auth";

const ITEMS: SidebarItem[] = [
  { href: "/b2b/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/b2b/employees", label: "Xodimlar", icon: Users },
  { href: "/b2b/enroll", label: "Kursga yozish", icon: FileSpreadsheet },
  { href: "/b2b/crm", label: "CRM sinxron", icon: RefreshCw },
];

export default function B2BLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, authorized } = useRequireAuth(["b2b_manager", "org_admin", "admin"]);

  if (loading || !authorized) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="size-7" />
      </div>
    );
  }

  return (
    <DashboardShell
      items={ITEMS}
      title="Korporativ panel"
      subtitle={user?.full_name}
      brand={
        <Link href="/" className="flex items-center gap-2">
          <span className="flex size-9 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
            <Building2 className="size-5" />
          </span>
          <span>
            <span className="block font-bold leading-tight">Zehno.uz</span>
            <span className="block text-xs text-muted-foreground">B2B kabinet</span>
          </span>
        </Link>
      }
    >
      {children}
    </DashboardShell>
  );
}
