import {
  ArrowRight,
  Award,
  BarChart3,
  Building2,
  CheckCircle2,
  Clock,
  GraduationCap,
  Smartphone,
  Sparkles,
  Star,
  TrendingUp,
  Users,
} from "lucide-react";
import Link from "next/link";

import { CourseCard } from "@/components/course/course-card";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Accordion } from "@/components/ui/misc";
import { api } from "@/lib/api-client";
import type { Category, CourseCard as CourseCardType } from "@/lib/types";

// Landing SEO uchun ISR — har 5 daqiqada yangilanadi (ARCHITECTURE 5: SSR muhim)
export const revalidate = 300;

async function loadLandingData() {
  const [categories, featured] = await Promise.all([
    api
      .get<Category[]>("/categories", { auth: false, revalidate: 600 })
      .catch(() => [] as Category[]),
    api
      .get<CourseCardType[]>("/courses/featured", {
        auth: false,
        query: { limit: 8 },
        revalidate: 300,
      })
      .catch(() => [] as CourseCardType[]),
  ]);
  return { categories, featured };
}

const BENEFITS = [
  {
    icon: Award,
    title: "Rasmiy sertifikat",
    text: "Kursni tugatgach QR kodli sertifikat olasiz — uni istalgan ish beruvchi tekshira oladi.",
  },
  {
    icon: Clock,
    title: "O'z tezligingizda",
    text: "Darslarni istalgan vaqtda, istalgan joyda ko'ring. Umrbod kirish huquqi.",
  },
  {
    icon: GraduationCap,
    title: "Ekspert ustozlar",
    text: "Har bir kurs moderatsiyadan o'tadi — faqat sifatli kontent katalogga tushadi.",
  },
  {
    icon: Smartphone,
    title: "Mobil qulaylik",
    text: "Telefon, planshet, kompyuter — barchasida bir xil qulay interfeys.",
  },
];

const FAQ = [
  {
    q: "Kursni sotib olgach qancha vaqt kirish huquqim bo'ladi?",
    a: "Kurslarga umrbod kirish huquqi beriladi. Bir marta sotib olsangiz, materiallar doimo sizda qoladi va ustoz kursni yangilaganda yangilanishlar ham bepul ochiladi.",
  },
  {
    q: "To'lovni qanday amalga oshirsam bo'ladi?",
    a: "Payme, Click va Uzcard/Humo kartalari qo'llab-quvvatlanadi. To'lov tasdiqlangach kurs avtomatik ochiladi va Telegram orqali xabar keladi.",
  },
  {
    q: "Sertifikat qanday tekshiriladi?",
    a: "Har bir sertifikatda unikal kod va QR kod bo'ladi. Ish beruvchi zehno.uz/certificates/KOD manzilida uni bir necha soniyada tekshira oladi.",
  },
  {
    q: "Men ustozman — kursimni qanday joylashtiraman?",
    a: "Ro'yxatdan «Ustoz» roli bilan o'tasiz, bosqichma-bosqich ustada kurs yaratasiz (ma'lumot → modullar → video → narx), moderatsiyaga yuborasiz. Tasdiqlangach kurs katalogda paydo bo'ladi.",
  },
  {
    q: "Kurs pulini qanday olaman?",
    a: "Har bir sotuvdan platforma komissiyasi (15%) ushlanadi, qolgani sizning balansingizga tushadi. Daromad bo'limidan pul yechish so'rovini yuborasiz.",
  },
  {
    q: "Kompaniyam uchun xodimlarni o'qitmoqchiman. Qanday?",
    a: "B2B panelida CSV orqali xodimlarni bir vaqtda kursga yozasiz, progressni jadval ko'rinishida kuzatasiz va hisobotlarni Excel/CSV formatida yuklab olasiz. Bitrix24 bilan integratsiya ham mavjud.",
  },
];

