import {
  Award,
  BookOpen,
  CheckCircle2,
  Clock,
  FileText,
  Globe,
  Infinity as InfinityIcon,
  PlayCircle,
  Target,
  Users,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CourseActions } from "@/components/course/course-actions";
import { CourseReviews } from "@/components/course/course-reviews";
import { Badge } from "@/components/ui/badge";
import { Accordion, Avatar, Rating } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { CourseDetail } from "@/lib/types";
import {
  LANGUAGE_LABELS,
  LEVEL_LABELS,
  formatDuration,
  formatNumber,
  formatPrice,
} from "@/lib/utils";

export const revalidate = 120;

async function loadCourse(slug: string): Promise<CourseDetail | null> {
  try {
    return await api.get<CourseDetail>(`/courses/${slug}`, { auth: false, revalidate: 120 });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const course = await loadCourse(slug).catch(() => null);
  if (!course) return { title: "Kurs topilmadi" };

  return {
    title: course.title,
    description: course.subtitle ?? course.description?.slice(0, 160) ?? undefined,
    openGraph: {
      title: course.title,
      description: course.subtitle ?? undefined,
      images: course.cover_url ? [{ url: course.cover_url }] : undefined,
    },
  };
}

export default async function CourseDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const course = await loadCourse(slug);
  if (!course) notFound();

  const totalLessons = course.modules.reduce((sum, module) => sum + module.lessons.length, 0);
  const previewLesson = course.modules
    .flatMap((module) => module.lessons)
    .find((lesson) => lesson.is_preview);

  return (
    <div>
      {/* ============ Yuqori blok ============ */}
      <section className="border-b bg-gradient-to-br from-primary-50 to-background">
        <div className="container-page grid gap-8 py-10 lg:grid-cols-[1fr_360px]">
          <div>
            <nav className="mb-4 flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
              <Link href="/courses" className="hover:text-foreground">
                Kurslar
              </Link>
              {course.category ? (
                <>
                  <span>/</span>
                  <Link
                    href={`/courses?category=${course.category.slug}`}
                    className="hover:text-foreground"
                  >
                    {course.category.name}
                  </Link>
                </>
              ) : null}
            </nav>

            <div className="mb-3 flex flex-wrap gap-2">
              {course.is_bestseller ? <Badge variant="accent">Bestseller</Badge> : null}
              <Badge variant="muted">{LEVEL_LABELS[course.level]}</Badge>
              <Badge variant="outline">
                <Globe className="size-3" /> {LANGUAGE_LABELS[course.language]}
              </Badge>
            </div>

            <h1 className="text-balance text-3xl leading-tight sm:text-4xl">{course.title}</h1>
            {course.subtitle ? (
              <p className="mt-3 text-lg text-muted-foreground">{course.subtitle}</p>
            ) : null}

            <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
              {course.rating_count > 0 ? (
                <Rating value={course.rating_avg} count={course.rating_count} />
              ) : (
                <Badge variant="secondary">Yangi kurs</Badge>
              )}
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Users className="size-4" /> {formatNumber(course.students_count)} talaba
              </span>
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <BookOpen className="size-4" /> {totalLessons} dars
              </span>
              {course.duration_seconds > 0 ? (
                <span className="flex items-center gap-1.5 text-muted-foreground">
                  <Clock className="size-4" /> {formatDuration(course.duration_seconds)}
                </span>
              ) : null}
            </div>

            {course.owner ? (
              <Link
                href={`/teachers/${course.owner.id}`}
                className="mt-5 inline-flex items-center gap-2.5 rounded-lg p-1 hover:bg-muted"
              >
                <Avatar name={course.owner.full_name} src={course.owner.avatar_url} size={40} />
                <span>
                  <span className="block text-xs text-muted-foreground">Ustoz</span>
                  <span className="block text-sm font-semibold">{course.owner.full_name}</span>
                </span>
              </Link>
            ) : null}
          </div>

          {/* Sotib olish paneli */}
          <aside className="lg:-mb-24 lg:sticky lg:top-20 lg:self-start">
            <div className="overflow-hidden rounded-2xl border bg-card shadow-card-hover">
              <div className="relative aspect-video bg-muted">
                {course.cover_url ? (
                  <img
                    src={course.cover_url}
                    alt={course.title}
                    className="size-full object-cover"
                  />
                ) : (
                  <span className="flex size-full items-center justify-center text-muted-foreground">
                    <BookOpen className="size-10" />
                  </span>
                )}
                {previewLesson ? (
                  <Link
                    href={`/courses/${course.slug}/preview/${previewLesson.id}`}
                    className="absolute inset-0 flex items-center justify-center bg-black/40 transition-colors hover:bg-black/50"
                  >
                    <span className="flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900">
                      <PlayCircle className="size-4" /> Bepul ko&apos;rish
                    </span>
                  </Link>
                ) : null}
              </div>

              <div className="p-5">
                <CourseActions course={course} />

                <ul className="mt-5 space-y-2.5 border-t pt-5 text-sm">
                  <li className="flex items-center gap-2.5">
                    <PlayCircle className="size-4 shrink-0 text-primary" />
                    {totalLessons} ta video dars
                  </li>
                  {course.modules.some((module) =>
                    module.lessons.some((lesson) => lesson.has_quiz),
                  ) ? (
                    <li className="flex items-center gap-2.5">
                      <FileText className="size-4 shrink-0 text-primary" />
                      Amaliy testlar
                    </li>
                  ) : null}
                  {course.has_certificate ? (
                    <li className="flex items-center gap-2.5">
                      <Award className="size-4 shrink-0 text-primary" />
                      QR kodli sertifikat
                    </li>
                  ) : null}
                  <li className="flex items-center gap-2.5">
                    <InfinityIcon className="size-4 shrink-0 text-primary" />
                    Umrbod kirish huquqi
                  </li>
                  <li className="flex items-center gap-2.5">
                    <Clock className="size-4 shrink-0 text-primary" />
                    O&apos;z tezligingizda o&apos;qish
                  </li>
                </ul>

                <p className="mt-4 border-t pt-4 text-center text-xs text-muted-foreground">
                  30 kunlik pulni qaytarish kafolati
                </p>
              </div>
            </div>
          </aside>
        </div>
      </section>

      {/* ============ Kontent ============ */}
      <div className="container-page grid gap-10 py-10 lg:grid-cols-[1fr_360px]">
        <div className="min-w-0 space-y-10">
          {/* Nima o'rganasiz */}
          {course.what_you_learn && course.what_you_learn.length > 0 ? (
            <section className="rounded-xl border bg-card p-6">
              <h2 className="text-xl">Nima o&apos;rganasiz</h2>
              <ul className="mt-4 grid gap-2.5 sm:grid-cols-2">
                {course.what_you_learn.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-secondary" />
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {/* Dastur */}
          <section>
            <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
              <h2 className="text-xl">Kurs dasturi</h2>
              <p className="text-sm text-muted-foreground">
                {course.modules.length} modul · {totalLessons} dars ·{" "}
                {formatDuration(course.duration_seconds)}
              </p>
            </div>

            <div className="space-y-2.5">
              {course.modules.map((module, index) => (
                <Accordion
                  key={module.id}
                  title={`${index + 1}. ${module.title}`}
                  subtitle={`${module.lessons.length} dars · ${formatDuration(module.duration_seconds)}`}
                  defaultOpen={index === 0}
                >
                  <ul className="divide-y">
                    {module.lessons.map((lesson) => (
                      <li key={lesson.id} className="flex items-center gap-3 py-2.5">
                        {lesson.content_type === "quiz" ? (
                          <FileText className="size-4 shrink-0 text-muted-foreground" />
                        ) : (
                          <PlayCircle className="size-4 shrink-0 text-muted-foreground" />
                        )}
                        <span className="min-w-0 flex-1 truncate text-sm">{lesson.title}</span>
                        {lesson.is_preview ? (
                          <Badge variant="secondary" className="shrink-0">
                            Bepul
                          </Badge>
                        ) : null}
                        <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                          {formatDuration(lesson.duration_seconds)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </Accordion>
              ))}
            </div>
          </section>

          {/* Talablar */}
          {course.requirements && course.requirements.length > 0 ? (
            <section>
              <h2 className="text-xl">Talablar</h2>
              <ul className="mt-3 space-y-2">
                {course.requirements.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                    <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-muted-foreground" />
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {/* Tavsif */}
          {course.description ? (
            <section>
              <h2 className="text-xl">Kurs haqida</h2>
              <div className="mt-3 whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
                {course.description}
              </div>
            </section>
          ) : null}

          {/* Kimga mos */}
          {course.target_audience && course.target_audience.length > 0 ? (
            <section>
              <h2 className="text-xl">Bu kurs kimga mos</h2>
              <ul className="mt-3 space-y-2">
                {course.target_audience.map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                    <Target className="mt-0.5 size-4 shrink-0 text-primary" />
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {/* Ustoz haqida */}
          {course.owner ? (
            <section className="rounded-xl border bg-card p-6">
              <h2 className="text-xl">Ustoz haqida</h2>
              <div className="mt-4 flex items-start gap-4">
                <Avatar name={course.owner.full_name} src={course.owner.avatar_url} size={64} />
                <div>
                  <p className="font-semibold">{course.owner.full_name}</p>
                  {course.owner.bio ? (
                    <p className="mt-1.5 text-sm text-muted-foreground">{course.owner.bio}</p>
                  ) : null}
                  <Link
                    href={`/teachers/${course.owner.id}`}
                    className="mt-3 inline-block text-sm font-medium text-primary hover:underline"
                  >
                    Barcha kurslarini ko&apos;rish →
                  </Link>
                </div>
              </div>
            </section>
          ) : null}

          {/* Sharhlar */}
          <CourseReviews courseId={course.id} isEnrolled={course.is_enrolled} />
        </div>

        {/* O'ng ustun (mobil uchun narx takrorlanmaydi) */}
        <div className="hidden lg:block" aria-hidden />
      </div>

      {/* Mobil pastdagi sticky panel */}
      <div className="sticky bottom-0 z-30 border-t bg-card p-4 shadow-[0_-4px_16px_-4px_rgb(15_23_42/0.12)] lg:hidden">
        <div className="flex items-center gap-3">
          <div className="min-w-0 flex-1">
            <p className="truncate text-lg font-bold">
              {formatPrice(course.discount_price ?? course.price, course.currency)}
            </p>
          </div>
          <div className="shrink-0">
            <CourseActions course={course} compact />
          </div>
        </div>
      </div>
    </div>
  );
}
