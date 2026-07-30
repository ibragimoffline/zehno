"use client";

import { useQuery } from "@tanstack/react-query";
import { Award, BookOpen, CheckCircle2, Clock, GraduationCap, TrendingUp } from "lucide-react";
import Link from "next/link";
import * as React from "react";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { StatCard } from "@/components/layout/dashboard-shell";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { CourseCardSkeleton, EmptyState, Progress, Tabs } from "@/components/ui/misc";
import { api } from "@/lib/api-client";
import { useRequireAuth } from "@/lib/hooks/use-auth";
import type { Certificate, Enrollment } from "@/lib/types";
import { formatDate, formatDuration } from "@/lib/utils";

export default function StudentDashboard() {
  const { user, loading: authLoading } = useRequireAuth();
  const [tab, setTab] = React.useState("active");

  const { data: enrollments = [], isLoading } = useQuery({
    queryKey: ["enrollments"],
    queryFn: () => api.get<Enrollment[]>("/enrollments/me"),
    enabled: Boolean(user),
  });

  const { data: certificates = [] } = useQuery({
    queryKey: ["certificates"],
    queryFn: () => api.get<Certificate[]>("/certificates/me"),
    enabled: Boolean(user),
  });

  const active = enrollments.filter((item) => item.status === "active");
  const completed = enrollments.filter((item) => item.status === "completed");
  const totalMinutes = enrollments.reduce(
    (sum, item) => sum + Math.round((item.course.duration_seconds * item.progress_percent) / 100),
    0,
  );
  const avgProgress = enrollments.length
    ? Math.round(
        enrollments.reduce((sum, item) => sum + item.progress_percent, 0) / enrollments.length,
      )
    : 0;

  const visible = tab === "active" ? active : tab === "completed" ? completed : enrollments;

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />

      <main id="main-content" className="container-page flex-1 py-8">
        <header className="mb-7">
          <h1 className="text-3xl">
            Salom{user ? `, ${user.full_name.split(" ")[0]}` : ""}! 👋
          </h1>
          <p className="mt-1.5 text-muted-foreground">
            {active.length > 0
              ? `${active.length} ta kurs davom etmoqda — bugun bir dars yakunlaymizmi?`
              : "Yangi kurs tanlab o'qishni boshlang."}
          </p>
        </header>

        {/* KPI */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Jami kurslar"
            value={enrollments.length}
            icon={BookOpen}
            tone="primary"
          />
          <StatCard
            label="Tugatilgan"
            value={completed.length}
            icon={CheckCircle2}
            tone="success"
          />
          <StatCard
            label="O'rtacha progress"
            value={`${avgProgress}%`}
            icon={TrendingUp}
            tone="warning"
          />
          <StatCard
            label="Sertifikatlar"
            value={certificates.length}
            hint={totalMinutes > 0 ? `~${formatDuration(totalMinutes)} o'qildi` : undefined}
            icon={Award}
            tone="success"
          />
        </div>

        {/* Davom etayotgan kurs (birinchi) */}
        {active.length > 0 ? (
          <section className="mb-8 overflow-hidden rounded-2xl border bg-gradient-to-r from-primary-50 to-card">
            <div className="flex flex-col gap-5 p-6 sm:flex-row sm:items-center">
              <div className="hidden w-40 shrink-0 overflow-hidden rounded-xl bg-muted sm:block">
                {active[0].course.cover_url ? (
                  <img
                    src={active[0].course.cover_url}
                    alt={active[0].course.title}
                    className="aspect-video size-full object-cover"
                  />
                ) : null}
              </div>

              <div className="min-w-0 flex-1">
                <Badge variant="default" className="mb-2">
                  Davom etmoqda
                </Badge>
                <h2 className="truncate text-xl font-semibold">{active[0].course.title}</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {active[0].completed_lessons} / {active[0].course.lessons_count} dars yakunlangan
                </p>
                <Progress value={active[0].progress_percent} showLabel className="mt-3 max-w-md" />
              </div>

              <ButtonLink href={`/learn/${active[0].course.id}`} size="lg" className="shrink-0">
                Davom ettirish
              </ButtonLink>
            </div>
          </section>
        ) : null}

        {/* Kurslar ro'yxati */}
        <section>
          <Tabs
            active={tab}
            onChange={setTab}
            tabs={[
              { id: "active", label: "Davom etmoqda", count: active.length },
              { id: "completed", label: "Tugatilgan", count: completed.length },
              { id: "all", label: "Barchasi", count: enrollments.length },
            ]}
            className="mb-5"
          />

          {isLoading || authLoading ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <CourseCardSkeleton key={index} />
              ))}
            </div>
          ) : visible.length > 0 ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {visible.map((enrollment) => (
                <EnrollmentCard key={enrollment.id} enrollment={enrollment} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={GraduationCap}
              title={
                tab === "completed" ? "Hali tugatilgan kurs yo'q" : "Kurslar ro'yxati bo'sh"
              }
              description="Katalogdan o'zingizga mos kursni tanlang va bugundan boshlang."
              action={<ButtonLink href="/courses">Kurslarni ko&apos;rish</ButtonLink>}
              className="rounded-xl border border-dashed"
            />
          )}
        </section>

        {/* Sertifikatlar */}
        {certificates.length > 0 ? (
          <section className="mt-10">
            <h2 className="mb-4 text-xl">Sertifikatlarim</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {certificates.map((certificate) => (
                <div
                  key={certificate.id}
                  className="flex items-start gap-3.5 rounded-xl border bg-card p-4"
                >
                  <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
                    <Award className="size-5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{certificate.course_title ?? "Kurs"}</p>
                    <p className="mt-0.5 font-mono text-xs text-muted-foreground">
                      {certificate.certificate_code}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {formatDate(certificate.issued_at)}
                    </p>
                    <div className="mt-2 flex gap-3 text-xs font-medium">
                      {certificate.pdf_url ? (
                        <a
                          href={certificate.pdf_url}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="text-primary hover:underline"
                        >
                          PDF yuklab olish
                        </a>
                      ) : null}
                      <Link
                        href={`/certificates/${certificate.certificate_code}`}
                        className="text-muted-foreground hover:underline"
                      >
                        Tekshirish
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ) : null}
      </main>

      <SiteFooter />
    </div>
  );
}

function EnrollmentCard({ enrollment }: { enrollment: Enrollment }) {
  const { course } = enrollment;

  return (
    <article className="flex flex-col overflow-hidden rounded-xl border bg-card shadow-card">
      <Link href={`/learn/${course.id}`} className="relative block aspect-video bg-muted">
        {course.cover_url ? (
          <img src={course.cover_url} alt={course.title} className="size-full object-cover" />
        ) : (
          <span className="flex size-full items-center justify-center text-muted-foreground">
            <BookOpen className="size-8" />
          </span>
        )}
        {enrollment.status === "completed" ? (
          <span className="absolute right-2.5 top-2.5">
            <Badge variant="success">
              <CheckCircle2 className="size-3" /> Tugatilgan
            </Badge>
          </span>
        ) : null}
      </Link>

      <div className="flex flex-1 flex-col p-4">
        <h3 className="line-clamp-2 font-semibold leading-snug">
          <Link href={`/learn/${course.id}`} className="hover:text-primary">
            {course.title}
          </Link>
        </h3>

        {course.owner ? (
          <p className="mt-1 truncate text-sm text-muted-foreground">{course.owner.full_name}</p>
        ) : null}

        <div className="mt-3">
          <Progress value={enrollment.progress_percent} showLabel />
          <p className="mt-1.5 text-xs text-muted-foreground">
            {enrollment.completed_lessons} / {course.lessons_count} dars
          </p>
        </div>

        <div className="mt-auto flex items-center justify-between gap-2 pt-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="size-3.5" /> {formatDuration(course.duration_seconds)}
          </span>
          {enrollment.has_certificate ? (
            <span className="flex items-center gap-1 text-secondary">
              <Award className="size-3.5" /> Sertifikat
            </span>
          ) : (
            <span>{formatDate(enrollment.enrolled_at)}</span>
          )}
        </div>
      </div>
    </article>
  );
}
