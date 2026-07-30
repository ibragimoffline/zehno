import { CheckCircle2, Minus } from "lucide-react";
import type { Metadata } from "next";

import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Accordion } from "@/components/ui/misc";

export const metadata: Metadata = {
  title: "Narxlar",
  description:
    "Talabalar uchun kurs narxi, ustozlar uchun 15% komissiya, biznes uchun o'rin modeli.",
};

const PLANS = [
  {
    name: "Talaba",
    price: "Bepul",
    hint: "kurslar alohida sotib olinadi",
    features: [
      { text: "Bepul kurslarga cheksiz kirish", included: true },
      { text: "Sotib olingan kurslarga umrbod kirish", included: true },
      { text: "QR kodli sertifikat", included: true },
      { text: "Telegram eslatmalar", included: true },
      { text: "Testlar va amaliy topshiriqlar", included: true },
    ],
    cta: { label: "Ro'yxatdan o'tish", href: "/register" },
  },
  {
    name: "Ustoz / O'quv markaz",
    price: "15%",
    hint: "faqat sotuvdan komissiya",
    highlighted: true,
    features: [
      { text: "Cheksiz kurs va dars", included: true },
      { text: "Video hosting va himoyalangan streaming", included: true },
      { text: "Daromad paneli va payout", included: true },
      { text: "Kupon va chegirmalar", included: true },
      { text: "Talabalar statistikasi", included: true },
      { text: "Oylik abonent to'lovi", included: false },
    ],
    cta: { label: "Ustoz bo'lish", href: "/teach" },
  },
  {
    name: "Biznes (B2B)",
    price: "Kelishuv",
    hint: "o'rin (seat) modeli",
    features: [
      { text: "Bulk enroll (CSV)", included: true },
      { text: "Xodimlar progressi paneli", included: true },
      { text: "CRM integratsiyasi (Bitrix24/EspoCRM)", included: true },
      { text: "CSV/Excel hisobotlar", included: true },
      { text: "Litsenziya o'rinlarini boshqarish", included: true },
      { text: "Alohida menejer", included: true },
    ],
    cta: { label: "Taklif olish", href: "/business#contact" },
  },
];

export default function PricingPage() {
  return (
    <>
      <section className="border-b bg-gradient-to-br from-primary-50 to-background">
        <div className="container-page py-14 text-center">
          <h1 className="text-4xl sm:text-5xl">Shaffof narxlar</h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
            Yashirin to&apos;lovlar yo&apos;q.
          </p>
        </div>
      </section>

      <section className="container-page py-14">
        <div className="grid gap-6 lg:grid-cols-3">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={
                plan.highlighted
                  ? "relative rounded-2xl border-2 border-primary bg-card p-7 shadow-card-hover"
                  : "rounded-2xl border bg-card p-7 shadow-card"
              }
            >
              {plan.highlighted ? (
                <Badge variant="default" className="absolute -top-3 left-7">
                  Eng mashhur
                </Badge>
              ) : null}

              <h2 className="text-lg font-semibold">{plan.name}</h2>
              <p className="mt-3 text-3xl font-bold">{plan.price}</p>
              <p className="mt-1 text-sm text-muted-foreground">{plan.hint}</p>

              <ul className="mt-6 space-y-2.5">
                {plan.features.map((feature) => (
                  <li key={feature.text} className="flex items-start gap-2.5 text-sm">
                    {feature.included ? (
                      <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-secondary" />
                    ) : (
                      <Minus className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                    )}
                    <span
                      className={feature.included ? undefined : "text-muted-foreground line-through"}
                    >
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              <ButtonLink
                href={plan.cta.href}
                full
                size="lg"
                variant={plan.highlighted ? "default" : "outline"}
                className="mt-7"
              >
                {plan.cta.label}
              </ButtonLink>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t bg-muted/30 py-14">
        <div className="container-page mx-auto max-w-3xl">
          <h2 className="text-center text-2xl sm:text-3xl">Narxlar bo&apos;yicha savollar</h2>
          <div className="mt-8 space-y-3">
            {[
              {
                q: "Kurs narxini kim belgilaydi?",
                a: "Ustoz yoki o'quv markaz — chegirma narxi ham qo'yish mumkin.",
              },
              {
                q: "To'lovni qaytarish mumkinmi?",
                a: "Ha — 30 kun ichida, kurs 30% dan kam tugatilgan bo'lsa.",
              },
              {
                q: "B2B narxi qanday hisoblanadi?",
                a: "O'rinlar soniga qarab. 10 o'rindan boshlab chegirma.",
              },
            ].map((item, index) => (
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
