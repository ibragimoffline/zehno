"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, FileSpreadsheet, Upload, Users } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Checkbox, Field, Textarea } from "@/components/ui/input";
import { Alert } from "@/components/ui/misc";
import { ApiError, api, apiBaseUrl, tokenStore } from "@/lib/api-client";
import type { CourseCard, Page } from "@/lib/types";
import { cn, formatPrice } from "@/lib/utils";

interface BulkResult {
  enrolled: number;
  created_users: number;
  skipped: string[];
  seats_used: number;
  seats_available?: number | null;
}

export default function BulkEnrollPage() {
  const [selected, setSelected] = React.useState<string[]>([]);
  const [emailsText, setEmailsText] = React.useState("");
  const [result, setResult] = React.useState<BulkResult | null>(null);
  const [uploading, setUploading] = React.useState(false);

  const { data: courses } = useQuery({
    queryKey: ["courses", "b2b-picker"],
    queryFn: () =>
      api.get<Page<CourseCard>>("/courses", { query: { per_page: 50, sort: "popular" } }),
  });

  const emails = React.useMemo(
    () =>
      emailsText
        .split(/[\s,;]+/)
        .map((value) => value.trim().toLowerCase())
        .filter((value) => value.includes("@")),
    [emailsText],
  );

  const enrollMutation = useMutation({
    mutationFn: () =>
      api.post<BulkResult>("/b2b/bulk-enroll", {
        course_ids: selected,
        emails,
        send_invites: true,
      }),
    onSuccess: (data) => {
      setResult(data);
      toast.success(`${data.enrolled} ta yozilish yaratildi`);
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.message : "Yozib bo'lmadi"),
  });

  const uploadCsv = async (file: File) => {
    if (selected.length === 0) {
      toast.error("Avval kamida bitta kursni tanlang");
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const token = tokenStore.get();
      const response = await fetch(
        `${apiBaseUrl()}/b2b/bulk-enroll/csv?course_ids=${selected.join(",")}`,
        {
          method: "POST",
          body: formData,
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          credentials: "include",
        },
      );
      if (!response.ok) throw new Error("CSV qayta ishlanmadi");
      const data = (await response.json()) as BulkResult;
      setResult(data);
      toast.success(`${data.enrolled} ta yozilish yaratildi`);
    } catch {
      toast.error("CSV faylni yuklab bo'lmadi");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      {/* 1. Kurs tanlash */}
      <section className="rounded-xl border bg-card p-5">
        <h2 className="text-lg font-semibold">1. Kurslarni tanlang</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Xodimlaringiz bir vaqtda bir nechta kursga yozilishi mumkin
        </p>

        <div className="mt-4 max-h-72 space-y-2 overflow-y-auto scrollbar-thin">
          {courses?.items.map((course) => {
            const checked = selected.includes(course.id);
            return (
              <label
                key={course.id}
                className={cn(
                  "flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors",
                  checked ? "border-primary bg-primary/5" : "hover:bg-muted",
                )}
              >
                <Checkbox
                  checked={checked}
                  onChange={() =>
                    setSelected((prev) =>
                      checked ? prev.filter((id) => id !== course.id) : [...prev, course.id],
                    )
                  }
                />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium">{course.title}</span>
                  <span className="block text-xs text-muted-foreground">
                    {course.lessons_count} dars ·{" "}
                    {formatPrice(course.discount_price ?? course.price, course.currency)}
                  </span>
                </span>
              </label>
            );
          })}
        </div>

        {selected.length > 0 ? (
          <p className="mt-3 text-sm font-medium text-primary">
            {selected.length} kurs tanlandi
          </p>
        ) : null}
      </section>

      {/* 2. Xodimlar */}
      <section className="rounded-xl border bg-card p-5">
        <h2 className="text-lg font-semibold">2. Xodimlarni kiriting</h2>

        <Field
          label="Email manzillar"
          htmlFor="emails"
          hint="Vergul, bo'sh joy yoki yangi qatordan ajratib yozing"
          className="mt-4"
        >
          <Textarea
            rows={6}
            value={emailsText}
            onChange={(event) => setEmailsText(event.target.value)}
            placeholder={"ali@company.uz\nolim@company.uz\nmalika@company.uz"}
          />
        </Field>

        {emails.length > 0 ? (
          <p className="mt-2 text-sm text-secondary">
            {emails.length} ta yaroqli email aniqlandi
          </p>
        ) : null}

        <div className="mt-5 border-t pt-5">
          <p className="mb-2.5 text-sm font-medium">Yoki CSV fayl yuklang</p>
          <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed px-4 py-3 text-sm hover:bg-muted">
            <Upload className="size-4" />
            {uploading ? "Yuklanmoqda..." : "CSV tanlash (email, ism)"}
            <input
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              disabled={uploading}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void uploadCsv(file);
              }}
            />
          </label>
          <p className="mt-1.5 text-xs text-muted-foreground">
            Format: har qatorda <code className="font-mono">email,To&apos;liq ism</code> (ism
            ixtiyoriy)
          </p>
        </div>
      </section>

      {/* 3. Yakunlash */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card p-5">
        <p className="text-sm text-muted-foreground">
          {selected.length} kurs × {emails.length} xodim ={" "}
          <strong className="text-foreground">{selected.length * emails.length}</strong> yozilish
        </p>
        <Button
          size="lg"
          loading={enrollMutation.isPending}
          disabled={selected.length === 0 || emails.length === 0}
          onClick={() => enrollMutation.mutate()}
        >
          <Users /> Kursga yozish
        </Button>
      </div>

      {/* Natija */}
      {result ? (
        <Alert variant="success" title="Yozilish yakunlandi">
          <ul className="mt-2 space-y-1 text-sm">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="size-4 text-secondary" />
              {result.enrolled} ta yozilish yaratildi
            </li>
            <li className="flex items-center gap-2">
              <Users className="size-4 text-primary" />
              {result.created_users} ta yangi hisob ochildi
            </li>
            {result.seats_available !== null && result.seats_available !== undefined ? (
              <li className="flex items-center gap-2">
                <FileSpreadsheet className="size-4 text-muted-foreground" />
                Bo&apos;sh o&apos;rinlar: {result.seats_available}
              </li>
            ) : null}
          </ul>

          {result.skipped.length > 0 ? (
            <details className="mt-3">
              <summary className="cursor-pointer text-sm font-medium">
                O&apos;tkazib yuborilgan ({result.skipped.length})
              </summary>
              <ul className="mt-2 max-h-40 space-y-0.5 overflow-y-auto text-xs text-muted-foreground scrollbar-thin">
                {result.skipped.map((item, index) => (
                  <li key={index}>• {item}</li>
                ))}
              </ul>
            </details>
          ) : null}
        </Alert>
      ) : null}
    </div>
  );
}
