"use client";

import { AlertTriangle } from "lucide-react";
import * as React from "react";

import { Button, ButtonLink } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    // Production'da bu joyga Sentry kabi monitoring ulanadi (ADDITIONAL_FEATURES 7)
    console.error("Sahifa xatosi:", error);
  }, [error]);

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-6 text-center">
      <span className="mb-6 flex size-16 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
        <AlertTriangle className="size-8" />
      </span>
      <h1 className="text-3xl">Nimadir xato ketdi</h1>
      <p className="mt-3 max-w-md text-muted-foreground">
        Kutilmagan xatolik yuz berdi. Sahifani qayta yuklashga harakat qiling.
      </p>
      {error.digest ? (
        <p className="mt-2 font-mono text-xs text-muted-foreground">ID: {error.digest}</p>
      ) : null}
      <div className="mt-7 flex flex-wrap justify-center gap-3">
        <Button onClick={reset}>Qayta urinish</Button>
        <ButtonLink href="/" variant="outline">
          Bosh sahifa
        </ButtonLink>
      </div>
    </div>
  );
}
