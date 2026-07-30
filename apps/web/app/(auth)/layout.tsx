import { CheckCircle2, GraduationCap } from "lucide-react";
import Link from "next/link";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="flex flex-col px-5 py-8 sm:px-10">
        <Link href="/" className="flex items-center gap-2 self-start">
          <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <GraduationCap className="size-5" />
          </span>
          <span className="text-lg font-bold">
            Zehno<span className="text-primary">.uz</span>
          </span>
        </Link>

        <main id="main-content" className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-sm">{children}</div>
        </main>

        <p className="text-center text-xs text-muted-foreground">
          Davom etish orqali{" "}
          <Link href="/terms" className="underline hover:text-foreground">
            foydalanish shartlari
          </Link>{" "}
          va{" "}
          <Link href="/privacy" className="underline hover:text-foreground">
            maxfiylik siyosati
          </Link>
          ga rozilik bildirasiz.
        </p>
      </div>

      <aside className="relative hidden flex-col justify-center bg-gradient-to-br from-primary to-primary-900 p-12 text-white lg:flex">
        <h2 className="text-3xl font-bold leading-tight">
          Bilim — eng foydali
          <br />
          sarmoya
        </h2>
        <p className="mt-4 max-w-md text-white/85">
          10 000+ talaba Zehno.uz orqali yangi kasb egallaydi.
        </p>

        <ul className="mt-8 space-y-3">
          {[
            "500+ kurs — IT, tillar, biznes, dizayn",
            "Videodarslik + amaliy testlar",
            "QR kodli tekshiriladigan sertifikat",
            "Telegram orqali eslatmalar",
          ].map((item) => (
            <li key={item} className="flex items-start gap-2.5 text-sm text-white/90">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
              {item}
            </li>
          ))}
        </ul>

        <div className="mt-10 rounded-xl bg-white/10 p-5 backdrop-blur">
          <p className="text-sm text-white/90">
            &laquo;Kursdan keyin 3 oy ichida ishga kirdim. Amaliy loyihalar juda foydali
            bo&apos;ldi.&raquo;
          </p>
          <p className="mt-3 text-xs font-semibold">Sardor M. — Frontend dasturchi</p>
        </div>
      </aside>
    </div>
  );
}
