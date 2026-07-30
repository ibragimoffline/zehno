"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  FileText,
  GripVertical,
  Loader2,
  Pencil,
  Plus,
  Send,
  Trash2,
  Upload,
  Video,
} from "lucide-react";
import { useParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { Alert, EmptyState, Modal, Skeleton, Tabs } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { CourseAdminDetail, LessonPublic, ModulePublic } from "@/lib/types";
import { COURSE_STATUS_LABELS, cn, formatDuration } from "@/lib/utils";

export default function CourseBuilderPage() {
  const params = useParams<{ courseId: string }>();
  const courseId = params.courseId;
  const queryClient = useQueryClient();

  const [tab, setTab] = React.useState("curriculum");
  const [moduleModal, setModuleModal] = React.useState<{ id?: string; title: string } | null>(null);
  const [lessonModal, setLessonModal] = React.useState<{
    moduleId: string;
    lesson?: LessonPublic;
  } | null>(null);

  const { data: course, isLoading } = useQuery({
    queryKey: ["teacher-course", courseId],
    queryFn: () => api.get<CourseAdminDetail>(`/teacher/courses/${courseId}`),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["teacher-course", courseId] });

  const submitMutation = useMutation({
    mutationFn: () => api.post(`/teacher/courses/${courseId}/submit`),
    onSuccess: async () => {
      toast.success("Kurs moderatsiyaga yuborildi");
      await invalidate();
    },
    onError: (error) =>
      toast.error(error instanceof ApiError ? error.message : "Yuborilmadi"),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!course) {
    return <EmptyState title="Kurs topilmadi" className="rounded-xl border" />;
  }

  const totalLessons = course.modules.reduce((sum, module) => sum + module.lessons.length, 0);
  const missingVideos = course.modules
    .flatMap((module) => module.lessons)
    .filter((lesson) => lesson.content_type === "video" && !lesson.has_video).length;

  return (
    <div className="space-y-6">
      {/* Kurs sarlavhasi */}
      <div className="flex flex-col gap-4 rounded-xl border bg-card p-5 sm:flex-row sm:items-center">
        {course.cover_url ? (
          <img
            src={course.cover_url}
            alt={course.title}
            className="h-20 w-32 shrink-0 rounded-lg object-cover"
          />
        ) : null}

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge
              status={course.status}
              label={COURSE_STATUS_LABELS[course.status] ?? course.status}
            />
            <Badge variant="muted">
              {course.modules.length} modul · {totalLessons} dars
            </Badge>
            {course.duration_seconds > 0 ? (
              <Badge variant="outline">{formatDuration(course.duration_seconds)}</Badge>
            ) : null}
          </div>
          <h2 className="mt-2 truncate text-xl font-semibold">{course.title}</h2>
        </div>

        {course.status === "draft" || course.status === "rejected" ? (
          <Button
            className="shrink-0"
            loading={submitMutation.isPending}
            onClick={() => submitMutation.mutate()}
          >
            <Send /> Moderatsiyaga yuborish
          </Button>
        ) : null}
      </div>

      {course.status === "rejected" && course.rejection_reason ? (
        <Alert variant="error" title="Kurs rad etildi">
          {course.rejection_reason}
        </Alert>
      ) : null}

      {missingVideos > 0 ? (
        <Alert variant="warning" title="Video yuklanmagan darslar bor">
          {missingVideos} ta video darsga video yuklanmagan. Moderatsiyaga yuborishdan oldin
          yuklashingiz kerak.
        </Alert>
      ) : null}

      <Tabs
        active={tab}
        onChange={setTab}
        tabs={[
          { id: "curriculum", label: "Dastur", count: totalLessons },
          { id: "settings", label: "Sozlamalar" },
        ]}
      />

      {tab === "curriculum" ? (
        <div className="space-y-4">
          {course.modules.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="Hali modul qo'shilmagan"
              description="Kurs tarkibini modullardan boshlab quring: masalan «1-modul. Kirish»."
              action={
                <Button onClick={() => setModuleModal({ title: "" })}>
                  <Plus /> Modul qo&apos;shish
                </Button>
              }
              className="rounded-xl border border-dashed bg-card"
            />
          ) : (
            <>
              {course.modules.map((module, index) => (
                <ModuleBlock
                  key={module.id}
                  module={module}
                  index={index}
                  onEdit={() => setModuleModal({ id: module.id, title: module.title })}
                  onAddLesson={() => setLessonModal({ moduleId: module.id })}
                  onEditLesson={(lesson) => setLessonModal({ moduleId: module.id, lesson })}
                  onChanged={invalidate}
                />
              ))}

              <Button variant="outline" onClick={() => setModuleModal({ title: "" })}>
                <Plus /> Modul qo&apos;shish
              </Button>
            </>
          )}
        </div>
      ) : (
        <CourseSettings course={course} onSaved={invalidate} />
      )}

      {/* Modul modali */}
      <ModuleModal
        state={moduleModal}
        courseId={courseId}
        onClose={() => setModuleModal(null)}
        onSaved={invalidate}
      />

      {/* Dars modali */}
      <LessonModal
        state={lessonModal}
        onClose={() => setLessonModal(null)}
        onSaved={invalidate}
      />
    </div>
  );
}

/* ================= Modul bloki ================= */
function ModuleBlock({
  module,
  index,
  onEdit,
  onAddLesson,
  onEditLesson,
  onChanged,
}: {
  module: ModulePublic;
  index: number;
  onEdit: () => void;
  onAddLesson: () => void;
  onEditLesson: (lesson: LessonPublic) => void;
  onChanged: () => void;
}) {
  const deleteModule = useMutation({
    mutationFn: () => api.delete(`/teacher/modules/${module.id}`),
    onSuccess: () => {
      toast.success("Modul o'chirildi");
      onChanged();
    },
  });

  const deleteLesson = useMutation({
    mutationFn: (lessonId: string) => api.delete(`/teacher/lessons/${lessonId}`),
    onSuccess: () => {
      toast.success("Dars o'chirildi");
      onChanged();
    },
  });

  return (
    <div className="rounded-xl border bg-card">
      <div className="flex items-center gap-3 border-b p-4">
        <GripVertical className="size-4 shrink-0 cursor-grab text-muted-foreground" />
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold">
            {index + 1}. {module.title}
          </p>
          <p className="text-xs text-muted-foreground">
            {module.lessons.length} dars · {formatDuration(module.duration_seconds)}
          </p>
        </div>
        <Button size="icon-sm" variant="ghost" onClick={onEdit} aria-label="Modulni tahrirlash">
          <Pencil />
        </Button>
        <Button
          size="icon-sm"
          variant="ghost"
          loading={deleteModule.isPending}
          onClick={() => deleteModule.mutate()}
          aria-label="Modulni o'chirish"
        >
          <Trash2 className="text-destructive" />
        </Button>
      </div>

      <ul className="divide-y">
        {module.lessons.map((lesson) => (
          <li key={lesson.id} className="flex items-center gap-3 px-4 py-3">
            <GripVertical className="size-4 shrink-0 cursor-grab text-muted-foreground" />

            {lesson.content_type === "quiz" ? (
              <FileText className="size-4 shrink-0 text-muted-foreground" />
            ) : (
              <Video className="size-4 shrink-0 text-muted-foreground" />
            )}

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{lesson.title}</p>
              <p className="text-xs text-muted-foreground">
                {formatDuration(lesson.duration_seconds)}
                {lesson.is_preview ? " · bepul ko'rish" : ""}
              </p>
            </div>

            {lesson.content_type === "video" ? (
              lesson.has_video ? (
                <Badge variant="success">
                  <CheckCircle2 className="size-3" /> Video
                </Badge>
              ) : (
                <VideoUploadButton lessonId={lesson.id} onUploaded={onChanged} />
              )
            ) : null}

            <Button
              size="icon-sm"
              variant="ghost"
              onClick={() => onEditLesson(lesson)}
              aria-label="Darsni tahrirlash"
            >
              <Pencil />
            </Button>
            <Button
              size="icon-sm"
              variant="ghost"
              onClick={() => deleteLesson.mutate(lesson.id)}
              aria-label="Darsni o'chirish"
            >
              <Trash2 className="text-destructive" />
            </Button>
          </li>
        ))}
      </ul>

      <div className="p-3">
        <Button variant="ghost" size="sm" onClick={onAddLesson}>
          <Plus /> Dars qo&apos;shish
        </Button>
      </div>
    </div>
  );
}

/* ================= Video yuklash ================= */
function VideoUploadButton({
  lessonId,
  onUploaded,
}: {
  lessonId: string;
  onUploaded: () => void;
}) {
  const [progress, setProgress] = React.useState<number | null>(null);

  const upload = async (file: File) => {
    setProgress(0);
    try {
      const formData = new FormData();
      formData.append("file", file);
      // Katta fayllar uchun oddiy fetch — progressni taxminiy ko'rsatamiz
      const timer = setInterval(
        () => setProgress((value) => Math.min((value ?? 0) + 7, 92)),
        700,
      );
      await api.post(`/lessons/${lessonId}/video`, formData);
      clearInterval(timer);
      setProgress(100);
      toast.success("Video yuklandi — transkodlash boshlandi");
      onUploaded();
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Video yuklanmadi");
    } finally {
      setTimeout(() => setProgress(null), 800);
    }
  };

  if (progress !== null) {
    return (
      <span className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="size-3.5 animate-spin" />
        {progress}%
      </span>
    );
  }

  return (
    <label className="flex shrink-0 cursor-pointer items-center gap-1.5 rounded-lg border border-dashed px-2.5 py-1.5 text-xs hover:bg-muted">
      <Upload className="size-3.5" />
      Video
      <input
        type="file"
        accept="video/*"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void upload(file);
        }}
      />
    </label>
  );
}

