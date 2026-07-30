import {
  BarChart3,
  CheckCircle2,
  CreditCard,
  GraduationCap,
  Upload,
  Users,
  Video,
} from "lucide-react";
import type { Metadata } from "next";

import { ButtonLink } from "@/components/ui/button";
import { Accordion } from "@/components/ui/misc";

export const metadata: Metadata = {
  title: "Ustozlar uchun",
  description:
    "Kursingizni joylang — sotuvdan 85% sizga.",
};

const STEPS = [
  { icon: GraduationCap, title: "1. Ro'yxatdan o'ting", text: "«Ustozman» rolini tanlang" },
  { icon: Upload, title: "2. Kursni quring", text: "Modul → dars → narx" },
  { icon: Video, title: "3. Video yuklang", text: "Transkodlash va streaming bizda" },
  { icon: CreditCard, title: "4. Sotuvni boshlang", text: "To'lovlar Payme/Click orqali" },
];

const FAQ = [
  { q: "Komissiya qancha?", a: "15%. Oylik abonent to'lovi yo'q." },
  { q: "Pulni qanday olaman?", a: "«Daromad» bo'limidan so'rov yuborasiz, admin tasdiqlaydi." },
  {
    q: "Videolarim himoyalanganmi?",
    a: "Ha — faqat sotib olganlarga 10-15 daqiqalik signed havola beriladi.",
  },
  { q: "Moderatsiya qancha vaqt oladi?", a: "Odatda 1-2 ish kuni." },
  {
    q: "Test va sertifikat qo'shsam bo'ladimi?",
    a: "Ha — kurs 100% tugatilganda QR kodli PDF sertifikat avtomatik beriladi.",
  },
];

export default function TeachPage() {
  return (
    <>
      <section className="border-b bg-gradient-to-br from-primary-50 to-background">
        <div className="container-page py-16 text-center">
          <h1 className="text-balance text-4xl sm:text-5xl">
            Bilimingizni <span className="text-primary">daromadga</span> aylantiring
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground">
            Sotuvdan 85% sizga — to&apos;lov, video hosting va sertifikat bizda.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/register" size="lg">
              Ustoz bo&apos;lib boshlash
            </ButtonLink>
            <ButtonLink href="/teacher/courses/new" size="lg" variant="outline">
              Kurs yaratish
            </ButtonLink>
          </div>
        </div>
      </section>

      <section className="container-page py-14">
        <h2 className="text-center text-2xl sm:text-3xl">Qanday ishlaydi</h2>
        <div className="mt-9 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step) => (
            <div key={step.title} className="rounded-xl border bg-card p-6 shadow-card">
              <span className="mb-4 flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <step.icon className="size-5" />
              </span>
              <h3 className="font-semibold">{step.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="commission" className="border-y bg-muted/30 py-14">
        <div className="container-page grid gap-8 lg:grid-cols-2">
          <div>
            <h2 className="text-2xl sm:text-3xl">Shaffof shartlar</h2>
            <ul className="mt-5 space-y-3">
              {[
                "Platforma komissiyasi — 15%, boshqa to'lov yo'q",
                "Kursni istalgan vaqtda tahrirlash va narxini o'zgartirish",
                "Chegirma kuponlari va aksiyalar yaratish",
                "Talabalar progressi va daromad statistikasi",
                "Telegram orqali sotuv haqida darhol xabar",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-secondary" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {[
              { icon: BarChart3, title: "Daromad paneli", text: "Grafik, tranzaksiyalar, payout" },
              { icon: Users, title: "Talabalar", text: "Progress, sertifikat holati" },
              { icon: Video, title: "Video hosting", text: "PeerTube / Kinescope / Bunny" },
              { icon: CreditCard, title: "To'lovlar", text: "Payme, Click, Uzcard" },
            ].map((card) => (
              <div key={card.title} className="rounded-xl border bg-card p-5">
                <card.icon className="mb-3 size-5 text-primary" />
                <p className="font-semibold">{card.title}</p>
                <p className="mt-0.5 text-sm text-muted-foreground">{card.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="faq" className="container-page py-14">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-center text-2xl sm:text-3xl">Ustozlar uchun FAQ</h2>
          <div className="mt-8 space-y-3">
            {FAQ.map((item, index) => (
              <Accordion key={item.q} title={item.q} defaultOpen={index === 0}>
                <p className="text-sm text-muted-foreground">{item.a}</p>
              </Accordion>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
