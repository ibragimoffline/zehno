# Texnologik qarorlar va spetsifikatsiyadan farqlar

Ushbu fayl loyihaning boshlang'ich spetsifikatsiyalari (`ARCHITECTURE.md`, `FRONTEND_UX_UI.md`,
`ADDITIONAL_FEATURES.md`) bilan **amaldagi implementatsiya** orasidagi farqlarni va sabablarini
qayd etadi.

---

## 1. Talab bo'yicha o'zgarishlar

| Spetsifikatsiyada | Amalda | Sabab |
|---|---|---|
| Loyiha nomi: EduHub | **Zehno.uz** | Buyurtmachi talabi |
| Backend: NestJS (TypeScript) yoki Django | **FastAPI (Python)** | Buyurtmachi talabi |
| Auth: JWT + Refresh | **JWT `python-jose`** + refresh rotatsiyasi | Buyurtmachi talabi |
| Queue: BullMQ yoki Celery | **Celery + Redis** (worker + beat) | Buyurtmachi talabi |
| Konteynerlash | **Docker + Docker Compose** | Buyurtmachi talabi |

Qolgan barcha qarorlar (PostgreSQL, Next.js, MinIO, adapter pattern, PeerTube/Bitrix24/Payme/Click,
Telegram bot, modulli monolit) spetsifikatsiyaga muvofiq saqlangan.

---

## 2. Implementatsiya paytida qabul qilingan qarorlar

### 2.1 Ma'lumotlar bazasi: `PAYMENTS.enrollment_id` → `Order`/`OrderItem`

ER-diagrammada to'lov to'g'ridan-to'g'ri enrollment'ga bog'langan edi. Savatda bir vaqtda bir
nechta kurs bo'lishi mumkinligi uchun bir qadam normalizatsiya kiritildi:

```
CartItem → Order → OrderItem[]  →  Payment (bitta tranzaksiya)
                             └→  Enrollment[] (to'lov tasdiqlangach ochiladi)
```

Bu B2B bulk-xaridni ham tabiiy qoplaydi va komissiya hisobini `OrderItem` darajasida "muzlatib"
saqlaydi (kurs narxi keyin o'zgarsa ham hisobot to'g'ri qoladi).

### 2.2 Enum'lar `VARCHAR + CHECK` sifatida

`Enum(..., native_enum=False)` ishlatilgan — PostgreSQL native enum'ga nisbatan migratsiya qilish
osonroq va SQLite'da test o'tkazish imkonini beradi.

### 2.3 Ikki xil DB engine

* **async** (`asyncpg`) — FastAPI request'lari uchun
* **sync** (`psycopg`) — Celery task'lari va CLI uchun

Celery task'lari sinxron bo'lgani uchun har bir task ichida `asyncio.run()` chaqirish o'rniga
alohida sinxron sessiya ishlatiladi (`app.db.session.sync_session`). Faqat async adapterlar
(httpx) chaqirilganda `asyncio.run()` qo'llanadi.

### 2.4 `CourseAdminSummary` va `CourseAdminDetail` ajratilgan

Async SQLAlchemy lazy-load qila olmaydi (`MissingGreenlet`). Shu sababli `modules` maydoni faqat
modul va darslar eager-load qilingan endpointda (`GET /teacher/courses/{id}`) qaytariladi; ro'yxat
va CRUD javoblari `modules` siz `CourseAdminSummary` qaytaradi.

### 2.5 PDF: Puppeteer emas, `fpdf2`

Spetsifikatsiyada Puppeteer yoki PDFKit taklif qilingan edi (Node ekosistemasi). Python backend
uchun `fpdf2` tanlandi — sof Python, tizim kutubxonalari talab qilmaydi, konteyner hajmi kichik
qoladi. Kirill matnlar PDF'da translit qilinadi (standart Helvetica shrifti latin-1 bilan
cheklangan). Kelajakda `TTF` shrift qo'shib to'liq Unicode qilish mumkin.

### 2.6 `mock` provayderlar

Har bir integratsiya turi uchun `mock` adapter yozildi:

* **mock video** — faylni MinIO'ga yuklab presigned URL beradi (PeerTube o'rnatilmagan holatda ham
  yuklash → ko'rish → progress oqimi to'liq ishlaydi)