export default async function LandingPage() {
  const { categories, featured } = await loadLandingData();

  return (
    <>
      {/* ================= HERO ================= */}
      <section className="relative overflow-hidden border-b bg-gradient-to-br from-primary-50 via-background to-secondary/5">
        <div className="container-page grid items-center gap-10 py-16 lg:grid-cols-2 lg:py-24">
          <div>
            <Badge variant="default" className="mb-5">
              <Sparkles className="size-3" /> O&apos;zbekistondagi onlayn ta&apos;lim platformasi
            </Badge>

            <h1 className="text-balance text-4xl leading-[1.1] sm:text-5xl lg:text-6xl">
              Istalgan ko&apos;nikmani <span className="text-primary">onlayn o&apos;rganing</span>
            </h1>

            <p className="mt-5 max-w-xl text-lg text-muted-foreground">
              Videodarsliklar, amaliy testlar va rasmiy sertifikat. Eng yaxshi ustozlar va o&apos;quv
              markazlaridan — bitta platformada.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="/courses" size="lg">
                Kurslarni ko&apos;rish <ArrowRight className="size-5" />
              </ButtonLink>
              <ButtonLink href="/courses?is_free=true" size="lg" variant="outline">
                Bepul boshlash
              </ButtonLink>
            </div>

            <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
              {["Umrbod kirish", "QR kodli sertifikat", "Mobil qurilmalarda"].map((item) => (
                <li key={item} className="flex items-center gap-1.5">
                  <CheckCircle2 className="size-4 text-secondary" /> {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Hero vizual */}
          <div className="relative hidden lg:block">
            <div className="relative rounded-2xl border bg-card p-6 shadow-card-hover">
              <div className="player-frame flex items-center justify-center bg-gradient-to-br from-primary to-primary-700">
                <GraduationCap className="size-16 text-white/90" />
              </div>
              <div className="mt-4 space-y-3">
                <div className="h-3 w-3/4 rounded-full bg-muted" />
                <div className="h-3 w-1/2 rounded-full bg-muted" />
                <div className="mt-4 flex items-center gap-3">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                    <div className="h-full w-[62%] rounded-full bg-secondary" />
                  </div>
                  <span className="text-xs font-semibold text-muted-foreground">62%</span>
                </div>
              </div>
            </div>

            <div className="absolute -bottom-5 -left-6 flex items-center gap-3 rounded-xl border bg-card p-3.5 shadow-card-hover">
              <span className="flex size-10 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                <Award className="size-5" />
              </span>
              <div>
                <p className="text-sm font-semibold">Sertifikat tayyor!</p>
                <p className="text-xs text-muted-foreground">ZH-4KX9-TL2M</p>
              </div>
            </div>

            <div className="absolute -right-4 -top-5 flex items-center gap-2 rounded-xl border bg-card p-3 shadow-card-hover">
              <Star className="size-4 fill-accent-500 text-accent-500" />
              <span className="text-sm font-semibold">4.8</span>
              <span className="text-xs text-muted-foreground">o&apos;rtacha reyting</span>
            </div>
          </div>
        </div>
      </section>

      {/* ================= STATISTIKA ================= */}
      <section className="border-b bg-card">
        <div className="container-page grid grid-cols-2 gap-6 py-8 sm:grid-cols-4">
          {[
            { icon: Users, value: "10 000+", label: "talaba" },
            { icon: GraduationCap, value: "500+", label: "kurs" },
            { icon: Award, value: "200+", label: "ustoz" },
            { icon: TrendingUp, value: "92%", label: "tugatish darajasi" },
          ].map((stat) => (
            <div key={stat.label} className="flex items-center gap-3">
              <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <stat.icon className="size-5" />
              </span>
              <div>
                <p className="text-xl font-bold">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ================= KATEGORIYALAR ================= */}
      <section className="container-page py-14">
        <div className="mb-7 flex items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl sm:text-3xl">Yo&apos;nalishlar</h2>
            <p className="mt-1.5 text-muted-foreground">O&apos;zingizga mos sohani tanlang</p>
          </div>
          <Link
            href="/courses"
            className="hidden shrink-0 text-sm font-medium text-primary hover:underline sm:block"
          >
            Barcha kurslar →
          </Link>
        </div>

        {categories.length > 0 ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {categories.slice(0, 8).map((category) => (
              <Link
                key={category.id}
                href={`/courses?category=${category.slug}`}
                className="group rounded-xl border bg-card p-5 transition-colors hover:border-primary hover:bg-primary/5"
              >
                <p className="font-semibold group-hover:text-primary">{category.name}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {category.courses_count} kurs
                </p>
              </Link>
            ))}
          </div>
        ) : (
          <p className="rounded-xl border border-dashed p-8 text-center text-muted-foreground">
            Kategoriyalar hali yuklanmagan. Backend ishga tushgach avtomatik ko&apos;rinadi.
          </p>
        )}
      </section>

      {/* ================= MASHHUR KURSLAR ================= */}
      <section className="border-y bg-muted/30 py-14">
        <div className="container-page">
          <div className="mb-7 flex items-end justify-between gap-4">
            <div>
              <h2 className="text-2xl sm:text-3xl">Mashhur kurslar</h2>
              <p className="mt-1.5 text-muted-foreground">
                Talabalar eng ko&apos;p tanlagan kurslar
              </p>
            </div>
            <Link
              href="/courses?sort=popular"
              className="hidden shrink-0 text-sm font-medium text-primary hover:underline sm:block"
            >
              Barchasini ko&apos;rish →
            </Link>
          </div>

          {featured.length > 0 ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {featured.map((course) => (
                <CourseCard key={course.id} course={course} />
              ))}
            </div>
          ) : (
            <p className="rounded-xl border border-dashed bg-card p-8 text-center text-muted-foreground">
              Hali nashr etilgan kurslar yo&apos;q. Demo kontent uchun{" "}
              <code className="font-mono text-xs">python -m app.cli seed</code> ni ishga tushiring.
            </p>
          )}
        </div>
      </section>

      {/* ================= NEGA ZEHNO ================= */}
      <section className="container-page py-14">
        <h2 className="text-center text-2xl sm:text-3xl">Nega Zehno.uz?</h2>
        <p className="mx-auto mt-2 max-w-2xl text-center text-muted-foreground">
          Ta&apos;lim jarayonining har bir bosqichi o&apos;ylab ishlangan
        </p>

        <div className="mt-9 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {BENEFITS.map((benefit) => (
            <div key={benefit.title} className="rounded-xl border bg-card p-6 shadow-card">
              <span className="mb-4 flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <benefit.icon className="size-5" />
              </span>
              <h3 className="text-base font-semibold">{benefit.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{benefit.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ================= USTOZ + B2B ================= */}
      <section className="container-page pb-14">
        <div className="grid gap-5 lg:grid-cols-2">
          <div className="rounded-2xl border bg-gradient-to-br from-primary to-primary-700 p-8 text-white">
            <span className="mb-4 inline-flex size-11 items-center justify-center rounded-xl bg-white/15">
              <GraduationCap className="size-5" />
            </span>
            <h3 className="text-2xl font-bold">Kursingizni joylang</h3>
            <p className="mt-2.5 max-w-md text-white/85">
              Ustoz, maktab yoki o&apos;quv markaz bo&apos;lsangiz — bilimingizni pulga aylantiring.
              Video yuklaysiz, biz to&apos;lov, sertifikat va marketingni hal qilamiz.
            </p>
            <ul className="mt-5 space-y-2 text-sm text-white/90">
              {[
                "Sotuvdan 85% sizga",
                "Bosqichma-bosqich kurs yaratish ustasi",
                "Daromad va talabalar statistikasi",
              ].map((item) => (
                <li key={item} className="flex items-center gap-2">
                  <CheckCircle2 className="size-4" /> {item}
                </li>
              ))}
            </ul>
            <ButtonLink
              href="/teach"
              size="lg"
              className="mt-7 bg-white text-primary hover:bg-white/90"
            >
              Ustoz bo&apos;lish →
            </ButtonLink>
          </div>

          <div className="rounded-2xl border bg-card p-8 shadow-card">
            <span className="mb-4 inline-flex size-11 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
              <Building2 className="size-5" />
            </span>
            <h3 className="text-2xl font-bold">Jamoangiz uchun</h3>
            <p className="mt-2.5 max-w-md text-muted-foreground">
              Xodimlaringizni bir vaqtda o&apos;qitishga yozing, progressni real vaqtda kuzating va
              hisobotlarni CRM tizimingizga ulang.
            </p>
            <ul className="mt-5 space-y-2 text-sm">
              {[
                { icon: Users, text: "CSV orqali ko'p xodimni bir vaqtda yozish" },
                { icon: BarChart3, text: "Progress va sertifikat holati jadvali" },
                { icon: Building2, text: "Bitrix24 / EspoCRM integratsiyasi" },
              ].map((item) => (
                <li key={item.text} className="flex items-center gap-2.5 text-muted-foreground">
                  <item.icon className="size-4 shrink-0 text-secondary" /> {item.text}
                </li>
              ))}
            </ul>
            <ButtonLink href="/business" variant="outline" size="lg" className="mt-7">
              Korporativ taklif →
            </ButtonLink>
          </div>
        </div>
      </section>

      {/* ================= FIKRLAR ================= */}
      <section className="border-y bg-muted/30 py-14">
        <div className="container-page">
          <h2 className="text-center text-2xl sm:text-3xl">Talabalar fikri</h2>

          <div className="mt-9 grid gap-5 md:grid-cols-3">
            {[
              {
                name: "Sardor Mahmudov",
                role: "Frontend dasturchi",
                text: "Kursdan keyin 3 oy ichida ishga kirdim. Amaliy loyihalar juda foydali bo'ldi — portfolio to'g'ridan-to'g'ri kurs ichida yaratildi.",
              },
              {
                name: "Nilufar Karimova",
                role: "IELTS 7.5",
                text: "Speaking bo'limi bo'yicha strategiyalar ishladi. Ustoz har bir javobni batafsil tahlil qilib bergani uchun xatolarimni tez tuzatdim.",
              },
              {
                name: "Jasur Toshev",
                role: "HR menejer",
                text: "Kompaniyamizda 40 xodimni bir vaqtda o'qitdik. B2B paneldagi hisobotlar bevosita Bitrix24'ga tushib turdi — juda qulay.",
              },
            ].map((review) => (
              <figure key={review.name} className="rounded-xl border bg-card p-6 shadow-card">
                <div className="mb-3 flex gap-0.5">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star key={star} className="size-4 fill-accent-500 text-accent-500" />
                  ))}
                </div>
                <blockquote className="text-sm text-muted-foreground">
                  &laquo;{review.text}&raquo;
                </blockquote>
                <figcaption className="mt-4 border-t pt-4">
                  <p className="text-sm font-semibold">{review.name}</p>
                  <p className="text-xs text-muted-foreground">{review.role}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      {/* ================= FAQ ================= */}
      <section className="container-page py-14">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-center text-2xl sm:text-3xl">Tez-tez so&apos;raladigan savollar</h2>

          <div className="mt-8 space-y-3">
            {FAQ.map((item, index) => (
              <Accordion key={item.q} title={item.q} defaultOpen={index === 0}>
                <p className="text-sm text-muted-foreground">{item.a}</p>
              </Accordion>
            ))}
          </div>
        </div>
      </section>

      {/* ================= CTA ================= */}
      <section className="border-t bg-primary py-14 text-white">
        <div className="container-page text-center">
          <h2 className="text-3xl font-bold">Bugun o&apos;rganishni boshlang</h2>
          <p className="mx-auto mt-3 max-w-xl text-white/85">
            Bepul kurslardan boshlang — kredit karta talab qilinmaydi.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <ButtonLink href="/register" size="lg" className="bg-white text-primary hover:bg-white/90">
              Ro&apos;yxatdan o&apos;tish
            </ButtonLink>
            <ButtonLink
              href="/courses"
              size="lg"
              variant="outline"
              className="border-white/40 bg-transparent text-white hover:bg-white/10"
            >
              Katalogni ko&apos;rish
            </ButtonLink>
          </div>
        </div>
      </section>
    </>
  );
}
