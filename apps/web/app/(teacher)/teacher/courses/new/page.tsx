"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, Plus, Upload, X } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Checkbox, Field, Input, Select, Textarea } from "@/components/ui/input";
import { Alert } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { Category, CourseAdminSummary } from "@/lib/types";
import { LANGUAGE_LABELS, LEVEL_LABELS, cn } from "@/lib/utils";

const STEPS = [
  { id: 1, label: "Umumiy" },
  { id: 2, label: "Dastur" },
  { id: 3, label: "Video" },
  { id: 4, label: "Narx" },
];

interface DraftForm {
  title: string;
  subtitle: string;
  description: string;
  category_id: string;
  level: string;
  language: string;
  cover_url: string;
  what_you_learn: string[];
  requirements: string[];
  price: string;
  discount_price: string;
  has_certificate: boolean;
  sequential_progress: boolean;
}

const EMPTY_FORM: DraftForm = {
  title: "",
  subtitle: "",
  description: "",
  category_id: "",
  level: "beginner",
  language: "uz",
  cover_url: "",
  what_you_learn: [""],
  requirements: [""],
  price: "0",
  discount_price: "",
  has_certificate: true,
  sequential_progress: false,
};

export default function NewCoursePage() {
  const router = useRouter();
  const [step, setStep] = React.useState(1);
  const [form, setForm] = React.useState<DraftForm>(EMPTY_FORM);
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [uploading, setUploading] = React.useState(false);

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<Category[]>("/categories", { auth: false }),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.post<CourseAdminSummary>("/teacher/courses", {
        title: form.title.trim(),
        subtitle: form.subtitle.trim() || undefined,
        description: form.description.trim() || undefined,
        category_id: form.category_id || undefined,
        level: form.level,
        language: form.language,
        cover_url: form.cover_url || undefined,
        price: form.price || "0",
        discount_price: form.discount_price || undefined,
        what_you_learn: form.what_you_learn.filter((item) => item.trim()),
        requirements: form.requirements.filter((item) => item.trim()),
        has_certificate: form.has_certificate,
        sequential_progress: form.sequential_progress,
      }),
    onSuccess: (course) => {
      toast.success("Kurs qoralamasi yaratildi — endi modul va darslarni qo'shing");
      router.push(`/teacher/courses/${course.id}`);
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Kurs yaratilmadi");
    },
  });

  const validateStep1 = () => {
    const next: Record<string, string> = {};
    if (form.title.trim().length < 3) next.title = "Kurs nomi kamida 3 belgidan iborat bo'lsin";
    if (!form.category_id) next.category_id = "Kategoriyani tanlang";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const uploadCover = async (file: File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await api.post<{ url: string }>("/uploads", formData, {
        query: { folder: "covers" },
      });
      setForm((prev) => ({ ...prev, cover_url: result.url }));
      toast.success("Muqova yuklandi");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Fayl yuklanmadi");
    } finally {
      setUploading(false);
    }
  };

  const updateList = (key: "what_you_learn" | "requirements", index: number, value: string) => {
    setForm((prev) => {
      const list = [...prev[key]];
      list[index] = value;
      return { ...prev, [key]: list };
    });
  };

  return (
    <div className="mx-auto max-w-3xl">
      {/* Bosqichlar chizig'i */}
      <ol className="mb-7 flex items-center gap-2">
        {STEPS.map((item, index) => (
          <li key={item.id} className="flex flex-1 items-center gap-2">
            <span
              className={cn(
                "flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
                step > item.id
                  ? "bg-secondary text-secondary-foreground"
                  : step === item.id
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground",
              )}
            >
              {step > item.id ? <Check className="size-4" /> : item.id}
            </span>
            <span
              className={cn(
                "hidden text-sm font-medium sm:block",
                step === item.id ? "text-foreground" : "text-muted-foreground",
              )}
            >
              {item.label}
            </span>
            {index < STEPS.length - 1 ? (
              <span
                className={cn(
                  "h-0.5 flex-1 rounded",
                  step > item.id ? "bg-secondary" : "bg-muted",
                )}
              />
            ) : null}
          </li>
        ))}
      </ol>

      <div className="rounded-xl border bg-card p-6">
        {/* ===== 1-qadam: umumiy ma'lumot ===== */}
        {step === 1 ? (
          <div className="space-y-5">
            <h2 className="text-xl">Umumiy ma&apos;lumot</h2>

            <Field label="Kurs nomi" htmlFor="title" error={errors.title} required>
              <Input
                value={form.title}
                onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
                placeholder="Masalan: Frontend dasturlash: HTML, CSS va JavaScript"
              />
            </Field>

            <Field
              label="Qisqa tavsif (subtitle)"
              htmlFor="subtitle"
              hint="Katalog kartochkasida ko'rinadi — 1-2 gap"
            >
              <Input
                value={form.subtitle}
                onChange={(event) => setForm((prev) => ({ ...prev, subtitle: event.target.value }))}
                placeholder="Noldan boshlab zamonaviy veb-saytlar yaratishni o'rganing"
              />
            </Field>

            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Kategoriya" htmlFor="category_id" error={errors.category_id} required>
                <Select
                  value={form.category_id}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, category_id: event.target.value }))
                  }
                >
                  <option value="">Tanlash…</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </Select>
              </Field>

              <Field label="Daraja" htmlFor="level">
                <Select
                  value={form.level}
                  onChange={(event) => setForm((prev) => ({ ...prev, level: event.target.value }))}
                >
                  {Object.entries(LEVEL_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </Select>
              </Field>

              <Field label="Til" htmlFor="language">
                <Select
                  value={form.language}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, language: event.target.value }))
                  }
                >
                  {Object.entries(LANGUAGE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>

            <Field label="To'liq tavsif" htmlFor="description" hint="Kurs kimga, nima uchun kerak">
              <Textarea
                rows={6}
                value={form.description}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, description: event.target.value }))
                }
                placeholder="Bu kursda siz..."
              />
            </Field>

            <div>
              <span className="mb-1.5 block text-sm font-medium">Muqova rasm</span>
              <div className="flex flex-wrap items-center gap-3">
                {form.cover_url ? (
                  <div className="relative">
                    <img
                      src={form.cover_url}
                      alt="Muqova"
                      className="h-24 w-40 rounded-lg border object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => setForm((prev) => ({ ...prev, cover_url: "" }))}
                      className="absolute -right-2 -top-2 rounded-full bg-destructive p-1 text-destructive-foreground"
                      aria-label="Rasmni o'chirish"
                    >
                      <X className="size-3" />
                    </button>
                  </div>
                ) : null}

                <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed px-4 py-3 text-sm hover:bg-muted">
                  <Upload className="size-4" />
                  {uploading ? "Yuklanmoqda..." : "Rasm yuklash"}
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    className="hidden"
                    disabled={uploading}
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      if (file) void uploadCover(file);
                    }}
                  />
                </label>
              </div>
              <p className="mt-1.5 text-xs text-muted-foreground">
                Tavsiya: 1280×720 px, JPG/PNG/WebP, 5 MB gacha
              </p>
            </div>
          </div>
        ) : null}

        {/* ===== 2-qadam: nima o'rganadi ===== */}
        {step === 2 ? (
          <div className="space-y-6">
            <h2 className="text-xl">Kurs dasturi haqida</h2>
            <Alert variant="info">
              Modullar va darslar keyingi qadamda (kurs yaratilgandan so&apos;ng) drag &amp; drop
              orqali qo&apos;shiladi. Hozir kurs natijalarini kiriting.
            </Alert>

            <ListEditor
              label="Nima o'rganadi"
              hint="Har bir qatorda bitta natija"
              items={form.what_you_learn}
              onChange={(index, value) => updateList("what_you_learn", index, value)}
              onAdd={() =>
                setForm((prev) => ({ ...prev, what_you_learn: [...prev.what_you_learn, ""] }))
              }
              onRemove={(index) =>
                setForm((prev) => ({
                  ...prev,
                  what_you_learn: prev.what_you_learn.filter((_, i) => i !== index),
                }))
              }
              placeholder="CSS Flexbox va Grid orqali istalgan layoutni yasash"
            />

            <ListEditor
              label="Talablar"
              hint="Kursni boshlash uchun nima kerak"
              items={form.requirements}
              onChange={(index, value) => updateList("requirements", index, value)}
              onAdd={() =>
                setForm((prev) => ({ ...prev, requirements: [...prev.requirements, ""] }))
              }
              onRemove={(index) =>
                setForm((prev) => ({
                  ...prev,
                  requirements: prev.requirements.filter((_, i) => i !== index),
                }))
              }
              placeholder="Kompyuter va internet aloqasi"
            />
          </div>
        ) : null}

        {/* ===== 3-qadam: video sozlamalari ===== */}
        {step === 3 ? (
          <div className="space-y-5">
            <h2 className="text-xl">Kontent sozlamalari</h2>

            <label className="flex cursor-pointer items-start gap-3 rounded-lg border p-4">
              <Checkbox
                checked={form.has_certificate}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, has_certificate: event.target.checked }))
                }
              />
              <span>
                <span className="block font-medium">Sertifikat berilsin</span>
                <span className="block text-sm text-muted-foreground">
                  Kurs 100% tugallanganda talabaga QR kodli PDF sertifikat avtomatik generatsiya
                  qilinadi
                </span>
              </span>
            </label>

            <label className="flex cursor-pointer items-start gap-3 rounded-lg border p-4">
              <Checkbox
                checked={form.sequential_progress}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, sequential_progress: event.target.checked }))
                }
              />
              <span>
                <span className="block font-medium">Darslar ketma-ket o&apos;tilsin</span>
                <span className="block text-sm text-muted-foreground">
                  Talaba oldingi darsni tugatmasa, keyingisi qulflangan bo&apos;ladi
                </span>
              </span>
            </label>

            <Alert variant="info" title="Videolarni qanday yuklash">
              Kurs yaratilgandan keyin har bir dars uchun video yuklaysiz. Video tanlangan
              provayderga (PeerTube / Kinescope / Bunny) yuboriladi va faqat sotib olgan talabalarga
              vaqtinchalik (10-15 daqiqalik) havola orqali ko&apos;rsatiladi.
            </Alert>
          </div>
        ) : null}

        {/* ===== 4-qadam: narx ===== */}
        {step === 4 ? (
          <div className="space-y-5">
            <h2 className="text-xl">Narx va nashr</h2>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Narx (UZS)" htmlFor="price" hint="0 kiritsangiz kurs bepul bo'ladi">
                <Input
                  type="number"
                  min={0}
                  step={1000}
                  value={form.price}
                  onChange={(event) => setForm((prev) => ({ ...prev, price: event.target.value }))}
                />
              </Field>

              <Field
                label="Chegirma narxi (UZS)"
                htmlFor="discount_price"
                hint="Ixtiyoriy — asosiy narxdan kichik bo'lishi kerak"
              >
                <Input
                  type="number"
                  min={0}
                  step={1000}
                  value={form.discount_price}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, discount_price: event.target.value }))
                  }
                />
              </Field>
            </div>

            <div className="rounded-lg bg-muted/50 p-4 text-sm">
              <p className="font-medium">Daromad hisobi</p>
              <p className="mt-1.5 text-muted-foreground">
                Har bir sotuvdan platforma komissiyasi <strong>15%</strong> ushlanadi. Masalan{" "}
                {Number(form.discount_price || form.price || 0).toLocaleString("uz-UZ")} so&apos;m
                narxda sizga{" "}
                <strong className="text-foreground">
                  {Math.round(Number(form.discount_price || form.price || 0) * 0.85).toLocaleString(
                    "uz-UZ",
                  )}{" "}
                  so&apos;m
                </strong>{" "}
                tushadi.
              </p>
            </div>

            <Alert variant="warning" title="Keyingi qadam">
              Kurs <strong>qoralama</strong> holatida yaratiladi. Modul va darslarni qo&apos;shib,
              video yuklaganingizdan keyin &laquo;Moderatsiyaga yuborish&raquo; tugmasini bosasiz.
            </Alert>
          </div>
        ) : null}

        {/* Navigatsiya */}
        <div className="mt-7 flex items-center justify-between gap-3 border-t pt-5">
          <Button
            variant="outline"
            onClick={() => (step === 1 ? router.push("/teacher/courses") : setStep(step - 1))}
          >
            <ArrowLeft /> {step === 1 ? "Bekor qilish" : "Orqaga"}
          </Button>

          {step < 4 ? (
            <Button
              onClick={() => {
                if (step === 1 && !validateStep1()) return;
                setStep(step + 1);
              }}
            >
              Keyingi <ArrowRight />
            </Button>
          ) : (
            <Button loading={createMutation.isPending} onClick={() => createMutation.mutate()}>
              <Check /> Kursni yaratish
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function ListEditor({
  label,
  hint,
  items,
  onChange,
  onAdd,
  onRemove,
  placeholder,
}: {
  label: string;
  hint?: string;
  items: string[];
  onChange: (index: number, value: string) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <span className="block text-sm font-medium">{label}</span>
      {hint ? <span className="mb-2 block text-xs text-muted-foreground">{hint}</span> : null}

      <div className="mt-2 space-y-2">
        {items.map((item, index) => (
          <div key={index} className="flex gap-2">
            <Input
              value={item}
              onChange={(event) => onChange(index, event.target.value)}
              placeholder={placeholder}
              aria-label={`${label} ${index + 1}`}
            />
            {items.length > 1 ? (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onRemove(index)}
                aria-label="Qatorni o'chirish"
              >
                <X className="text-destructive" />
              </Button>
            ) : null}
          </div>
        ))}
      </div>

      <Button variant="ghost" size="sm" onClick={onAdd} className="mt-2">
        <Plus /> Qator qo&apos;shish
      </Button>
    </div>
  );
}
