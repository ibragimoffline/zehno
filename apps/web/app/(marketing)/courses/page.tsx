"use client";

import { useQuery } from "@tanstack/react-query";
import { Filter, SearchX, SlidersHorizontal, X } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import * as React from "react";

import { CourseCard } from "@/components/course/course-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox, Input, Select } from "@/components/ui/input";
import { CourseCardSkeleton, EmptyState, Pagination } from "@/components/ui/misc";
import { api } from "@/lib/api-client";
import type { Category, CourseCard as CourseCardType, Page } from "@/lib/types";
import { LANGUAGE_LABELS, LEVEL_LABELS, cn, formatNumber } from "@/lib/utils";

const SORT_OPTIONS = [
  { value: "newest", label: "Eng yangi" },
  { value: "popular", label: "Mashhurligi bo'yicha" },
  { value: "rating", label: "Reyting bo'yicha" },
  { value: "price_asc", label: "Narx: arzondan" },
  { value: "price_desc", label: "Narx: qimmatdan" },
];

function CatalogContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [filtersOpen, setFiltersOpen] = React.useState(false);
  const [searchInput, setSearchInput] = React.useState(searchParams.get("search") ?? "");

  const filters = React.useMemo(
    () => ({
      search: searchParams.get("search") ?? undefined,
      category: searchParams.get("category") ?? undefined,
      level: searchParams.get("level") ?? undefined,
      language: searchParams.get("language") ?? undefined,
      price_min: searchParams.get("price_min") ?? undefined,
      price_max: searchParams.get("price_max") ?? undefined,
      is_free: searchParams.get("is_free") ?? undefined,
      min_rating: searchParams.get("min_rating") ?? undefined,
      sort: searchParams.get("sort") ?? "newest",
      page: Number(searchParams.get("page") ?? 1),
    }),
    [searchParams],
  );

  const setParam = (key: string, value: string | undefined) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value === undefined || value === "") params.delete(key);
    else params.set(key, value);
    if (key !== "page") params.delete("page");
    router.push(`/courses?${params.toString()}`);
  };

  const resetFilters = () => {
    setSearchInput("");
    router.push("/courses");
  };

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<Category[]>("/categories", { auth: false }),
    staleTime: 10 * 60_000,
  });

  const { data, isLoading, isError } = useQuery({
    queryKey: ["courses", filters],
    queryFn: () =>
      api.get<Page<CourseCardType>>("/courses", {
        query: { ...filters, per_page: 12 },
      }),
  });

  const activeFilterCount = [
    filters.category,
    filters.level,
    filters.language,
    filters.price_min,
    filters.price_max,
    filters.is_free,
    filters.min_rating,
  ].filter(Boolean).length;

  return (
    <div className="container-page py-8">
      <header className="mb-6">
        <h1 className="text-3xl">Kurs katalogi</h1>
        <p className="mt-1.5 text-muted-foreground">
          {data ? `${formatNumber(data.total)} ta kurs topildi` : "Kurslar yuklanmoqda..."}
        </p>
      </header>

      {/* Qidiruv + saralash */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <form
          className="flex-1"
          onSubmit={(event) => {
            event.preventDefault();
            setParam("search", searchInput.trim() || undefined);
          }}
        >
          <Input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Kurs nomi, mavzu yoki ustoz..."
            aria-label="Qidiruv"
          />
        </form>

        <Select
          value={filters.sort}
          onChange={(event) => setParam("sort", event.target.value)}
          className="sm:w-56"
          aria-label="Saralash"
        >
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>

        <Button
          variant="outline"
          onClick={() => setFiltersOpen((prev) => !prev)}
          className="lg:hidden"
        >
          <SlidersHorizontal /> Filtr
          {activeFilterCount > 0 ? <Badge variant="default">{activeFilterCount}</Badge> : null}
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        {/* Filtr paneli */}
        <aside
          className={cn(
            "space-y-6 lg:block",
            filtersOpen
              ? "rounded-xl border bg-card p-5"
              : "hidden",
          )}
        >
          <div className="flex items-center justify-between lg:hidden">
            <span className="font-semibold">Filtrlar</span>
            <button type="button" onClick={() => setFiltersOpen(false)} aria-label="Yopish">
              <X className="size-4" />
            </button>
          </div>

          {activeFilterCount > 0 ? (
            <Button variant="ghost" size="sm" onClick={resetFilters} className="w-full">
              <X /> Filtrlarni tozalash ({activeFilterCount})
            </Button>
          ) : null}

          <FilterGroup title="Kategoriya">
            <div className="space-y-1.5">
              <FilterRadio
                label="Barchasi"
                checked={!filters.category}
                onChange={() => setParam("category", undefined)}
              />
              {categories.map((category) => (
                <FilterRadio
                  key={category.id}
                  label={`${category.name} (${category.courses_count})`}
                  checked={filters.category === category.slug}
                  onChange={() => setParam("category", category.slug)}
                />
              ))}
            </div>
          </FilterGroup>

          <FilterGroup title="Daraja">
            <div className="space-y-1.5">
              <FilterRadio
                label="Barchasi"
                checked={!filters.level}
                onChange={() => setParam("level", undefined)}
              />
              {Object.entries(LEVEL_LABELS).map(([value, label]) => (
                <FilterRadio
                  key={value}
                  label={label}
                  checked={filters.level === value}
                  onChange={() => setParam("level", value)}
                />
              ))}
            </div>
          </FilterGroup>

          <FilterGroup title="Til">
            <div className="space-y-1.5">
              <FilterRadio
                label="Barchasi"
                checked={!filters.language}
                onChange={() => setParam("language", undefined)}
              />
              {Object.entries(LANGUAGE_LABELS).map(([value, label]) => (
                <FilterRadio
                  key={value}
                  label={label}
                  checked={filters.language === value}
                  onChange={() => setParam("language", value)}
                />
              ))}
            </div>
          </FilterGroup>

          <FilterGroup title="Narx">
            <label className="mb-3 flex cursor-pointer items-center gap-2 text-sm">
              <Checkbox
                checked={filters.is_free === "true"}
                onChange={(event) =>
                  setParam("is_free", event.target.checked ? "true" : undefined)
                }
              />
              Faqat bepul kurslar
            </label>

            <div className="flex items-center gap-2">
              <Input
                type="number"
                min={0}
                placeholder="dan"
                defaultValue={filters.price_min ?? ""}
                onBlur={(event) => setParam("price_min", event.target.value || undefined)}
                aria-label="Minimal narx"
              />
              <span className="text-muted-foreground">—</span>
              <Input
                type="number"
                min={0}
                placeholder="gacha"
                defaultValue={filters.price_max ?? ""}
                onBlur={(event) => setParam("price_max", event.target.value || undefined)}
                aria-label="Maksimal narx"
              />
            </div>
          </FilterGroup>

          <FilterGroup title="Reyting">
            <div className="space-y-1.5">
              <FilterRadio
                label="Barchasi"
                checked={!filters.min_rating}
                onChange={() => setParam("min_rating", undefined)}
              />
              {["4.5", "4", "3.5"].map((rating) => (
                <FilterRadio
                  key={rating}
                  label={`${rating} va yuqori`}
                  checked={filters.min_rating === rating}
                  onChange={() => setParam("min_rating", rating)}
                />
              ))}
            </div>
          </FilterGroup>
        </aside>

        {/* Natijalar */}
        <div>
          {isLoading ? (
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <CourseCardSkeleton key={index} />
              ))}
            </div>
          ) : isError ? (
            <EmptyState
              icon={SearchX}
              title="Kurslarni yuklab bo'lmadi"
              description="Serverga ulanishda muammo bo'ldi. Sahifani yangilab ko'ring."
              action={
                <Button onClick={() => window.location.reload()} variant="outline">
                  Qayta urinish
                </Button>
              }
            />
          ) : data && data.items.length > 0 ? (
            <>
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {data.items.map((course) => (
                  <CourseCard key={course.id} course={course} />
                ))}
              </div>
              <Pagination
                page={data.page}
                pages={data.pages}
                onChange={(page) => setParam("page", String(page))}
                className="mt-9"
              />
            </>
          ) : (
            <EmptyState
              icon={Filter}
              title="Hech narsa topilmadi"
              description="Filtr shartlarini yumshatib yoki boshqa kalit so'z bilan qidirib ko'ring."
              action={
                <Button variant="outline" onClick={resetFilters}>
                  Filtrlarni tozalash
                </Button>
              }
            />
          )}
        </div>
      </div>
    </div>
  );
}

function FilterGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="mb-2.5 text-sm font-semibold">{title}</h2>
      {children}
    </div>
  );
}

function FilterRadio({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
      <input
        type="radio"
        checked={checked}
        onChange={onChange}
        className="size-4 accent-primary"
      />
      <span className={cn(checked && "font-medium text-foreground")}>{label}</span>
    </label>
  );
}

export default function CatalogPage() {
  return (
    <React.Suspense
      fallback={
        <div className="container-page grid gap-5 py-10 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <CourseCardSkeleton key={index} />
          ))}
        </div>
      }
    >
      <CatalogContent />
    </React.Suspense>
  );
}
