"use client";

import { CreditCard, PlayCircle, ShoppingCart } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ApiError, api } from "@/lib/api-client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useCart } from "@/lib/hooks/use-cart";
import type { CheckoutResponse, CourseDetail } from "@/lib/types";
import { discountPercent, formatPrice } from "@/lib/utils";

export function CourseActions({
  course,
  compact = false,
}: {
  course: CourseDetail;
  compact?: boolean;
}) {
  const { user } = useAuth();
  const { add, cart } = useCart();
  const router = useRouter();
  const [loading, setLoading] = React.useState(false);

  const inCart = cart?.items.some((item) => item.course.id === course.id) ?? false;
  const discount = discountPercent(course.price, course.discount_price);
  const isFree = Number(course.discount_price ?? course.price) <= 0;

  // Sotib olingan bo'lsa — darsga o'tish
  if (course.is_enrolled) {
    return (
      <Button full={!compact} size="lg" onClick={() => router.push(`/learn/${course.id}`)}>
        <PlayCircle /> Darsni davom ettirish
      </Button>
    );
  }

  const requireAuth = (): boolean => {
    if (user) return true;
    router.push(`/login?next=${encodeURIComponent(`/courses/${course.slug}`)}`);
    return false;
  };

  const buyNow = async () => {
    if (!requireAuth()) return;
    setLoading(true);
    try {
      const result = await api.post<CheckoutResponse>("/cart/checkout", {
        course_ids: [course.id],
      });
      if (result.is_free) {
        toast.success("Kurs ochildi! Darslarni boshlashingiz mumkin.");
        router.push(`/learn/${course.id}`);
        return;
      }
      // To'lov provayderi sahifasiga o'tamiz
      window.location.href = result.checkout_url;
    } catch (error) {
      toast.error(
        error instanceof ApiError ? error.message : "To'lovni boshlashda xatolik yuz berdi",
      );
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async () => {
    if (!requireAuth()) return;
    if (inCart) {
      router.push("/cart");
      return;
    }
    setLoading(true);
    await add(course.id);
    setLoading(false);
  };

  if (compact) {
    return (
      <Button size="lg" loading={loading} onClick={buyNow}>
        {isFree ? "Bepul boshlash" : "Sotib olish"}
      </Button>
    );
  }

  return (
    <div>
      <div className="mb-4 flex items-end gap-2.5">
        <span className="text-3xl font-bold">
          {formatPrice(course.discount_price ?? course.price, course.currency)}
        </span>
        {discount > 0 ? (
          <>
            <span className="text-lg text-muted-foreground line-through">
              {formatPrice(course.price, course.currency)}
            </span>
            <span className="mb-1 rounded bg-destructive/10 px-1.5 py-0.5 text-xs font-bold text-destructive">
              −{discount}%
            </span>
          </>
        ) : null}
      </div>

      <div className="space-y-2.5">
        <Button full size="lg" loading={loading} onClick={buyNow}>
          <CreditCard />
          {isFree ? "Bepul boshlash" : "Hozir sotib olish"}
        </Button>

        {!isFree ? (
          <Button full size="lg" variant="outline" onClick={addToCart} disabled={loading}>
            <ShoppingCart />
            {inCart ? "Savatga o'tish" : "Savatga qo'shish"}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
