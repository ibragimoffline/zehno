"use client";

import { CheckCircle2, CreditCard, XCircle } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Button, ButtonLink } from "@/components/ui/button";
import { Alert } from "@/components/ui/misc";
import { api } from "@/lib/api-client";
import { formatPrice } from "@/lib/utils";

function MockCheckoutForm() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const orderId = searchParams.get("order_id");
  const amount = searchParams.get("amount");
  const txn = searchParams.get("txn");

  const [state, setState] = React.useState<"idle" | "processing" | "done" | "failed">("idle");

  const pay = async (success: boolean) => {
    if (!orderId) return;
    setState("processing");
    try {
      await api.post(
        "/payments/webhook/mock",
        { order_id: orderId, transaction_id: txn, amount, success },
        { auth: false },
      );
      if (success) {
        setState("done");
        toast.success("To'lov tasdiqlandi!");
        setTimeout(() => router.push("/dashboard"), 1500);
      } else {
        setState("failed");
        toast.error("To'lov bekor qilindi");
      }
    } catch {
      setState("failed");
      toast.error("Webhook chaqirilmadi");
    }
  };

  if (!orderId) {
    return (
      <div className="container-page py-16">
        <Alert variant="error" title="Buyurtma topilmadi">
          URL manzilda <code className="font-mono">order_id</code> parametri yo&apos;q.
        </Alert>
      </div>
    );
  }

  return (
    <div className="container-page flex min-h-[70vh] items-center justify-center py-12">
      <div className="w-full max-w-md rounded-2xl border bg-card p-7 shadow-card-hover">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex size-11 items-center justify-center rounded-xl bg-accent/15 text-accent-foreground">
            <CreditCard className="size-5" />
          </span>
          <div>
            <h1 className="text-lg font-semibold">Sandbox to&apos;lov</h1>
            <p className="text-xs text-muted-foreground">Test rejimi — haqiqiy pul o&apos;tmaydi</p>
          </div>
        </div>

        <dl className="space-y-2.5 rounded-lg bg-muted/50 p-4 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Buyurtma</dt>
            <dd className="font-mono text-xs">{orderId.slice(0, 8)}…</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Tranzaksiya</dt>
            <dd className="font-mono text-xs">{txn ?? "—"}</dd>
          </div>
          <div className="flex justify-between border-t pt-2.5">
            <dt className="font-semibold">To&apos;lov summasi</dt>
            <dd className="text-lg font-bold">{formatPrice(amount)}</dd>
          </div>
        </dl>

        {state === "done" ? (
          <Alert variant="success" className="mt-5">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="size-4" /> To&apos;lov muvaffaqiyatli. Kurslar ochildi —
              dashboardga o&apos;tilmoqda...
            </span>
          </Alert>
        ) : state === "failed" ? (
          <Alert variant="error" className="mt-5">
            <span className="flex items-center gap-2">
              <XCircle className="size-4" /> To&apos;lov amalga oshmadi.
            </span>
          </Alert>
        ) : null}

        <div className="mt-6 space-y-2.5">
          <Button
            full
            size="lg"
            loading={state === "processing"}
            disabled={state === "done"}
            onClick={() => pay(true)}
          >
            To&apos;lovni tasdiqlash
          </Button>
          <Button
            full
            variant="outline"
            disabled={state === "processing" || state === "done"}
            onClick={() => pay(false)}
          >
            Bekor qilish
          </Button>
          <ButtonLink href="/cart" variant="ghost" full>
            Savatga qaytish
          </ButtonLink>
        </div>
      </div>
    </div>
  );
}

export default function MockCheckoutPage() {
  return (
    <React.Suspense
      fallback={
        <div className="container-page py-16">
          <div className="mx-auto h-80 max-w-md animate-pulse rounded-2xl bg-muted" />
        </div>
      }
    >
      <MockCheckoutForm />
    </React.Suspense>
  );
}
