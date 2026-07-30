# Zehno.uz — Onlayn ta'lim marketplace platformasi

Maktablar, xususiy ustozlar va o'quv markazlariga o'z kurslarini (videodarslik, materiallar,
testlar) joylash va sotish imkonini beruvchi platforma. Talabalar kurs sotib oladi, videodarsliklarni
ko'radi, testlardan o'tadi va **QR kodli sertifikat** oladi. B2B mijozlar uchun **CRM integratsiyali**
alohida nazorat paneli mavjud.

> Loyiha `docs/` dagi spetsifikatsiyalar (`ARCHITECTURE.md`, `FRONTEND_UX_UI.md`,
> `ADDITIONAL_FEATURES.md`) asosida qurilgan. Texnologik farq: backend **FastAPI (Python)** —
> NestJS emas, JWT esa **python-jose** orqali.

---

## Texnologik stek

| Qatlam | Tanlov |
|---|---|
| Frontend | Next.js 15 (App Router, React 19, TypeScript), Tailwind CSS, TanStack Query, Recharts, hls.js |
| Backend | **FastAPI** + Pydantic v2, SQLAlchemy 2.0 (async), Alembic |
| Auth | **JWT (python-jose)** + argon2, refresh token rotatsiyasi (HttpOnly cookie) |
| Baza | PostgreSQL 16 |
| Cache / Queue | **Redis** + **Celery** (worker + beat) |
| Fayl saqlash | MinIO (S3-mos) |
| Konteynerlash | **Docker** + Docker Compose |
| Video | PeerTube (MVP) · Kinescope · Bunny Stream · mock — adapter orqali |
| To'lov | Payme · Click · mock (sandbox) — adapter orqali |
| CRM | Bitrix24 · EspoCRM · ichki mini-CRM — adapter orqali |
| Bildirishnoma | Telegram Bot API |

---

## Tez boshlash (Docker)

```bash
# 1. Muhit o'zgaruvchilari
cp .env.example .env          # Windows: copy .env.example .env

# 2. Hammasini ko'tarish
docker compose up -d --build

# 3. Loglarni kuzatish
docker compose logs -f api web
```

Birinchi ishga tushirishda `api` konteyneri quyidagilarni avtomatik bajaradi:

1. Postgres/Redis tayyor bo'lishini kutadi
2. **Boshlang'ich Alembic migratsiyasini generatsiya qiladi** (`alembic/versions/` bo'sh bo'lsa) va qo'llaydi
3. MinIO bucket'ini yaratadi
4. Seed qiladi: kategoriyalar, tizim sozlamalari, super-admin, demo kurslar

| Xizmat | Manzil |
|---|---|
| Web (Next.js) | http://localhost:3000 |
| API (Swagger) | http://localhost:8000/docs |
| API healthcheck | http://localhost:8000/health |
| MinIO konsoli | http://localhost:9001 |

### Demo hisoblar (seed)

| Rol | Email | Parol |
|---|---|---|
| Super admin | `admin@zehno.uz` | `Admin12345!` |
| Ustoz / o'quv markaz | `ustoz@zehno.uz` | `Ustoz12345!` |
| Talaba | `talaba@zehno.uz` | `Talaba12345!` |
| B2B menejer | `hr@demotech.uz` | `Manager12345!` |

> Production'da `.env` dagi `JWT_SECRET_KEY` va `FIRST_SUPERADMIN_PASSWORD` ni **albatta** almashtiring.

---

## Lokal ishlab chiqish (Docker'siz)

### Backend

```bash
cd apps/api
py -m venv .venv && .venv\Scripts\activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt

# Postgres va Redis kerak (docker compose up -d postgres redis minio)
python -m app.cli migrate
python -m app.cli seed
uvicorn app.main:app --reload

# Celery (alohida terminalda)
celery -A app.worker.celery_app.celery_app worker --loglevel=INFO
celery -A app.worker.celery_app.celery_app beat  --loglevel=INFO

# Telegram bot workeri
python -m app.bot.main
```

### Frontend

```bash
cd apps/web
npm install
npm run dev          # http://localhost:3000
npm run typecheck
npm run build
```

### Sifat tekshiruvlari

```bash
# Backend
cd apps/api && ruff check app && ruff format --check app && pytest

# Frontend
cd apps/web && npm run typecheck && npm run lint && npm run build
```

---

## Sirlarni himoyalash (majburiy qadam)

Repozitoriyani klonlagach **bir marta** bajaring — bu pre-commit tekshiruvini yoqadi:

```bash
git config core.hooksPath .githooks
```

Shundan keyin `.env`, `*.pem`, SSH kalitlari va matn ichidagi tokenlar (Telegram,
Bitrix24, AWS, GitHub, JWT, private key) commit qilinmaydi — hook commitni to'xtatadi.

```bash
./scripts/scan-secrets.sh            # barcha kuzatilayotgan fayllar
./scripts/scan-secrets.sh --staged   # commitga tayyorlanganlar
./scripts/scan-secrets.sh --history  # git tarixi (push qilinganlar)
```

