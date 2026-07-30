"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, RotateCcw, XCircle } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, EmptyState, Progress, Skeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import type { Quiz, QuizResult } from "@/lib/types";
import { cn } from "@/lib/utils";

export function QuizRunner({
  lessonId,
  onPassed,
}: {
  lessonId: string;
  onPassed?: () => void | Promise<void>;
}) {
  const [answers, setAnswers] = React.useState<Record<string, string[]>>({});
  const [result, setResult] = React.useState<QuizResult | null>(null);

  const { data: quiz, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["quiz", lessonId],
    queryFn: () => api.get<Quiz>(`/lessons/${lessonId}/quiz`),
    retry: false,
  });

  const submit = useMutation({
    mutationFn: () => api.post<QuizResult>(`/lessons/${lessonId}/quiz/submit`, { answers }),
    onSuccess: async (data) => {
      setResult(data);
      if (data.passed) {
        toast.success(`Test o'tildi — ${data.score}%`);
        await onPassed?.();
      } else {
        toast.error(`${data.score}% — o'tish uchun ${data.passing_score}% kerak`);
      }
    },
    onError: (caught) => {
      toast.error(caught instanceof ApiError ? caught.message : "Testni yuborib bo'lmadi");
    },
  });

  const toggle = (questionId: string, optionId: string, multiple: boolean) => {
    setAnswers((prev) => {
      const current = prev[questionId] ?? [];
      if (!multiple) return { ...prev, [questionId]: [optionId] };
      return {
        ...prev,
        [questionId]: current.includes(optionId)
          ? current.filter((id) => id !== optionId)
          : [...current, optionId],
      };
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-3 rounded-xl border bg-card p-6">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (isError || !quiz) {
    const message = error instanceof ApiError ? error.message : "Testni yuklab bo'lmadi";
    return (
      <EmptyState
        icon={AlertCircle}
        title="Test topilmadi"
        description={message}
        className="rounded-xl border bg-card"
      />
    );
  }

  const answered = Object.values(answers).filter((value) => value.length > 0).length;
  const allAnswered = answered === quiz.questions.length;
  const attemptsLeft = quiz.max_attempts ? quiz.max_attempts - quiz.attempts_used : null;
  const detailsById = new Map(result?.details.map((item) => [item.question_id, item]) ?? []);

  return (
    <div className="rounded-xl border bg-card p-6">
      <header className="mb-5 flex flex-wrap items-start justify-between gap-3 border-b pb-4">
        <div>
          <h2 className="text-xl">{quiz.title ?? "Test"}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {quiz.questions.length} savol · o&apos;tish balli {quiz.passing_score}%
            {quiz.time_limit_minutes ? ` · ${quiz.time_limit_minutes} daqiqa` : ""}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {quiz.passed ? (
            <Badge variant="success">
              <CheckCircle2 className="size-3" /> O&apos;tilgan
            </Badge>
          ) : null}
          {quiz.best_score !== null && quiz.best_score !== undefined ? (
            <Badge variant="muted">Eng yaxshi: {quiz.best_score}%</Badge>
          ) : null}
          {attemptsLeft !== null ? (
            <Badge variant={attemptsLeft > 0 ? "outline" : "destructive"}>
              {attemptsLeft > 0 ? `${attemptsLeft} urinish qoldi` : "Urinishlar tugadi"}
            </Badge>
          ) : null}
        </div>
      </header>

      {/* Natija */}
      {result ? (
        <Alert variant={result.passed ? "success" : "error"} className="mb-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-semibold">
                {result.passed ? "Test muvaffaqiyatli o'tildi!" : "Test o'tilmadi"}
              </p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                Natija: {result.score}% ({result.correct_count}/{result.total_questions} to&apos;g&apos;ri)
                · o&apos;tish balli {result.passing_score}%
              </p>
            </div>
            {!result.passed ? (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setResult(null);
                  setAnswers({});
                  void refetch();
                }}
              >
                <RotateCcw /> Qayta urinish
              </Button>
            ) : null}
          </div>
          <Progress value={result.score} className="mt-3" />
        </Alert>
      ) : null}

      {/* Savollar */}
      <ol className="space-y-5">
        {quiz.questions.map((question, index) => {
          const multiple = question.type === "multiple";
          const selected = answers[question.id] ?? [];
          const detail = detailsById.get(question.id);

          return (
            <li key={question.id} className="rounded-lg border p-4">
              <div className="mb-3 flex items-start gap-2.5">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-bold">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{question.text}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {multiple ? "Bir nechta javob tanlash mumkin" : "Bitta javobni tanlang"} ·{" "}
                    {question.points} ball
                  </p>
                </div>
                {detail ? (
                  detail.correct ? (
                    <CheckCircle2 className="size-5 shrink-0 text-secondary" />
                  ) : (
                    <XCircle className="size-5 shrink-0 text-destructive" />
                  )
                ) : null}
              </div>

              <div className="space-y-1.5">
                {question.options.map((option) => {
                  const isSelected = selected.includes(option.id);
                  const isCorrect = detail?.correct_answers.includes(option.id);
                  const showAnswer = Boolean(detail);

                  return (
                    <label
                      key={option.id}
                      className={cn(
                        "flex cursor-pointer items-center gap-2.5 rounded-lg border px-3 py-2.5 text-sm transition-colors",
                        showAnswer && isCorrect && "border-secondary bg-secondary/5",
                        showAnswer && isSelected && !isCorrect && "border-destructive bg-destructive/5",
                        !showAnswer && isSelected && "border-primary bg-primary/5",
                        !showAnswer && !isSelected && "hover:bg-muted",
                      )}
                    >
                      <input
                        type={multiple ? "checkbox" : "radio"}
                        name={question.id}
                        checked={isSelected}
                        disabled={Boolean(result)}
                        onChange={() => toggle(question.id, option.id, multiple)}
                        className="size-4 shrink-0 accent-primary"
                      />
                      <span className="min-w-0 flex-1">{option.text}</span>
                    </label>
                  );
                })}
              </div>
            </li>
          );
        })}
      </ol>

      {/* Yuborish */}
      {!result ? (
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t pt-5">
          <p className="text-sm text-muted-foreground">
            {answered}/{quiz.questions.length} savolga javob berildi
          </p>
          <Button
            size="lg"
            loading={submit.isPending}
            disabled={!allAnswered || (attemptsLeft !== null && attemptsLeft <= 0)}
            onClick={() => submit.mutate()}
          >
            Testni yakunlash
          </Button>
        </div>
      ) : null}
    </div>
  );
}
