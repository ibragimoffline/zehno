"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquare, Star } from "lucide-react";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { Avatar, EmptyState, Rating, Skeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import { useAuth } from "@/lib/hooks/use-auth";
import type { Page, Review } from "@/lib/types";
import { cn, formatRelative } from "@/lib/utils";

export function CourseReviews({
  courseId,
  isEnrolled,
}: {
  courseId: string;
  isEnrolled: boolean;
}) {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [rating, setRating] = React.useState(5);
  const [comment, setComment] = React.useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["reviews", courseId],
    queryFn: () =>
      api.get<Page<Review>>(`/courses/${courseId}/reviews`, {
        auth: false,
        query: { per_page: 10 },
      }),
  });

  const mutation = useMutation({
    mutationFn: () =>
      api.post<Review>(`/courses/${courseId}/reviews`, {
        rating,
        comment: comment.trim() || undefined,
      }),
    onSuccess: async () => {
      toast.success("Sharhingiz qo'shildi. Rahmat!");
      setComment("");
      await queryClient.invalidateQueries({ queryKey: ["reviews", courseId] });
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Sharh qo'shilmadi");
    },
  });

  return (
    <section id="reviews">
      <div className="mb-4 flex items-end justify-between gap-3">
        <h2 className="text-xl">Sharhlar</h2>
        {data && data.total > 0 ? (
          <span className="text-sm text-muted-foreground">{data.total} ta sharh</span>
        ) : null}
      </div>

      {user && isEnrolled ? (
        <div className="mb-6 rounded-xl border bg-card p-5">
          <p className="text-sm font-medium">Kursni baholang</p>

          <div className="mt-2.5 flex gap-1" role="radiogroup" aria-label="Reyting">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                role="radio"
                aria-checked={rating === star}
                aria-label={`${star} yulduz`}
                onClick={() => setRating(star)}
                className="rounded p-0.5"
              >
                <Star
                  className={cn(
                    "size-6 transition-colors",
                    star <= rating
                      ? "fill-accent-500 text-accent-500"
                      : "text-muted-foreground/40",
                  )}
                />
              </button>
            ))}
          </div>

          <Textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Kurs sizga qanday yordam berdi? Boshqalarga foydali bo'ladigan fikringizni yozing."
            className="mt-3"
            maxLength={2000}
          />

          <div className="mt-3 flex justify-end">
            <Button loading={mutation.isPending} onClick={() => mutation.mutate()}>
              Sharhni yuborish
            </Button>
          </div>
        </div>
      ) : null}

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="flex gap-3">
              <Skeleton className="size-10 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            </div>
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <ul className="space-y-5">
          {data.items.map((review) => (
            <li key={review.id} className="flex gap-3.5 border-b pb-5 last:border-0">
              <Avatar name={review.user?.full_name} src={review.user?.avatar_url} size={40} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="font-medium">{review.user?.full_name ?? "Talaba"}</span>
                  <Rating value={review.rating} size={12} />
                  <span className="text-xs text-muted-foreground">
                    {formatRelative(review.created_at)}
                  </span>
                </div>
                {review.comment ? (
                  <p className="mt-1.5 text-sm text-muted-foreground">{review.comment}</p>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          icon={MessageSquare}
          title="Hali sharhlar yo'q"
          description={
            isEnrolled
              ? "Birinchi bo'lib fikringizni qoldiring!"
              : "Kursni sotib olgan talabalar sharh qoldirishi mumkin."
          }
          className="rounded-xl border border-dashed"
        />
      )}
    </section>
  );
}