* **mock to'lov** — `/checkout/mock` sahifasida "To'lovni tasdiqlash" tugmasi webhook'ni chaqiradi
  (Payme/Click merchant kalitlarisiz to'liq oqimni sinash mumkin)
* **mock CRM** — barcha sinxronizatsiya `crm_sync_log` jadvaliga yoziladi (ichki mini-CRM)

### 2.7 Boshlang'ich migratsiya avtomatik generatsiya qilinadi

`python -m app.cli migrate` — `alembic/versions/` bo'sh bo'lsa modellar asosida boshlang'ich
migratsiyani generatsiya qilib qo'llaydi. Fayl repozitoriyada saqlanadi va keyingi o'zgarishlar
unga nisbatan hisoblanadi. Bu "birinchi `docker compose up` da jadvallar yo'q" muammosini yechadi.

### 2.8 Teacher uchun alohida talabalar endpointi

`GET /api/v1/teacher/students` qo'shildi — ustoz faqat o'zi (yoki tashkiloti) egasi bo'lgan
kurslardagi enrollment'larni ko'radi. B2B endpointidan foydalanish RBAC nuqtai nazaridan to'g'ri
bo'lmaydi.

---

## 3. Frontend qarorlari

| Qaror | Sabab |
|---|---|
| shadcn/ui CLI o'rniga **qo'lda yozilgan primitivlar** (`components/ui/`) | Aynan shu uslub (Tailwind + CVA + forwardRef), lekin tashqi generatorga bog'liqlik yo'q; barcha komponentlar `aria-*` atributlari bilan |
| `next/font` o'rniga **CSS font stack** | Build vaqtida tashqi tarmoqqa bog'liqlik bo'lmasligi uchun (offline build ishlaydi). Inter/Manrope tizimda bo'lsa ishlatiladi, aks holda fallback |
| `ButtonLink` komponenti | `<button>` ichiga `<a>` joylashtirmaslik uchun (ichma-ich interaktiv elementlar a11y buzadi) |
| Super-admin uchun `data-theme="admin"` | FRONTEND_UX_UI 7: alohida "operatsion" quyuq tema — hech qanday komponentni dublikat qilmasdan, faqat CSS o'zgaruvchilari orqali |
| `useSearchParams` ishlatgan sahifalar `<Suspense>` bilan o'raldi | Next.js 15 talabi (CSR bailout) |
| Watch-progress har **12 sekundda** saqlanadi | FRONTEND_UX_UI 5.3 dagi "10-15 soniya debounce" talabi; `seek` qilish ko'rilgan vaqt sifatida hisoblanmaydi |

---

## 4. Hali qilinmagan (keyingi bosqichlar)

| Funksiya | Holat | Reja |
|---|---|---|
| Drag & drop bilan modul/dars tartibini o'zgartirish | Backend endpoint (`PUT .../reorder`) tayyor, frontend'da `dnd-kit` ulanmagan (hozircha qo'lda `order_index`) | Phase 1 oxiri |
| Dars ostida Q&A va izohlar | UI joyi tayyor (tablar), backend modeli yo'q | Phase 2 |
| Gamifikatsiya (streak, badge, XP) | Yo'q | Phase 2 |
| Referral / affiliate | Yo'q | Phase 2 |
| Live darslar (Jitsi) | Yo'q | Phase 2 |
| AI subtitr / quiz generatori | Yo'q | Phase 3 |
| PWA / offline video | Yo'q | Phase 3 |
| Parolni tiklash (email) | UI havolasi bor, SMTP oqimi yozilmagan | Phase 1 oxiri |
| OAuth (Google) | Model maydoni (`google_sub`) bor, oqim yo'q | Phase 2 |
| Ko'p tillilik (i18n) | Interfeys o'zbek tilida qattiq yozilgan; `locales` sozlamasi tayyor | Phase 3 |
| To'lovni qaytarish (refund) oqimi | `PaymentProvider.refund()` interfeysi bor, mock'da ishlaydi | Phase 2 |

---

## 4a. Kod uslubi: izohsiz kod

Loyiha talabiga ko'ra **barcha izohlar va docstring'lar kod fayllaridan olib tashlangan**
(`.py`, `.ts`, `.tsx`, `.css`, `.mjs` — jami 145 fayl).

Saqlab qolingan yagona istisno — bular izoh emas, **vosita direktivalari**; o'chirilsa
lint yoki build buziladi:

| Direktiva | Nechta | Nima uchun kerak |
|---|---|---|
| `# noqa: F401 / ASYNC110 / UP046` | 10 | `ruff check` o'tishi uchun (ataylab qilingan importlar va sikllar) |
| `# type: ignore[prop-decorator]` | 6 | pydantic `computed_field` + `property` uchun mypy |
| `# pragma: no cover` | 1 | `Base.__repr__` test qamrovidan chiqarilgan |
| `// eslint-disable-next-line react-hooks/exhaustive-deps` | 2 | `next lint` o'tishi uchun (ataylab cheklangan dependency ro'yxati) |

Tegilmagan fayllar (kod emas — konfiguratsiya va hujjat):
`.env.example`, `docker-compose*.yml`, `Dockerfile`, `alembic.ini`, `alembic/script.py.mako`,
`*.md`.

> Izohsiz kodda kontekst yo'qolmasligi uchun spetsifikatsiya bo'limlari bilan bog'lanish
> [docs/README.md](README.md) dagi "Spetsifikatsiya ↔ kod xaritasi" jadvalida saqlanadi.

## 5. Test qamrovi

Hozircha yozilgan:

* `tests/test_security.py` — parol hash, JWT yaratish/dekodlash, token turi tekshiruvi
* `tests/test_payment_adapters.py` — Payme Basic auth, Click MD5 imzo (to'g'ri/xato), webhook
  normallashtirish, mock provayder to'liq sikli

Keyingi qadam: DB bilan integratsiya testlari (checkout → webhook → enrollment → sertifikat
oqimi), `httpx.ASGITransport` orqali endpoint testlari.
