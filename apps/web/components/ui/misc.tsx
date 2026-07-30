"use client";

import { ChevronDown, Loader2, Star } from "lucide-react";
import * as React from "react";

import { cn, clampPercent } from "@/lib/utils";

// ---------------------------------------------------------------- Progress
export function Progress({
  value,
  className,
  showLabel,
  size = "default",
}: {
  value: number;
  className?: string;
  showLabel?: boolean;
  size?: "sm" | "default" | "lg";
}) {
  const percent = clampPercent(value);
  const height = size === "sm" ? "h-1.5" : size === "lg" ? "h-3" : "h-2";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn("w-full overflow-hidden rounded-full bg-muted", height)}
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Progress: ${percent}%`}
      >
        <div
          className="h-full rounded-full bg-secondary transition-[width] duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
      {showLabel ? (
        <span className="shrink-0 text-xs font-semibold tabular-nums text-muted-foreground">
          {percent}%
        </span>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------- Skeleton
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton", className)} aria-hidden />;
}

export function CourseCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      <Skeleton className="aspect-video w-full rounded-none" />
      <div className="space-y-3 p-4">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <div className="flex items-center justify-between pt-2">
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-4 w-12" />
        </div>
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-3">
          {Array.from({ length: cols }).map((__, colIndex) => (
            <Skeleton key={colIndex} className="h-10 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- Spinner
export function Spinner({ className }: { className?: string }) {
  return (
    <Loader2 className={cn("size-5 animate-spin text-muted-foreground", className)} aria-label="Yuklanmoqda" />
  );
}

// ---------------------------------------------------------------- Rating
export function Rating({
  value,
  count,
  size = 14,
  className,
}: {
  value: number;
  count?: number;
  size?: number;
  className?: string;
}) {
  const rounded = Math.round(Number(value ?? 0) * 2) / 2;

  return (
    <span className={cn("inline-flex items-center gap-1 text-sm", className)}>
      <span className="font-semibold text-accent-foreground">{Number(value ?? 0).toFixed(1)}</span>
      <span className="flex" aria-label={`Reyting ${rounded} / 5`}>
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            width={size}
            height={size}
            className={cn(
              star <= rounded ? "fill-accent-500 text-accent-500" : "text-muted-foreground/40",
            )}
          />
        ))}
      </span>
      {count !== undefined ? (
        <span className="text-xs text-muted-foreground">({count})</span>
      ) : null}
    </span>
  );
}

// ---------------------------------------------------------------- Avatar
export function Avatar({
  name,
  src,
  size = 36,
  className,
}: {
  name?: string | null;
  src?: string | null;
  size?: number;
  className?: string;
}) {
  const label = (name ?? "?")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");

  if (src) {
    return (
      <img
        src={src}
        alt={name ?? "Avatar"}
        width={size}
        height={size}
        className={cn("shrink-0 rounded-full object-cover", className)}
        style={{ width: size, height: size }}
      />
    );
  }

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full bg-primary/10 font-semibold text-primary",
        className,
      )}
      style={{ width: size, height: size, fontSize: size * 0.38 }}
      aria-hidden
    >
      {label}
    </span>
  );
}

// ---------------------------------------------------------------- Accordion
export function Accordion({
  title,
  subtitle,
  defaultOpen = false,
  children,
  className,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  const [open, setOpen] = React.useState(defaultOpen);

  return (
    <div className={cn("overflow-hidden rounded-lg border bg-card", className)}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-muted/60"
      >
        <span className="min-w-0">
          <span className="block truncate font-medium">{title}</span>
          {subtitle ? (
            <span className="block text-xs text-muted-foreground">{subtitle}</span>
          ) : null}
        </span>
        <ChevronDown
          className={cn("size-4 shrink-0 transition-transform", open && "rotate-180")}
          aria-hidden
        />
      </button>
      {open ? <div className="border-t px-4 py-3">{children}</div> : null}
    </div>
  );
}

// ---------------------------------------------------------------- Tabs
export function Tabs({
  tabs,
  active,
  onChange,
  className,
}: {
  tabs: Array<{ id: string; label: string; count?: number }>;
  active: string;
  onChange: (id: string) => void;
  className?: string;
}) {
  return (
    <div className={cn("flex gap-1 overflow-x-auto border-b scrollbar-thin", className)} role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={active === tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            "-mb-px shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
            active === tab.id
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:border-border hover:text-foreground",
          )}
        >
          {tab.label}
          {tab.count !== undefined ? (
            <span className="ml-1.5 rounded-full bg-muted px-1.5 py-0.5 text-2xs tabular-nums">
              {tab.count}
            </span>
          ) : null}
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- Empty state
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center px-6 py-14 text-center", className)}>
      {Icon ? (
        <span className="mb-4 flex size-14 items-center justify-center rounded-2xl bg-muted">
          <Icon className="size-6 text-muted-foreground" />
        </span>
      ) : null}
      <h3 className="text-base font-semibold">{title}</h3>
      {description ? (
        <p className="mt-1.5 max-w-md text-sm text-muted-foreground">{description}</p>
      ) : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

// ---------------------------------------------------------------- Alert
export function Alert({
  variant = "info",
  title,
  children,
  className,
}: {
  variant?: "info" | "success" | "warning" | "error";
  title?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  const styles = {
    info: "border-primary/25 bg-primary/5 text-foreground",
    success: "border-secondary/30 bg-secondary/5 text-foreground",
    warning: "border-accent/35 bg-accent/10 text-foreground",
    error: "border-destructive/30 bg-destructive/5 text-foreground",
  }[variant];

  return (
    <div className={cn("rounded-lg border px-4 py-3 text-sm", styles, className)} role="alert">
      {title ? <p className="mb-0.5 font-semibold">{title}</p> : null}
      {children}
    </div>
  );
}

// ---------------------------------------------------------------- Modal
export function Modal({
  open,
  onClose,
  title,
  children,
  footer,
  size = "default",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: "default" | "lg";
}) {
  React.useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          "relative z-10 max-h-[92vh] w-full overflow-y-auto rounded-t-2xl bg-card p-5 shadow-xl sm:rounded-2xl scrollbar-thin",
          size === "lg" ? "sm:max-w-3xl" : "sm:max-w-lg",
        )}
      >
        <h2 className="mb-4 text-lg font-semibold">{title}</h2>
        {children}
        {footer ? <div className="mt-6 flex justify-end gap-3">{footer}</div> : null}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Pagination
export function Pagination({
  page,
  pages,
  onChange,
  className,
}: {
  page: number;
  pages: number;
  onChange: (page: number) => void;
  className?: string;
}) {
  if (pages <= 1) return null;

  const window = 2;
  const numbers: (number | "…")[] = [];
  for (let index = 1; index <= pages; index += 1) {
    if (index === 1 || index === pages || Math.abs(index - page) <= window) {
      numbers.push(index);
    } else if (numbers[numbers.length - 1] !== "…") {
      numbers.push("…");
    }
  }

  return (
    <nav className={cn("flex items-center justify-center gap-1.5", className)} aria-label="Sahifalar">
      <button
        type="button"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
        className="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40"
      >
        Oldingi
      </button>
      {numbers.map((item, index) =>
        item === "…" ? (
          <span key={`gap-${index}`} className="px-2 text-muted-foreground">
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            onClick={() => onChange(item)}
            aria-current={item === page ? "page" : undefined}
            className={cn(
              "min-w-9 rounded-lg border px-3 py-1.5 text-sm tabular-nums",
              item === page && "border-primary bg-primary text-primary-foreground",
            )}
          >
            {item}
          </button>
        ),
      )}
      <button
        type="button"
        onClick={() => onChange(page + 1)}
        disabled={page >= pages}
        className="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-40"
      >
        Keyingi
      </button>
    </nav>
  );
}
