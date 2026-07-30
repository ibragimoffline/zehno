import { GraduationCap, Mail, MapPin, Phone, Send } from "lucide-react";
import Link from "next/link";

const FOOTER_SECTIONS = [
  {
    title: "Platforma",
    links: [
      { href: "/courses", label: "Barcha kurslar" },
      { href: "/courses?is_free=true", label: "Bepul kurslar" },
      { href: "/certificates/verify", label: "Sertifikatni tekshirish" },
      { href: "/pricing", label: "Narxlar" },
    ],
  },
  {
    title: "Ustozlar uchun",
    links: [
      { href: "/teach", label: "Kursingizni joylang" },
      { href: "/teacher/courses/new", label: "Kurs yaratish" },
      { href: "/teach#commission", label: "Komissiya shartlari" },
      { href: "/teach#faq", label: "Ustozlar FAQ" },
    ],
  },
  {
    title: "Biznes",
    links: [
      { href: "/business", label: "Jamoangiz uchun" },
      { href: "/business#crm", label: "CRM integratsiyasi" },
      { href: "/business#reports", label: "Hisobotlar" },
      { href: "/business#contact", label: "Bog'lanish" },
    ],
  },
  {
    title: "Kompaniya",
    links: [
      { href: "/about", label: "Biz haqimizda" },
      { href: "/contact", label: "Aloqa" },
      { href: "/terms", label: "Foydalanish shartlari" },
      { href: "/privacy", label: "Maxfiylik siyosati" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="container-page py-12">
        <div className="grid gap-10 lg:grid-cols-[1.4fr_repeat(4,1fr)]">
          <div>
            <Link href="/" className="flex items-center gap-2">
              <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <GraduationCap className="size-5" />
              </span>
              <span className="text-lg font-bold">
                Zehno<span className="text-primary">.uz</span>
              </span>
            </Link>

            <p className="mt-4 max-w-sm text-sm text-muted-foreground">
              Maktablar, ustozlar va o&apos;quv markazlari uchun onlayn ta&apos;lim platformasi.
            </p>

            <div className="mt-5 space-y-2 text-sm text-muted-foreground">
              <a href="tel:+998900000000" className="flex items-center gap-2 hover:text-foreground">
                <Phone className="size-4" /> +998 90 000 00 00
              </a>
              <a href="mailto:info@zehno.uz" className="flex items-center gap-2 hover:text-foreground">
                <Mail className="size-4" /> info@zehno.uz
              </a>
              <p className="flex items-center gap-2">
                <MapPin className="size-4" /> Toshkent, O&apos;zbekiston
              </p>
              <a
                href="https://t.me/zehno_uz"
                target="_blank"
                rel="noreferrer noopener"
                className="flex items-center gap-2 hover:text-foreground"
              >
                <Send className="size-4" /> Telegram kanal
              </a>
            </div>
          </div>

          {FOOTER_SECTIONS.map((section) => (
            <div key={section.title}>
              <h3 className="mb-3 text-sm font-semibold">{section.title}</h3>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link.href + link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground hover:text-foreground"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t pt-6 text-sm text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} Zehno.uz — barcha huquqlar himoyalangan.</p>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-secondary" aria-hidden />
              To&apos;lov: Payme · Click · Uzcard
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
