"use client";

import { ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";

export default function VerifyFormPage() {
  const router = useRouter();
  const [code, setCode] = React.useState("");

  return (
    <div className="container-page flex min-h-[70vh] items-center justify-center py-12">
      <div className="w-full max-w-md rounded-2xl border bg-card p-7 shadow-card">
        <span className="mb-5 flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <ShieldCheck className="size-6" />
        </span>

        <h1 className="text-2xl">Sertifikatni tekshirish</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">
          Sertifikatdagi unikal kodni kiriting yoki QR kodni skanerlang.
        </p>

        <form
          className="mt-6 space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            const value = code.trim().toUpperCase();
            if (value) router.push(`/certificates/${encodeURIComponent(value)}`);
          }}
        >
          <Field label="Sertifikat kodi" htmlFor="code" hint="Masalan: ZH-4KX9-TL2M" required>
            <Input
              value={code}
              onChange={(event) => setCode(event.target.value.toUpperCase())}
              placeholder="ZH-XXXX-XXXX"
              className="font-mono uppercase"
              required
            />
          </Field>

          <Button type="submit" full size="lg" disabled={!code.trim()}>
            Tekshirish
          </Button>
        </form>
      </div>
    </div>
  );
}