Qoidalar:

- **Barcha kalitlar faqat `.env` da** — u `.gitignore` da, hech qachon commit qilinmaydi
- `.env.example` da faqat bo'sh yoki `change-me...` kabi namuna qiymatlar
- Kalit tasodifan commit qilinsa — uni olib tashlash **yetarli emas**, provayderda
  albatta almashtiring (u allaqachon oshkor bo'lgan)
- Xato aniqlash (false positive) bo'lsa: `ALLOW_SECRET=1 git commit ...`

## Loyiha strukturasi

```
zehno/
├── apps/
│   ├── api/                        # FastAPI (modulli monolit)
│   │   ├── app/
│   │   │   ├── core/               # config, security (JWT/argon2), deps (RBAC), rate limit
│   │   │   ├── db/                 # engine (async + sync), Base, seed
│   │   │   ├── models/             # SQLAlchemy modellari (17 jadval)
│   │   │   ├── modules/            # domen modullari
│   │   │   │   ├── auth/           #   ro'yxatdan o'tish, login, refresh rotatsiyasi
│   │   │   │   ├── users/          #   foydalanuvchilarni boshqarish (admin)
│   │   │   │   ├── organizations/  #   maktab/markaz/B2B mijoz
│   │   │   │   ├── courses/        #   katalog + CMS + moderatsiya
│   │   │   │   ├── media/          #   video yuklash, signed playback, fayllar
│   │   │   │   ├── commerce/       #   savat, checkout, webhook, kupon, payout
│   │   │   │   ├── progress/       #   watch-progress, quiz
│   │   │   │   ├── certificates/   #   PDF + QR + ochiq tekshiruv
│   │   │   │   ├── b2b/            #   bulk enroll, xodimlar, hisobot, CRM
│   │   │   │   └── admin/          #   KPI, integratsiya monitoringi, sozlamalar
│   │   │   ├── integrations/       # ADAPTER PATTERN
│   │   │   │   ├── video/          #   base + mock/peertube/kinescope/bunny
│   │   │   │   ├── payment/        #   base + mock/payme/click
│   │   │   │   ├── crm/            #   base + mock/bitrix24/espocrm
│   │   │   │   ├── notification/   #   base + telegram
│   │   │   │   ├── storage/        #   S3/MinIO
│   │   │   │   └── factory.py      #   .env bo'yicha provayder tanlash
│   │   │   ├── worker/             # Celery app + tasks (sertifikat, CRM, bot, video, xizmat)
│   │   │   ├── bot/                # Telegram bot workeri (long-polling)
│   │   │   ├── api/v1/router.py    # barcha routerlar yig'indisi
│   │   │   ├── cli.py              # wait-for-services / migrate / seed / reset-db
│   │   │   └── main.py             # FastAPI ilovasi
│   │   ├── alembic/                # migratsiyalar
│   │   └── tests/
│   └── web/                        # Next.js
│       ├── app/
│       │   ├── (marketing)/        # landing, katalog, kurs sahifasi, savat, sertifikat
│       │   ├── (auth)/             # login, register
│       │   ├── (student)/          # dashboard, Course Player, profil
│       │   ├── (teacher)/          # kurslarim, wizard, daromad, kuponlar, sozlamalar
│       │   ├── (b2b)/              # dashboard, xodimlar, bulk enroll, CRM
│       │   └── (super-admin)/      # KPI, moderatsiya, foydalanuvchilar, moliya, integratsiyalar
│       ├── components/             # ui/, layout/, course/, player/
│       └── lib/                    # api-client (401 → refresh), types, utils, hooks
├── docs/                           # spetsifikatsiyalar va qo'shimcha hujjatlar
├── docker-compose.yml              # postgres, redis, minio, api, worker, beat, bot, web
├── docker-compose.peertube.yml     # PeerTube (alohida ishga tushiriladi)
└── .env.example
```

---

## Asosiy oqimlar

### 1. Kurs yaratishdan sotuvgacha

```
Ustoz: wizard (umumiy → dastur → video → narx)  →  status: draft
   ↓ "Moderatsiyaga yuborish"  (validatsiya: modul/dars/tavsif/muqova/video bor)
status: pending  →  Super-admin: tasdiqlash / rad etish (+ izoh)
   ↓
status: published  →  katalogda ko'rinadi
```

### 2. Sotib olishdan sertifikatgacha

```
Savat → /cart/checkout → PaymentProvider.create_invoice() → Payme/Click sahifasi
   ↓ webhook (imzo tekshiriladi)
Order: paid → Enrollment ochiladi → Telegram xabar + CRM sync (Celery)
   ↓ dars ko'rish (signed video URL, 10-15 daqiqa)
Progress har 12 sekundda saqlanadi → 100% + testlar o'tilgan
   ↓ Celery: CERTIFICATE_ISSUE
PDF (fpdf2) + QR → MinIO → /certificates/{kod}/verify (ochiq)
```

### 3. B2B nazorat

```
CSV yuklash → bulk enroll (seat cheklovi bilan) → xodim hisoblari ochiladi
   ↓ xodim o'qiydi
progress 25/50/75/100% → Celery → CrmProvider.push_progress()
   ↓
Bitrix24/EspoCRM Contact timeline'ida progress ko'rinadi
```

---

## Provayderni almashtirish (adapter pattern)

Biznes-logikaga tegmasdan faqat `.env` o'zgaradi:

```bash
VIDEO_PROVIDER=mock          # mock | peertube | kinescope | bunny
PAYMENT_PROVIDER=mock        # mock | payme | click
CRM_PROVIDER=mock            # mock | bitrix24 | espocrm
TELEGRAM_ENABLED=false
```

**MVP uchun bepul to'plam:** `peertube` + `bitrix24` + MinIO + Telegram.
**Sozlamasiz sinash uchun:** `mock` (video S3'ga yuklanadi, to'lov `/checkout/mock` sahifasida
tasdiqlanadi) — Payme/Click merchant kalitlari kerak bo'lmaydi.

PeerTube'ni ko'tarish:

```bash
docker compose -f docker-compose.peertube.yml up -d
docker compose -f docker-compose.peertube.yml logs peertube | grep -i password
# .env: VIDEO_PROVIDER=peertube, PEERTUBE_BASE_URL=http://localhost:9010, login/parol
```

Yangi provayder qo'shish tartibi (`ARCHITECTURE.md` qoidasi): **avval interfeys, keyin
implementatsiya** — `integrations/<kind>/base.py` dagi abstrakt klassni meros qilib olib,
`factory.py` dagi lug'atga qo'shiladi.

---

## API xulosasi

To'liq interaktiv hujjat: **http://localhost:8000/docs**

```
POST   /api/v1/auth/register | login | refresh | logout
GET    /api/v1/auth/me                     PATCH /api/v1/auth/me
GET    /api/v1/courses                     # katalog: qidiruv, filtr, saralash
GET    /api/v1/courses/{slug}
POST   /api/v1/teacher/courses             # CMS: kurs/modul/dars CRUD + reorder
POST   /api/v1/lessons/{id}/video          # video yuklash (provayderga proxy)
GET    /api/v1/lessons/{id}/playback       # signed URL (faqat sotib olganlarga)
POST   /api/v1/cart/checkout
POST   /api/v1/payments/webhook/{payme|click|mock}
GET    /api/v1/learn/{course_id}           # Course Player ma'lumoti
POST   /api/v1/enrollments/{id}/progress
POST   /api/v1/lessons/{id}/quiz/submit
GET    /api/v1/certificates/{code}/verify  # ochiq
POST   /api/v1/b2b/bulk-enroll             GET /api/v1/b2b/dashboard
GET    /api/v1/admin/dashboard             # platforma KPI
GET    /api/v1/admin/integrations          # monitoring
POST   /api/v1/admin/moderation/{id}/approve | reject
```

---

## Xavfsizlik

- Parollar **argon2id** bilan hash qilinadi (bcrypt fallback)
- Access token 15 daqiqa, refresh token DB'da **SHA-256 hash** ko'rinishida + **rotatsiya** va
  qayta ishlatish (reuse) aniqlanganda barcha sessiyalar yopiladi
- Refresh token **HttpOnly cookie**'da; mobil ilova uchun body orqali ham qabul qilinadi
- Video playback URL vaqtinchalik (10-15 daqiqa) — havola tarqatilishining oldini oladi
- To'lov webhooklari **imzo/auth** orqali tekshiriladi (Payme Basic auth, Click MD5 `sign_string`)
- Rate limiting (slowapi + Redis): login/register uchun qattiqroq
- Fayl yuklashda MIME-type va hajm cheklovlari (video 2 GB, fayl 50 MB)
- RBAC + resource-level ownership (`course.owner_id == user.id`)

---

## Keyingi bosqichlar

`docs/ADDITIONAL_FEATURES.md` bo'yicha ustuvorlik:

1. **Phase 2** — gamifikatsiya (streak, badge), referral, live darslar (Jitsi), Q&A
2. **Phase 3** — AI subtitr/quiz generatori, tavsiya tizimi, PWA/offline
3. **Phase 4** — SCORM/xAPI, blockchain sertifikat, white-label subdomain

Allaqachon qo'yilgan asos: sharh/reyting tizimi, kupon/chegirma, feature flaglar
(`/super-admin/settings`), audit log, integratsiya monitoringi.

---

## Foydali buyruqlar

```bash
# Migratsiya yaratish (model o'zgargandan keyin)
docker compose exec api alembic revision --autogenerate -m "add xyz"
docker compose exec api alembic upgrade head

# Testlar
docker compose exec api pytest -v

# Bazani tozalash (DIQQAT: barcha ma'lumot o'chadi)
docker compose exec api python -m app.cli reset-db
docker compose exec api python -m app.cli migrate
docker compose exec api python -m app.cli seed

# Celery navbatini kuzatish
docker compose logs -f worker beat
```
