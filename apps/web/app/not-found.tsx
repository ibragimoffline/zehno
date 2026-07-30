import { SearchX } from "lucide-react";

import { ButtonLink } from "@/components/ui/button";

export const metadata = { title: "Sahifa topilmadi" };

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <span className="mb-6 flex size-16 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
        <SearchX className="size-8" />
      </span>
      <p className="font-mono text-sm text-muted-foreground">404</p>
      <h1 className="mt-2 text-3xl">Sahifa topilmadi</h1>
      <p className="mt-3 max-w-md text-muted-foreground">
        Siz izlagan sahifa o&apos;chirilgan yoki manzil xato kiritilgan bo&apos;lishi mumkin.
      </p>
      <div className="mt-7 flex flex-wrap justify-center gap-3">
        <ButtonLink href="/">Bosh sahifa</ButtonLink>
        <ButtonLink href="/courses" variant="outline">
          Kurslar katalogi
        </ButtonLink>
      </div>
    </div>
  );
}
