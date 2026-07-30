import { type VariantProps, cva } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary/10 text-primary",
        secondary: "border-transparent bg-secondary/10 text-secondary",
        accent: "border-transparent bg-accent/15 text-accent-foreground",
        outline: "border-border text-foreground",
        muted: "border-transparent bg-muted text-muted-foreground",
        success: "border-transparent bg-success/10 text-success",
        warning: "border-transparent bg-warning/15 text-warning-foreground",
        destructive: "border-transparent bg-destructive/10 text-destructive",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

/** Kurs holati uchun rangli belgi */
export function StatusBadge({ status, label }: { status: string; label: string }) {
  const variant: BadgeProps["variant"] =
    status === "published" || status === "paid" || status === "completed" || status === "ok"
      ? "success"
      : status === "pending" || status === "processing" || status === "degraded"
        ? "warning"
        : status === "rejected" || status === "failed" || status === "error"
          ? "destructive"
          : "muted";

  return <Badge variant={variant}>{label}</Badge>;
}

export { badgeVariants };
