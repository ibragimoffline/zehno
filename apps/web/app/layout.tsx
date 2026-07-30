import type { Metadata, Viewport } from "next";

import "./globals.css";
import { Providers } from "./providers";

const siteName = process.env.NEXT_PUBLIC_SITE_NAME ?? "Zehno.uz";
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: `${siteName} — Onlayn ta'lim platformasi`,
    template: `%s · ${siteName}`,
  },
  description:
    "Zehno.uz — maktablar, xususiy ustozlar va o'quv markazlari uchun onlayn kurs platformasi. " +
    "Videodarsliklar, testlar, sertifikatlar va korporativ o'qitish.",
  keywords: [
    "onlayn kurs",
    "onlayn ta'lim",
    "video darslik",
    "sertifikat",
    "o'quv markaz",
    "Zehno",
  ],
  openGraph: {
    type: "website",
    locale: "uz_UZ",
    siteName,
    title: `${siteName} — Onlayn ta'lim platformasi`,
    description: "Istalgan ko'nikmani onlayn o'rganing — o'z tezligingizda, sertifikat bilan.",
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#2563EB",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="uz" suppressHydrationWarning>
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
        >
          Asosiy kontentga o&apos;tish
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
