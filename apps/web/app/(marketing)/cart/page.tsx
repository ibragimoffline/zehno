"use client";

import { useMutation } from "@tanstack/react-query";
import { ShoppingCart, Tag, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Button, ButtonLink } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, EmptyState, Skeleton } from "@/components/ui/misc";
import { ApiError, api } from "@/lib/api-client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useCart } from "@/lib/hooks/use-cart";
import type { CheckoutResponse, CouponValidateResponse } from "@/lib/types";
import { formatPrice } from "@/lib/utils";

interface CouponState {
  code: string;
  discount: number;
  message: string;
}

export default function CartPage() {
  const { user, loading: authLoading } = useAuth();
  const { cart, loading, remove } = useCart();
  const router = useRouter();

  const [couponInput, setCouponInput] = React.useState("");
  const [coupon, setCoupon] = React.useState<CouponState | null>(null);
  const [provider, setProvider] = React.useState("");

  const couponMutation = useMutation({
    mutationFn: () =>
      api.post<CouponValidateResponse>("/coupons/validate", { code: couponInput.trim() }),
    onSuccess: (result) => {
      if (result.valid) {
        setCoupon({
          code: couponInput.trim().toUpperCase(),
          discount: Number(result.discount),
          message: result.message,
        });
        toast.success(result.message);
      } else {
        setCoupon(null);
        toast.error(result.message);
      }
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Kuponni tekshirib bo'lmadi");
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: () =>
      api.post<CheckoutResponse>("/cart/checkout", {
        coupon_code: coupon?.code,
        provider: provider || undefined,
      }),
    onSuccess: (result) => {
      if (result.is_free) {
        toast.success("Kurslar ochildi!");
        router.push("/dashboard");
        return;
      }
      window.location.href = result.checkout_url;
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : "Checkout amalga oshmadi");
    },
  });

  if (authLoading || loading) {
    return (
      <div className="container-page space-y-4 py-10">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container-page py-10">
        <EmptyState
          icon={ShoppingCart}
          title="Savatni ko'rish uchun tizimga kiring"
          description="Hisobingizga kirsangiz savatdagi kurslar saqlanib qoladi."
          action={<ButtonLink href="/login?next=/cart">Kirish</ButtonLink>}
          className="rounded-xl border"
        />
      </div>
    );
  }

  const items = cart?.items ?? [];
  const subtotal = Number(cart?.subtotal ?? 0);
  const discount = coupon?.discount ?? 0;
  const total = Math.max(subtotal - discount, 0);

  if (items.length === 0) {
    return (
      <div className="container-page py-10">
        <h1 className="mb-6 text-3xl">Savat</h1>
        <EmptyState
          icon={ShoppingCart}
          title="Savat bo'sh"
          description="Katalogdan o'zingizga mos kurs tanlang va savatga qo'shing."
          action={<ButtonLink href="/courses">Kurslarni ko&apos;rish</ButtonLink>}
          className="rounded-xl border"
        />
      </div>
    );
  }

  return (
    <div className="container-page py-10">
      <h1 className="mb-6 text-3xl">Savat ({items.length})</h1>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Kurslar */}
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.id} className="flex gap-4 rounded-xl border bg-card p-4">
              <Link
                href={`/courses/${item.course.slug}`}
                className="hidden w-32 shrink-0 overflow-hidden rounded-lg bg-muted sm:block"
              >
                {item.course.cover_url ? (
                  <img
                    src={item.course.cover_url}
                    alt={item.course.title}
                    className="aspect-video size-full object-cover"
                  />
                ) : null}
              </Link>

              <div className="min-w-0 flex-1">
                <Link
                  href={`/courses/${item.course.slug}`}
                  className="line-clamp-2 font-semibold hover:text-primary"
                >
                  {item.course.title}
                </Link>
                {item.course.owner ? (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {item.course.owner.full_name}
                  </p>
                ) : null}
                <p className="mt-2 font-bold">
                  {formatPrice(
                    item.course.discount_price ?? item.course.price,
                    item.course.currency,
                  )}
                </p>
              </div>

              <button
                type="button"
                onClick={() => remove(item.course.id)}
                className="shrink-0 self-start rounded-lg p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                aria-label="Savatdan olib tashlash"
              >
                <Trash2 className="size-4" />
              </button>
            </li>
          ))}
        </ul>

        {/* Xulosa */}
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <div className="rounded-xl border bg-card p-5 shadow-card">
            <h2 className="text-lg font-semibold">Buyurtma xulosasi</h2>

            <dl className="mt-4 space-y-2.5 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Kurslar ({items.length})</dt>
                <dd className="font-medium">{formatPrice(subtotal)}</dd>
              </div>
              {discount > 0 ? (
                <div className="flex justify-between text-secondary">
                  <dt>Chegirma ({coupon?.code})</dt>
                  <dd className="font-medium">−{formatPrice(discount)}</dd>
                </div>
              ) : null}
              <div className="flex justify-between border-t pt-2.5 text-base">
                <dt className="font-semibold">Jami</dt>
                <dd className="font-bold">{formatPrice(total)}</dd>
              </div>
            </dl>

            {/* Kupon */}
            <div className="mt-5">
              <label htmlFor="coupon" className="mb-1.5 block text-sm font-medium">
                Chegirma kuponi
              </label>
              <div className="flex gap-2">
                <Input
                  id="coupon"
                  value={couponInput}
                  onChange={(event) => setCouponInput(event.target.value.toUpperCase())}
                  placeholder="KUPON2026"
                  className="font-mono uppercase"
                />
                <Button
                  variant="outline"
                  loading={couponMutation.isPending}
                  onClick={() => couponMutation.mutate()}
                  disabled={!couponInput.trim()}
                >
                  <Tag />
                </Button>
              </div>
              {coupon ? (
                <Alert variant="success" className="mt-2.5">
                  {coupon.message}: −{formatPrice(coupon.discount)}
                </Alert>
              ) : null}
            </div>

            {/* To'lov usuli */}
            <fieldset className="mt-5">
              <legend className="mb-2 text-sm font-medium">To&apos;lov usuli</legend>
              <div className="space-y-1.5">
                {[
                  { value: "", label: "Standart (server sozlamasi)" },
                  { value: "payme", label: "Payme" },
                  { value: "click", label: "Click" },
                  { value: "mock", label: "Test rejimi (sandbox)" },
                ].map((option) => (
                  <label
                    key={option.value}
                    className="flex cursor-pointer items-center gap-2 text-sm"
                  >
                    <input
                      type="radio"
                      name="provider"
                      value={option.value}
                      checked={provider === option.value}
                      onChange={() => setProvider(option.value)}
                      className="size-4 accent-primary"
                    />
                    {option.label}
                  </label>
                ))}
              </div>
            </fieldset>

            <Button
              full
              size="lg"
              className="mt-5"
              loading={checkoutMutation.isPending}
              onClick={() => checkoutMutation.mutate()}
            >
              To&apos;lovga o&apos;tish
            </Button>

            <p className="mt-3 text-center text-xs text-muted-foreground">
              To&apos;lov Payme/Click himoyalangan sahifasida amalga oshiriladi
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
