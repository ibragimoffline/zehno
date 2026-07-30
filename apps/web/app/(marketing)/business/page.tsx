import {
  BarChart3,
  Building2,
  CheckCircle2,
  FileSpreadsheet,
  RefreshCw,
  ShieldCheck,
  Users,
} from "lucide-react";
import type { Metadata } from "next";

import { ButtonLink } from "@/components/ui/button";
import { Accordion } from "@/components/ui/misc";

export const metadata: Metadata = {
  title: "Biznes uchun",
  description:
    "Xodimlaringizni onlayn o'qitishga yozing, progressni kuzating va hisobotlarni CRM tizimingizga ulang.",
};

const FEATURES = [
  {
    icon: FileSpreadsheet,
    title: "Bulk enroll (CSV)",
    text: "Bir vaqtda yuzlab xodimni kursga yozing — CSV yuklaysiz, hisoblar avtomatik ochiladi.",
  },
  {
    icon: BarChart3,
    title: "Progress nazorati",
    text: "Har bir xodim bo'yicha tugatilgan darslar, test natijalari va sertifikat holati.",
  },
  {
    icon: RefreshCw,
    title: "CRM integratsiyasi",
    text: "Bitrix24 yoki EspoCRM — progress Contact kartochkasiga avtomatik yozib boriladi.",
  },
  {
    icon: Users,
    title: "Litsenziya o'rinlari",
    text: "N ta «o'rin» sotib olasiz, xodim ishdan ketsa o'rinni boshqasiga o'tkazasiz.",
  },
  {
    icon: ShieldCheck,
    title: "Sertifikat tekshiruvi",
    text: "Har bir sertifikat QR kodli — HR bo'limi bir necha soniyada haqiqiyligini tekshiradi.",
  },
  {
    icon: Building2,
    title: "Hisobotlar",
    text: "CSV/Excel export, haftalik avtomatik hisobot Telegram yoki email orqali.",
  },
];

const FAQ = [
  {
    q: "Qanday boshlash kerak?",
    a: "«Biznes» hisobini ochasiz (b2b_manager roli), tashkilotingizni yaratasiz, keyin B2B panelda kurslarni tanlab xodimlarni CSV orqali yozasiz.",
  },
  {
    q: "Xodimlarga parol qanday beriladi?",
    a: "Bulk enroll paytida yangi hisoblar vaqtinchalik parol bilan ochiladi. Xodim «parolni tiklash» orqali o'z parolini o'rnatadi.",
  },
  {
    q: "CRM'ga qanday ma'lumot yuboriladi?",
    a: "Kontakt (xodim) va kompaniya kartochkalari yaratiladi/yangilanadi, progress 25/50/75/100% bosqichlarida timeline izohi sifatida yoziladi, sertifikat kodi ham qo'shiladi.",
  },
  {
    q: "O'z kurslarimizni joylash mumkinmi?",
    a: "Ha. Tashkilot ichki kurslarini yaratib, faqat xodimlaringizga yozilish uchun ochib qo'yishingiz mumkin (org_admin roli orqali).",
  },
];

export default function BusinessPage() {
  return (
    <>
      <section className="border-b bg-gradient-to-br from-secondary/10 to-background">
        <div className="container-page py-16 text-center">
          <h1 className="text-balance text-4xl sm:text-5xl">
            Jamoangizni <span className="text-secondary">bir tizimda</span> o&apos;qitng
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground">
            Xodimlarni kursga yozing, progressni real vaqtda kuzating va natijalarni CRM
            tizimingizga ulang.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/register" size="lg" variant="secondary">
              Boshlash
            </ButtonLink>
            <ButtonLink href="#contact" size="lg" variant="outline">
              Bog&apos;lanish
            </ButtonLink>
          </div>
        </div>
      </section>

      <section id="reports" className="container-page py-14">
        <h2 className="text-center text-2xl sm:text-3xl">Korporativ funksiyalar</h2>
        <div className="mt-9 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="rounded-xl border bg-card p-6 shadow-card">
              <span className="mb-4 flex size-11 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
                <feature.icon className="size-5" />
              </span>
              <h3 className="font-semibold">{feature.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{feature.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="crm" className="border-y bg-muted/30 py-14">
        <div className="container-page grid items-center gap-8 lg:grid-cols-2">
          <div>
            <h2 className="text-2xl sm:text-3xl">CRM bilan integratsiya</h2>
            <p className="mt-3 text-muted-foreground">
              Platforma har bir muhim hodisada CRM&apos;ga ma&apos;lumot yuboradi — HR bo&apos;limi
              odatiy ish muhitini o&apos;zgartirmasdan progressni kuzatadi.
            </p>
            <ul className="mt-5 space-y-2.5">
              {[
                "Bitrix24 (bepul tarif — 12 foydalanuvchigacha)",
                "EspoCRM (self-hosted, cheklovsiz)",
                "Webhook orqali xohlagan tizimga ulash imkoniyati",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm">
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-secondary" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-2xl border bg-card p-6 font-mono text-xs shadow-card">
            <p className="mb-3 font-sans text-sm font-semibold">Sinxronizatsiya oqimi</p>
            <pre className="whitespace-pre-wrap text-muted-foreground">{`Xodim darsni tugatadi
      ↓
Platform → "progress_updated" event
      ↓
Celery queue (Redis)
      ↓
CRM adapter (Bitrix24 / EspoCRM)
      ↓
Contact timeline: "Progress: 75%"`}</pre>
          </div>
        </div>
      </section>

      <section id="contact" className="container-page py-14">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-center text-2xl sm:text-3xl">Savollar</h2>
          <div className="mt-8 space-y-3">
            {FAQ.map((item, index) => (
              <Accordion key={item.q} title={item.q} defaultOpen={index === 0}>
                <p className="text-sm text-muted-foreground">{item.a}</p>
              </Accordion>
            ))}
          </div>

          <div className="mt-10 rounded-2xl border bg-card p-7 text-center">
            <h3 className="text-xl font-semibold">Korporativ taklif olish</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Xodimlar soni va yo&apos;nalishlarni yozib yuboring — 1 ish kuni ichida taklif
              tayyorlaymiz.
            </p>
            <div className="mt-5 flex flex-wrap justify-center gap-3">
              <ButtonLink href="mailto:b2b@zehno.uz" variant="secondary">
                b2b@zehno.uz
              </ButtonLink>
              <ButtonLink href="https://t.me/zehno_uz" target="_blank" variant="outline">
                Telegram orqali yozish
              </ButtonLink>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
