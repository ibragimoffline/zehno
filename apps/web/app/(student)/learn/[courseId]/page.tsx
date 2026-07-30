"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Award,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  FileText,
  Lock,
  MessageCircle,
  PlayCircle,
  X,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { QuizRunner } from "@/components/player/quiz-runner";
import { VideoPlayer } from "@/components/player/video-player";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Alert, EmptyState, Progress, Skeleton, Tabs } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { LearnCourse, LessonDetail, ProgressUpdateResult } from "@/lib/types";
import { cn, formatDuration } from "@/lib/utils";

function LearnContent() {
  const params = useParams<{ courseId: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  const courseId = params.courseId;
  const [activeLessonId, setActiveLessonId] = React.useState<string | null>(
    searchParams.get("lesson"),
  );
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [tab, setTab] = React.useState("about");
  const [autoNext, setAutoNext] = React.useState<number | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["learn", courseId],
    queryFn: () => api.get<LearnCourse>(`/learn/${courseId}`),
  });

  const lessons = React.useMemo(
    () => (data ? data.modules.flatMap((module) => module.lessons) : []),
    [data],
  );

  // Boshlang'ich darsni aniqlaymiz
  React.useEffect(() => {
    if (!data || activeLessonId) return;
    setActiveLessonId(data.current_lesson_id ?? lessons[0]?.id ?? null);
  }, [data, activeLessonId, lessons]);

  const activeLesson = lessons.find((lesson) => lesson.id === activeLessonId) ?? null;
  const activeIndex = lessons.findIndex((lesson) => lesson.id === activeLessonId);
  const previousLesson = activeIndex > 0 ? lessons[activeIndex - 1] : null;
  const nextLesson =
    activeIndex >= 0 && activeIndex < lessons.length - 1 ? lessons[activeIndex + 1] : null;

  const progressMutation = useMutation({
    mutationFn: (payload: {
      lesson_id: string;
      watch_seconds?: number;
      position_seconds?: number;
      completed?: boolean;
    }) =>
      api.post<ProgressUpdateResult>(`/enrollments/${data?.enrollment_id}/progress`, payload),
    onSuccess: async (result) => {
      if (result.completed) {
        await queryClient.invalidateQueries({ queryKey: ["learn", courseId] });
      }
      if (result.certificate_issued) {
        toast.success("Tabriklaymiz! Sertifikat generatsiya qilinmoqda 🎉");
      }
    },
  });

  const markComplete = React.useCallback(
    async (lessonId: string, silent = false) => {
      if (!data) return;
      try {
        const result = await progressMutation.mutateAsync({
          lesson_id: lessonId,
          completed: true,
        });
        if (!silent) toast.success("Dars tugatilgan deb belgilandi");
        if (result.course_completed && !result.certificate_issued) {
          toast.success("Kursni tamomladingiz!");
        }
      } catch (caught) {
        if (caught instanceof ApiError) toast.error(caught.message);
      }
    },
    [data, progressMutation],
  );

  // Video tugagach 5 sekundlik countdown bilan keyingi darsga o'tish taklifi
  React.useEffect(() => {
    if (autoNext === null) return;
    if (autoNext <= 0) {
      setAutoNext(null);
      if (nextLesson && !nextLesson.is_locked) selectLesson(nextLesson.id);
      return;
    }
    const timer = setTimeout(() => setAutoNext((value) => (value ?? 1) - 1), 1000);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoNext, nextLesson]);

  const selectLesson = (lessonId: string) => {
    const lesson = lessons.find((item) => item.id === lessonId);
    if (lesson?.is_locked) {
      toast.error("Bu darsni ochish uchun oldingi darslarni tugatishingiz kerak");
      return;
    }
    setActiveLessonId(lessonId);
    setSidebarOpen(false);
    setAutoNext(null);
    setTab("about");
    router.replace(`/learn/${courseId}?lesson=${lessonId}`, { scroll: false });
  };

  if (isLoading) {
    return (
      <div className="grid min-h-screen lg:grid-cols-[1fr_340px]">
        <div className="space-y-4 p-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="aspect-video w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
        <div className="hidden border-l p-4 lg:block">
          <Skeleton className="h-full w-full" />
        </div>
      </div>
    );
  }

  if (isError || !data) {
    const message =
      error instanceof ApiError ? error.message : "Kursni yuklab bo'lmadi";
    return (
      <div className="container-page py-16">
        <EmptyState
          icon={Lock}
          title="Kursga kirish yo'q"
          description={message}
          action={<ButtonLink href="/courses">Katalogga o&apos;tish</ButtonLink>}
          className="rounded-xl border"
        />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background lg:h-screen lg:flex-row lg:overflow-hidden">
      {/* ===== Asosiy qism ===== */}
      <div className="flex min-w-0 flex-1 flex-col lg:overflow-y-auto scrollbar-thin">
        {/* Yuqori panel */}
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b bg-card px-4 py-3">
          <Link
            href={`/courses/${data.course.slug}`}
            className="flex shrink-0 items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-4" />
            <span className="hidden sm:inline">Kursga qaytish</span>
          </Link>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold">{data.course.title}</p>
            <div className="mt-1 flex items-center gap-2">
              <Progress value={data.progress_percent} size="sm" className="max-w-48" />
              <span className="shrink-0 text-xs font-semibold tabular-nums text-muted-foreground">
                {data.progress_percent}% ({data.completed_lessons}/{data.total_lessons})
              </span>
            </div>
          </div>

          {data.certificate_code ? (
            <ButtonLink
              href={`/certificates/${data.certificate_code}`}
              size="sm"
              variant="secondary"
              className="hidden shrink-0 sm:inline-flex"
            >
              <Award /> Sertifikat
            </ButtonLink>
          ) : null}

          <Button
            variant="outline"
            size="sm"
            className="shrink-0 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            Modullar
          </Button>
        </header>

        {/* Pleer / quiz */}
        <div className="p-4">
          {!activeLesson ? (
            <EmptyState title="Dars tanlanmagan" description="Chapdagi ro'yxatdan darsni tanlang." />
          ) : activeLesson.is_locked ? (
            <Alert variant="warning" title="Dars qulflangan">
              Bu kursda darslar ketma-ket o&apos;tiladi. Avval oldingi darslarni tugatib chiqing.
            </Alert>
          ) : activeLesson.content_type === "quiz" || activeLesson.has_quiz ? (
            <QuizRunner
              lessonId={activeLesson.id}
              onPassed={async () => {
                await queryClient.invalidateQueries({ queryKey: ["learn", courseId] });
              }}
            />
          ) : activeLesson.has_video ? (
            <>
              <VideoPlayer
                key={activeLesson.id}
                lessonId={activeLesson.id}
                poster={activeLesson.video?.thumbnail_url ?? data.course.cover_url}
                startAt={activeLesson.last_position_seconds}
                onProgress={({ watchSeconds, positionSeconds }) => {
                  progressMutation.mutate({
                    lesson_id: activeLesson.id,
                    watch_seconds: watchSeconds,
                    position_seconds: positionSeconds,
                  });
                }}
                onEnded={async () => {
                  if (!activeLesson.completed) await markComplete(activeLesson.id, true);
                  if (nextLesson && !nextLesson.is_locked) setAutoNext(5);
                }}
              />

              {autoNext !== null && nextLesson ? (
                <div className="mt-3 flex items-center justify-between gap-3 rounded-lg border bg-card p-3.5">
                  <p className="min-w-0 text-sm">
                    <span className="font-medium">{autoNext} soniyadan keyin:</span>{" "}
                    <span className="text-muted-foreground">{nextLesson.title}</span>
                  </p>
                  <div className="flex shrink-0 gap-2">
                    <Button size="sm" variant="ghost" onClick={() => setAutoNext(null)}>
                      <X /> Bekor
                    </Button>
                    <Button size="sm" onClick={() => selectLesson(nextLesson.id)}>
                      Hozir o&apos;tish
                    </Button>
                  </div>
                </div>
              ) : null}
            </>
          ) : activeLesson.text_content ? (
            <article className="prose prose-slate max-w-none rounded-xl border bg-card p-6">
              <h2 className="text-xl font-semibold">{activeLesson.title}</h2>
              <div className="mt-3 whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
                {activeLesson.text_content}
              </div>
            </article>
          ) : (
            <Alert variant="info" title="Kontent hali yuklanmagan">
              Ustoz bu darsga video yoki matn yuklamagan.
            </Alert>
          )}

          {/* Navigatsiya */}
          <div className="mt-4 flex items-center justify-between gap-3">
            <Button
              variant="outline"
              disabled={!previousLesson}
              onClick={() => previousLesson && selectLesson(previousLesson.id)}
            >
              <ChevronLeft /> Oldingi
            </Button>

            {activeLesson && !activeLesson.completed && !activeLesson.is_locked ? (
              <Button
                variant="secondary"
                loading={progressMutation.isPending}
                onClick={() => markComplete(activeLesson.id)}
              >
                <CheckCircle2 /> Tugatildi deb belgilash
              </Button>
            ) : activeLesson?.completed ? (
              <Badge variant="success">
                <CheckCircle2 className="size-3" /> Tugatilgan
              </Badge>
            ) : null}

            <Button
              disabled={!nextLesson || nextLesson.is_locked}
              onClick={() => nextLesson && selectLesson(nextLesson.id)}
            >
              Keyingi <ChevronRight />
            </Button>
          </div>

          {/* Tablar */}
          {activeLesson ? (
            <div className="mt-6">
              <Tabs
                active={tab}
                onChange={setTab}
                tabs={[
                  { id: "about", label: "Haqida" },
                  {
                    id: "materials",
                    label: "Materiallar",
                    count: activeLesson.attachments?.length ?? 0,
                  },
                  { id: "qa", label: "Savol-javob" },
                  { id: "notes", label: "Izohlar" },
                ]}
              />

              <div className="rounded-b-xl border border-t-0 bg-card p-5">
                {tab === "about" ? (
                  <div>
                    <h3 className="font-semibold">{activeLesson.title}</h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatDuration(activeLesson.duration_seconds)}
                    </p>
                    <p className="mt-3 whitespace-pre-line text-sm text-muted-foreground">
                      {activeLesson.description ?? "Bu dars uchun qo'shimcha tavsif yo'q."}
                    </p>
                  </div>
                ) : tab === "materials" ? (
                  activeLesson.attachments && activeLesson.attachments.length > 0 ? (
                    <ul className="space-y-2">
                      {activeLesson.attachments.map((file, index) => {
                        const item = file as { name?: string; url?: string };
                        return (
                          <li key={index}>
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noreferrer noopener"
                              className="flex items-center gap-2.5 rounded-lg border p-3 text-sm hover:bg-muted"
                            >
                              <FileText className="size-4 shrink-0 text-primary" />
                              <span className="min-w-0 flex-1 truncate">
                                {item.name ?? `Material ${index + 1}`}
                              </span>
                              <Download className="size-4 shrink-0 text-muted-foreground" />
                            </a>
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      Bu darsga qo&apos;shimcha material biriktirilmagan.
                    </p>
                  )
                ) : tab === "qa" ? (
                  <EmptyState
                    icon={MessageCircle}
                    title="Savol-javob tez orada"
                    description="Dars ostida savol qoldirish funksiyasi Phase 2 rejasida (ADDITIONAL_FEATURES 2.2)."
                  />
                ) : (
                  <EmptyState
                    icon={FileText}
                    title="Izohlar tez orada"
                    description="Video vaqtiga bog'langan shaxsiy izohlar keyingi bosqichda qo'shiladi."
                  />
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* ===== Sidebar: modullar ===== */}
      <aside
        className={cn(
          "border-l bg-card lg:w-[340px] lg:shrink-0 lg:overflow-y-auto scrollbar-thin",
          "fixed inset-x-0 bottom-0 top-auto z-40 max-h-[80vh] overflow-y-auto rounded-t-2xl shadow-2xl transition-transform lg:static lg:max-h-none lg:rounded-none lg:shadow-none",
          sidebarOpen ? "translate-y-0" : "translate-y-full lg:translate-y-0",
        )}
      >
        <div className="sticky top-0 flex items-center justify-between border-b bg-card px-4 py-3">
          <h2 className="font-semibold">Kurs tarkibi</h2>
          <button
            type="button"
            onClick={() => setSidebarOpen(false)}
            className="rounded p-1 hover:bg-muted lg:hidden"
            aria-label="Yopish"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="p-3">
          {data.modules.map((module, moduleIndex) => (
            <div key={module.id} className="mb-4">
              <p className="mb-1.5 px-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {moduleIndex + 1}-modul · {module.title}
              </p>

              <ul className="space-y-0.5">
                {module.lessons.map((lesson) => (
                  <li key={lesson.id}>
                    <button
                      type="button"
                      onClick={() => selectLesson(lesson.id)}
                      aria-current={lesson.id === activeLessonId ? "true" : undefined}
                      className={cn(
                        "flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm transition-colors",
                        lesson.id === activeLessonId
                          ? "bg-primary/10 text-primary"
                          : lesson.is_locked
                            ? "text-muted-foreground/60"
                            : "hover:bg-muted",
                      )}
                    >
                      <LessonIcon lesson={lesson} active={lesson.id === activeLessonId} />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate">{lesson.title}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatDuration(lesson.duration_seconds)}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </aside>

      {/* Mobil overlay */}
      {sidebarOpen ? (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden
        />
      ) : null}
    </div>
  );
}

function LessonIcon({ lesson, active }: { lesson: LessonDetail; active: boolean }) {
  if (lesson.completed) {
    return <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-secondary" />;
  }
  if (lesson.is_locked) {
    return <Lock className="mt-0.5 size-4 shrink-0" />;
  }
  if (lesson.content_type === "quiz" || lesson.has_quiz) {
    return <FileText className="mt-0.5 size-4 shrink-0" />;
  }
  return (
    <PlayCircle className={cn("mt-0.5 size-4 shrink-0", active && "text-primary")} />
  );
}

export default function LearnPage() {
  return (
    <React.Suspense
      fallback={
        <div className="space-y-4 p-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="aspect-video w-full" />
        </div>
      }
    >
      <LearnContent />
    </React.Suspense>
  );
}
