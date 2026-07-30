import { BookOpen, Clock, PlayCircle, Users } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Rating } from "@/components/ui/misc";
import type { CourseCard as CourseCardType } from "@/lib/types";
import {
  LEVEL_LABELS,
  cn,
  discountPercent,
  formatDuration,
  formatNumber,
  formatPrice,
} from "@/lib/utils";

export function CourseCard({
  course,
  className,
  href,
}: {
  course: CourseCardType;
  className?: string;
  href?: string;
}) {
  const discount = discountPercent(course.price, course.discount_price);
  const effectivePrice = course.discount_price ?? course.price;
  const target = href ?? `/courses/${course.slug}`;

  return (
    <article
      className={cn(
        "group flex flex-col overflow-hidden rounded-xl border bg-card shadow-card transition-shadow hover:shadow-card-hover",
        className,
      )}
    >
      <Link href={target} className="relative block aspect-video overflow-hidden bg-muted">
        {course.cover_url ? (
          <img
            src={course.cover_url}
            alt={course.title}
            loading="lazy"
            className="size-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
          />
        ) : (
          <span className="flex size-full items-center justify-center text-muted-foreground">
            <BookOpen className="size-8" />
          </span>
        )}

        <div className="absolute left-2.5 top-2.5 flex flex-wrap gap-1.5">
          {course.is_bestseller ? <Badge variant="accent">Bestseller</Badge> : null}
          {course.is_featured && !course.is_bestseller ? (
            <Badge variant="default">Tanlangan</Badge>
          ) : null}
          {discount > 0 ? <Badge variant="destructive">−{discount}%</Badge> : null}
        </div>

        {course.is_enrolled ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black/45 opacity-0 transition-opacity group-hover:opacity-100">
            <span className="flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900">
              <PlayCircle className="size-4" /> Davom ettirish
            </span>
          </div>
        ) : null}
      </Link>

      <div className="flex flex-1 flex-col p-4">
        {course.category ? (
          <Link
            href={`/courses?category=${course.category.slug}`}
            className="mb-1.5 text-xs font-medium text-primary hover:underline"
          >
            {course.category.name}
          </Link>
        ) : null}

        <h3 className="line-clamp-2 font-semibold leading-snug">
          <Link href={target} className="hover:text-primary">
            {course.title}
          </Link>
        </h3>

        {course.owner ? (
          <p className="mt-1.5 truncate text-sm text-muted-foreground">{course.owner.full_name}</p>
        ) : null}

        <div className="mt-2.5 flex items-center gap-3">
          {course.rating_count > 0 ? (
            <Rating value={course.rating_avg} count={course.rating_count} />
          ) : (
            <span className="text-xs text-muted-foreground">Yangi kurs</span>
          )}
        </div>

        <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <BookOpen className="size-3.5" /> {course.lessons_count} dars
          </span>
          {course.duration_seconds > 0 ? (
            <span className="flex items-center gap-1">
              <Clock className="size-3.5" /> {formatDuration(course.duration_seconds)}
            </span>
          ) : null}
          {course.students_count > 0 ? (
            <span className="flex items-center gap-1">
              <Users className="size-3.5" /> {formatNumber(course.students_count)}
            </span>
          ) : null}
        </div>

        <div className="mt-auto flex items-end justify-between gap-2 pt-4">
          <div>
            {course.is_enrolled ? (
              <Badge variant="success">Sizda mavjud</Badge>
            ) : (
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-bold">
                  {formatPrice(effectivePrice, course.currency)}
                </span>
                {discount > 0 ? (
                  <span className="text-sm text-muted-foreground line-through">
                    {formatPrice(course.price, course.currency)}
                  </span>
                ) : null}
              </div>
            )}
          </div>
          <Badge variant="muted">{LEVEL_LABELS[course.level]}</Badge>
        </div>
      </div>
    </article>
  );
}
