"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as React from "react";

import { cn } from "@/lib/utils";

export interface SidebarItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number | string;
  exact?: boolean;
}

/**
 * Chap sidebar bilan universal dashboard karkasi.
 * Teacher, B2B va Super-Admin panellari shu karkasdan foydalanadi
 * (super-admin `theme="admin"` bilan — quyuq "operatsion" uslub).
 */
export function DashboardShell({
  items,
  title,
  subtitle,
  actions,
  children,
  brand,
  theme = "light",
}: {
  items: SidebarItem[];
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  brand?: React.ReactNode;
  theme?: "light" | "admin";
}) {
  const pathname = usePathname();
  const [open, setOpen] = React.useState(false);

  const isActive = (item: SidebarItem) =>
    item.exact ? pathname === item.href : pathname.startsWith(item.href);

  return (
    <div className="flex min-h-screen bg-muted/20" data-theme={theme === "admin" ? "admin" : undefined}>
      {/* Sidebar — desktop */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r bg-card lg:flex">
        {brand ? <div className="border-b p-5">{brand}</div> : null}
        <nav className="flex-1 space-y-1 overflow-y-auto p-3 scrollbar-thin">
          {items.map((item) => (
            <SidebarLink key={item.href} item={item} active={isActive(item)} />
          ))}
        </nav>
        <div className="border-t p-3">
          <Link
            href="/"
            className="block rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            ← Saytga qaytish
          </Link>
        </div>
      </aside>

      {/* Sidebar — mobil (drawer) */}
      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} aria-hidden />
          <aside className="relative z-10 flex h-full w-72 flex-col bg-card">
            <div className="flex items-center justify-between border-b p-4">
              {brand}
              <button type="button" onClick={() => setOpen(false)} aria-label="Yopish">
                <X className="size-5" />
              </button>
            </div>
            <nav className="flex-1 space-y-1 overflow-y-auto p-3">
              {items.map((item) => (
                <SidebarLink
                  key={item.href}
                  item={item}
                  active={isActive(item)}
                  onClick={() => setOpen(false)}
                />
              ))}
            </nav>
          </aside>
        </div>
      ) : null}

      {/* Asosiy qism */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b bg-card/95 backdrop-blur">
          <div className="flex items-center gap-3 px-4 py-3.5 sm:px-6">
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="rounded-lg p-2 hover:bg-muted lg:hidden"
              aria-label="Menyu"
            >
              <Menu className="size-5" />
            </button>
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-lg font-semibold">{title}</h1>
              {subtitle ? (
                <p className="truncate text-sm text-muted-foreground">{subtitle}</p>
              ) : null}
            </div>
            {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
          </div>
        </header>

        <main id="main-content" className="flex-1 p-4 sm:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}

function SidebarLink({
  item,
  active,
  onClick,
}: {
  item: SidebarItem;
  active: boolean;
  onClick?: () => void;
}) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
        active
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
    >
      <Icon className="size-4 shrink-0" />
      <span className="min-w-0 flex-1 truncate">{item.label}</span>
      {item.badge !== undefined && item.badge !== 0 ? (
        <span className="shrink-0 rounded-full bg-destructive px-1.5 py-0.5 text-2xs font-bold text-destructive-foreground">
          {item.badge}
        </span>
      ) : null}
    </Link>
  );
}

/** KPI kartochkasi — dashboardlarda takrorlanadigan blok */
export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
  icon?: React.ComponentType<{ className?: string }>;
  tone?: "default" | "success" | "warning" | "danger" | "primary";
}) {
  const toneClass = {
    default: "bg-muted text-muted-foreground",
    primary: "bg-primary/10 text-primary",
    success: "bg-secondary/10 text-secondary",
    warning: "bg-accent/15 text-accent-foreground",
    danger: "bg-destructive/10 text-destructive",
  }[tone];

  return (
    <div className="rounded-xl border bg-card p-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm text-muted-foreground">{label}</p>
          <p className="mt-1.5 text-2xl font-bold tabular-nums">{value}</p>
          {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
        </div>
        {Icon ? (
          <span className={cn("flex size-10 shrink-0 items-center justify-center rounded-lg", toneClass)}>
            <Icon className="size-5" />
          </span>
        ) : null}
      </div>
    </div>
  );
}