/* ================= Modul modali ================= */
function ModuleModal({
  state,
  courseId,
  onClose,
  onSaved,
}: {
  state: { id?: string; title: string } | null;
  courseId: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [title, setTitle] = React.useState("");

  React.useEffect(() => {
    setTitle(state?.title ?? "");
  }, [state]);

  const mutation = useMutation({
    mutationFn: () =>
      state?.id
        ? api.patch(`/teacher/modules/${state.id}`, { title })
        : api.post(`/teacher/courses/${courseId}/modules`, { title }),
    onSuccess: () => {
      toast.success(state?.id ? "Modul yangilandi" : "Modul qo'shildi");
      onSaved();
      onClose();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Saqlanmadi"),
  });

  return (
    <Modal
      open={Boolean(state)}
      onClose={onClose}
      title={state?.id ? "Modulni tahrirlash" : "Yangi modul"}
      footer={
        <>
          <Button variant="outline" onClick={onClose}>
            Bekor qilish
          </Button>
          <Button
            loading={mutation.isPending}
            disabled={!title.trim()}
            onClick={() => mutation.mutate()}
          >
            Saqlash
          </Button>
        </>
      }
    >
      <Field label="Modul nomi" htmlFor="module-title" required>
        <Input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="1-modul. HTML asoslari"
        />
      </Field>
    </Modal>
  );
}

/* ================= Dars modali ================= */
function LessonModal({
  state,
  onClose,
  onSaved,
}: {
  state: { moduleId: string; lesson?: LessonPublic } | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = React.useState({
    title: "",
    description: "",
    content_type: "video",
    duration_seconds: 0,
    is_preview: false,
  });

  React.useEffect(() => {
    setForm({
      title: state?.lesson?.title ?? "",
      description: state?.lesson?.description ?? "",
      content_type: state?.lesson?.content_type ?? "video",
      duration_seconds: state?.lesson?.duration_seconds ?? 0,
      is_preview: state?.lesson?.is_preview ?? false,
    });
  }, [state]);

  const mutation = useMutation({
    mutationFn: () =>
      state?.lesson
        ? api.patch(`/teacher/lessons/${state.lesson.id}`, form)
        : api.post(`/teacher/modules/${state?.moduleId}/lessons`, form),
    onSuccess: () => {
      toast.success(state?.lesson ? "Dars yangilandi" : "Dars qo'shildi");
      onSaved();
      onClose();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Saqlanmadi"),
  });

  return (
    <Modal
      open={Boolean(state)}
      onClose={onClose}
      title={state?.lesson ? "Darsni tahrirlash" : "Yangi dars"}
      footer={
        <>
          <Button variant="outline" onClick={onClose}>
            Bekor qilish
          </Button>
          <Button
            loading={mutation.isPending}
            disabled={!form.title.trim()}
            onClick={() => mutation.mutate()}
          >
            Saqlash
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <Field label="Dars nomi" htmlFor="lesson-title" required>
          <Input
            value={form.title}
            onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
            placeholder="1.1 Kirish: veb qanday ishlaydi"
          />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Turi" htmlFor="lesson-type">
            <Select
              value={form.content_type}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, content_type: event.target.value }))
              }
            >
              <option value="video">Video</option>
              <option value="text">Matn</option>
              <option value="pdf">PDF</option>
              <option value="quiz">Test</option>
            </Select>
          </Field>

          <Field label="Davomiyligi (sekund)" htmlFor="lesson-duration">
            <Input
              type="number"
              min={0}
              value={form.duration_seconds}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, duration_seconds: Number(event.target.value) }))
              }
            />
          </Field>
        </div>

        <Field label="Tavsif" htmlFor="lesson-description">
          <Textarea
            rows={3}
            value={form.description}
            onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
          />
        </Field>

        <label className="flex cursor-pointer items-center gap-2.5 text-sm">
          <input
            type="checkbox"
            checked={form.is_preview}
            onChange={(event) => setForm((prev) => ({ ...prev, is_preview: event.target.checked }))}
            className="size-4 accent-primary"
          />
          Bu darsni hamma bepul ko&apos;rishi mumkin (preview)
        </label>
      </div>
    </Modal>
  );
}

