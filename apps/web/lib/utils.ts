import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(value: string | number | null | undefined, currency = "UZS"): string {
  const amount = Number(value ?? 0);
  if (!Number.isFinite(amount)) return "—";
  if (amount <= 0) return "Bepul";

  const formatted = new Intl.NumberFormat("uz-UZ", { maximumFractionDigits: 0 }).format(amount);
  return currency === "UZS" ? `${formatted} so'm` : `${formatted} ${currency}`;
}

export function formatCompact(value: string | number | null | undefined): string {
  const amount = Number(value ?? 0);
  if (!Number.isFinite(amount)) return "0";
  if (amount >= 1_000_000_000) return `${(amount / 1_000_000_000).toFixed(2)} mlrd`;
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(2)} mln`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(1)} ming`;
  return new Intl.NumberFormat("uz-UZ").format(amount);
}

export function formatNumber(value: number | null | undefined): string {
  return new Intl.NumberFormat("uz-UZ").format(Number(value ?? 0));
}

export function formatDuration(seconds: number | null | undefined): string {
  const total = Math.max(0, Math.floor(Number(seconds ?? 0)));
  if (total === 0) return "0 daq";

  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);

  if (hours > 0) return minutes > 0 ? `${hours} s ${minutes} daq` : `${hours} s`;
  if (minutes > 0) return `${minutes} daq`;
  return `${total} sek`;
}

export function formatTimecode(seconds: number | null | undefined): string {
  const total = Math.max(0, Math.floor(Number(seconds ?? 0)));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return hours > 0 ? `${hours}:${pad(minutes)}:${pad(secs)}` : `${minutes}:${pad(secs)}`;
}

export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return "—";
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("uz-UZ", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}

export function formatDateTime(value: string | Date | null | undefined): string {
  if (!value) return "—";
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("uz-UZ", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatRelative(value: string | Date | null | undefined): string {
  if (!value) return "—";
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "—";

  const diff = Math.floor((Date.now() - date.getTime()) / 1000);
  if (diff < 60) return "hozir";
  if (diff < 3600) return `${Math.floor(diff / 60)} daq. oldin`;
  if (diff < 86_400) return `${Math.floor(diff / 3600)} soat oldin`;
  if (diff < 604_800) return `${Math.floor(diff / 86_400)} kun oldin`;
  return formatDate(date);
}

export const LEVEL_LABELS: Record<string, string> = {
  beginner: "Boshlang'ich",
  intermediate: "O'rta",
  advanced: "Yuqori",
};

export const LANGUAGE_LABELS: Record<string, string> = {
  uz: "O'zbek",
  ru: "Rus",
  en: "Ingliz",
};

export const ROLE_LABELS: Record<string, string> = {
  student: "Talaba",
  teacher: "Ustoz",
  org_admin: "Tashkilot admini",
  b2b_manager: "B2B menejer",
  admin: "Super admin",
};

export const COURSE_STATUS_LABELS: Record<string, string> = {
  draft: "Qoralama",
  pending: "Moderatsiyada",
  published: "Nashr etilgan",
  rejected: "Rad etilgan",
  archived: "Arxivlangan",
};

export const ORDER_STATUS_LABELS: Record<string, string> = {
  pending: "Kutilmoqda",
  paid: "To'langan",
  failed: "Muvaffaqiyatsiz",
  cancelled: "Bekor qilingan",
  refunded: "Qaytarilgan",
};

export const ENROLLMENT_STATUS_LABELS: Record<string, string> = {
  active: "Davom etmoqda",
  completed: "Tugatilgan",
  expired: "Muddati tugagan",
  cancelled: "Bekor qilingan",
};

export const ORGANIZATION_TYPE_LABELS: Record<string, string> = {
  school: "Maktab",
  teacher: "Xususiy ustoz",
  training_center: "O'quv markaz",
  b2b_client: "B2B mijoz",
};

export function initials(name: string | null | undefined): string {
  if (!name) return "?";
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function discountPercent(price: string | number, discount?: string | number | null): number {
  const base = Number(price);
  const sale = Number(discount ?? 0);
  if (!base || !sale || sale >= base) return 0;
  return Math.round((1 - sale / base) * 100);
}

export function clampPercent(value: number | null | undefined): number {
  return Math.min(100, Math.max(0, Math.round(Number(value ?? 0))));
}

export function debounce<Args extends unknown[]>(fn: (...args: Args) => void, delay = 400) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return (...args: Args) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/['’]/g, "")
    .replace(/[^a-z0-9Ѐ-ӿ]+/g, "-")
    .replace(/(^-|-$)/g, "");
}
