import { ShieldAlert } from "lucide-react";

import { ButtonLink } from "@/components/ui/button";

export const metadata = { title: "Ruxsat yo'q" };

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 text-center">
      <span className="mb-6 flex size-16 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
        <ShieldAlert className="size-8" />
      </span>
      <h1 className="text-3xl">Ruxsat yo&apos;q</h1>
      <p className="mt-3 max-w-md text-muted-foreground">
        Bu bo&apos;limga kirish uchun sizning rolingiz yetarli emas. Agar bu xato bo&apos;lsa,
        administratorga murojaat qiling.
      </p>
      <div className="mt-7 flex flex-wrap justify-center gap-3">
        <ButtonLink href="/">Bosh sahifa</ButtonLink>
        <ButtonLink href="/dashboard" variant="outline">
          Mening kurslarim
        </ButtonLink>
      </div>
    </div>
  );
}
