import { Award, CheckCircle2, Download, ShieldCheck, XCircle } from "lucide-react";
import type { Metadata } from "next";

import { ButtonLink } from "@/components/ui/button";
import { api } from "@/lib/api-client";
import type { CertificateVerification } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Sertifikatni tekshirish",
  description: "Zehno.uz sertifikatining haqiqiyligini kod orqali tekshirish.",
};

async function verify(code: string): Promise<CertificateVerification | null> {
  try {
    return await api.get<CertificateVerification>(
      `/certificates/${encodeURIComponent(code)}/verify`,
      { auth: false, revalidate: 60 },
    );
  } catch {
    return null;
  }
}

export default async function CertificateVerifyPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;
  const result = await verify(code);
  const valid = result?.valid ?? false;

  return (
    <div className="container-page flex min-h-[70vh] items-center justify-center py-12">
      <div className="w-full max-w-lg">
        <div className="overflow-hidden rounded-2xl border bg-card shadow-card-hover">
          {/* Yuqori chizig'i */}
          <div className={valid ? "h-1.5 bg-secondary" : "h-1.5 bg-destructive"} />

          <div className="p-7">
            <div className="mb-6 flex items-center gap-3.5">
              <span
                className={`flex size-12 items-center justify-center rounded-xl ${
                  valid ? "bg-secondary/10 text-secondary" : "bg-destructive/10 text-destructive"
                }`}
              >
                {valid ? <ShieldCheck className="size-6" /> : <XCircle className="size-6" />}
              </span>
              <div>
                <h1 className="text-xl font-semibold">
                  {valid ? "Sertifikat haqiqiy" : "Sertifikat tasdiqlanmadi"}
                </h1>
                <p className="text-sm text-muted-foreground">
                  {result?.message ?? "Serverga ulanib bo'lmadi"}
                </p>
              </div>
            </div>

            <dl className="space-y-3 rounded-xl bg-muted/40 p-5 text-sm">
              <Row label="Sertifikat kodi">
                <span className="font-mono font-semibold">{code.toUpperCase()}</span>
              </Row>
              {valid ? (
                <>
                  <Row label="Talaba">{result?.student_name ?? "—"}</Row>
                  <Row label="Kurs">{result?.course_title ?? "—"}</Row>
                  <Row label="Ustoz">{result?.teacher_name ?? "—"}</Row>
                  <Row label="Berilgan sana">{formatDate(result?.issued_at)}</Row>
                </>
              ) : null}
            </dl>

            {valid ? (
              <div className="mt-6 flex flex-col gap-2.5 sm:flex-row">
                {result?.pdf_url ? (
                  <ButtonLink href={result.pdf_url} target="_blank" full>
                    <Download /> PDF yuklab olish
                  </ButtonLink>
                ) : null}
                <ButtonLink href="/courses" variant="outline" full>
                  Kurslarni ko&apos;rish
                </ButtonLink>
              </div>
            ) : (
              <div className="mt-6">
                <ButtonLink href="/certificates/verify" variant="outline" full>
                  Boshqa kodni tekshirish
                </ButtonLink>
              </div>
            )}
          </div>
        </div>

        <p className="mt-5 flex items-center justify-center gap-2 text-center text-xs text-muted-foreground">
          {valid ? (
            <>
              <CheckCircle2 className="size-3.5 text-secondary" />
              Bu sertifikat Zehno.uz ma&apos;lumotlar bazasida saqlanadi va istalgan vaqtda
              tekshirilishi mumkin
            </>
          ) : (
            <>
              <Award className="size-3.5" />
              Sertifikat kodini QR kod ostidan yoki PDF fayldan ko&apos;chirib oling
            </>
          )}
        </p>
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="shrink-0 text-muted-foreground">{label}</dt>
      <dd className="min-w-0 text-right font-medium">{children}</dd>
    </div>
  );
}
