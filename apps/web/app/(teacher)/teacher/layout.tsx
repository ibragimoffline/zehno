"use client";

import {
  BookOpen,
  GraduationCap,
  LayoutDashboard,
  Settings,
  Tag,
  Users,
  Wallet,
} from "lucide-react";
import Link from "next/link";

import { DashboardShell, type SidebarItem } from "@/components/layout/dashboard-shell";
import { ButtonLink } from "@/components/ui/button";
import { Spinner } from "@/components/ui/misc";
import { useRequireAuth } from "@/lib/hooks/use-auth";

const ITEMS: SidebarItem[] = [
  { href: "/teacher/courses", label: "Kurslarim", icon: BookOpen },
  { href: "/teacher/students", label: "Talabalar", icon: Users },
  { href: "/teacher/earnings", label: "Daromad", icon: Wallet },
  { href: "/teacher/coupons", label: "Kuponlar", icon: Tag },
  { href: "/teacher/settings", label: "Sozlamalar", icon: Settings },
];

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, authorized } = useRequireAuth(["teacher", "org_admin", "admin"]);

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
      title="Ustoz paneli"
      subtitle={user?.full_name}
      brand={
        <Link href="/" className="flex items-center gap-2">
          <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <GraduationCap className="size-5" />
          </span>
          <span>
            <span className="block font-bold leading-tight">Zehno.uz</span>
            <span className="block text-xs text-muted-foreground">Ustoz kabineti</span>
          </span>
        </Link>
      }
      actions={
        <ButtonLink href="/teacher/courses/new" size="sm">
          <LayoutDashboard /> Yangi kurs
        </ButtonLink>
      }
    >
      {children}
    </DashboardShell>
  );
}