/* ================= Kurs sozlamalari ================= */
function CourseSettings({
  course,
  onSaved,
}: {
  course: CourseAdminDetail;
  onSaved: () => void;
}) {
  const [form, setForm] = React.useState({
    title: course.title,
    subtitle: course.subtitle ?? "",
    description: course.description ?? "",
    price: String(course.price),
    discount_price: course.discount_price ? String(course.discount_price) : "",
    has_certificate: course.has_certificate,
    sequential_progress: course.sequential_progress,
  });

  const mutation = useMutation({
    mutationFn: () =>
      api.patch(`/teacher/courses/${course.id}`, {
        title: form.title,
        subtitle: form.subtitle || undefined,
        description: form.description || undefined,
        price: form.price,
        discount_price: form.discount_price || undefined,
        has_certificate: form.has_certificate,
        sequential_progress: form.sequential_progress,
      }),
    onSuccess: () => {
      toast.success("Saqlandi");
      onSaved();
    },
    onError: (error) => toast.error(error instanceof ApiError ? error.message : "Saqlanmadi"),
  });

  return (
    <div className="max-w-2xl space-y-5 rounded-xl border bg-card p-6">
      <Field label="Kurs nomi" htmlFor="s-title" required>
        <Input
          value={form.title}
          onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
        />
      </Field>

      <Field label="Qisqa tavsif" htmlFor="s-subtitle">
        <Input
          value={form.subtitle}
          onChange={(event) => setForm((prev) => ({ ...prev, subtitle: event.target.value }))}
        />
      </Field>

      <Field label="To'liq tavsif" htmlFor="s-description">
        <Textarea
          rows={6}
          value={form.description}
          onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Narx (UZS)" htmlFor="s-price">
          <Input
            type="number"
            min={0}
            value={form.price}
            onChange={(event) => setForm((prev) => ({ ...prev, price: event.target.value }))}
          />
        </Field>
        <Field label="Chegirma narxi" htmlFor="s-discount">
          <Input
            type="number"
            min={0}
            value={form.discount_price}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, discount_price: event.target.value }))
            }
          />
        </Field>
      </div>

      <div className="space-y-2.5">
        {(
          [
            { key: "has_certificate", label: "Sertifikat berilsin" },
            { key: "sequential_progress", label: "Darslar ketma-ket o'tilsin" },
          ] as const
        ).map((option) => (
          <label key={option.key} className="flex cursor-pointer items-center gap-2.5 text-sm">
            <input
              type="checkbox"
              checked={form[option.key]}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, [option.key]: event.target.checked }))
              }
              className="size-4 accent-primary"
            />
            {option.label}
          </label>
        ))}
      </div>

      <div className={cn("flex justify-end border-t pt-5")}>
        <Button loading={mutation.isPending} onClick={() => mutation.mutate()}>
          Saqlash
        </Button>
      </div>
    </div>
  );
}
