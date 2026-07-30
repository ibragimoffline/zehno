# Tekshiruv va testlash

## 1. Avtomatlashtirilgan testlar

```bash
docker compose exec api pytest -v          # 14 ta test
docker compose exec api ruff check app     # lint
cd apps/web && npm run typecheck && npm run lint && npm run build
```

| Fayl | Nimani tekshiradi |
|---|---|
| `tests/test_security.py` | argon2 hash/verify, JWT yaratish va dekodlash, token turi (access/refresh) ajratilishi, `hash_token` determinizmi, kod generatsiyasida chalkash belgilar yo'qligi |
| `tests/test_payment_adapters.py` | Click MD5 imzosi (to'g'ri/xato), Prepare/Complete oqimi, Payme Basic auth va tiyinga o'tkazish, mock provayder to'liq sikli |

## 2. Qo'lda E2E tekshiruv (bajarilgan)

Quyidagi oqimlar to'liq stack (Docker) ustida tekshirilgan va ishlagan:

### Auth va RBAC
- login → JWT → `/auth/me`
- `student` → `/admin/*`, `/teacher/*`, `/b2b/*` = **403**
- `teacher` → `/admin/*` = **403**, `/teacher/courses` = **200**
- tokensiz → `/auth/me` = **401**, `/courses` va `/certificates/{kod}/verify` = **200** (ochiq)

### Katalog
- `/categories` — 8 kategoriya, har birida kurslar soni
- `/courses` — filtr (`is_free`, `category`, `level`), saralash, sahifalash
- `/courses/{slug}` — modullar + darslar daraxti bilan

### Commerce
- **Bepul kurs**: `/cart/checkout` → order darhol `paid` → enrollment ochildi
- **Pullik kurs**: savatga qo'shish → checkout (`mock`) → `checkout_url` → `/payments/webhook/mock` → enrollment ochildi
- Komissiya hisobi: 600 000 so'm sotuvdan → ustozga 510 000, platformaga 90 000 (15%)

### O'quv jarayoni
- `/learn/{course_id}` — Course Player ma'lumoti (modullar, darslar, progress)
- Har bir dars uchun `/enrollments/{id}/progress` → 20% → 40% → 60% → 80% → **100%**
- 100% da `course_completed=true` va `certificate_issued=true`

### Quiz
- To'g'ri javoblar talabaga **yuborilmaydi** (tekshirilgan)
- Noto'g'ri javoblar → 0%, `passed=false`
- To'g'ri javoblar → 100%, `passed=true`, urinishlar soni hisoblanadi

### Sertifikat
- Celery worker `issue_certificate` task'ini bajardi
- PDF generatsiya qilindi (5.5 KB, `%PDF-1.3`) va MinIO'ga saqlandi
- `/certificates/{kod}/verify` → `valid=true`, talaba/kurs/ustoz nomi bilan
- Frontend `/certificates/{kod}` sahifasi SSR orqali to'g'ri ko'rsatdi

### Ustoz paneli
- Kurslar ro'yxati, daromad (yalpi/sof/komissiya), talabalar
- Kurs yaratish → modul → dars → moderatsiyaga yuborish
- Moderatsiya validatsiyasi ishladi: *"Kurs tavsifi to'ldirilishi kerak"*

### B2B
- Dashboard: xodimlar, o'rinlar (seat), CRM holati
- Bulk enroll: 2 email → 2 yangi hisob + 2 enrollment, seat hisobi to'g'ri

### Super-admin
- KPI: daromad, komissiya, konversiya, foydalanuvchi/kurs/enrollment/sertifikat sonlari
- Integratsiya monitoringi: 5 ta adapter holati (`ok` / `disabled`)
- Moderatsiya navbati, foydalanuvchilar, buyurtmalar ro'yxati

### Frontend
17 ta route tekshirildi — barchasi **200**, mavjud bo'lmagan manzil **404**.
Landing, kurs sahifasi va sertifikat sahifasi SSR orqali backend ma'lumotini render qildi.

## 3. Tekshiruv paytida topilgan va tuzatilgan xatolar

| Muammo | Sabab | Yechim |
|---|---|---|
| Migratsiya `relation "users" does not exist` bilan tushdi | `users ↔ organizations` aylanaviy FK — Alembic jadval tartibini aniqlay olmadi | `organizations.owner_id` FK'ga `use_alter=True` |
| `/auth/login` body'ni query parametr deb qabul qildi | `slowapi` dekoratori FastAPI signaturasini o'raydi | Rate limiting Redis asosidagi **dependency** ga o'tkazildi, `slowapi` olib tashlandi |
| `request: Request` query parametr deb qaraldi | `from __future__ import annotations` + klass-dependency: FastAPI callable obyektda `__globals__` topa olmaydi | `core/rate_limit.py` dan `__future__` importi olib tashlandi |
| Progress saqlashda `TypeError: '>' not supported between int and NoneType` | Ustun `default=0` faqat INSERT paytida qo'llanadi — yangi obyektda qiymat `None` | Obyekt yaratishda Python tomonida default berildi + `or 0` himoyasi |
| `integration_statuses` da `duplicate key (provider)=(mock)` | `mock` nomi video/to'lov/CRM uchun bir vaqtda ishlatiladi, `provider` esa unikal edi | Unikal kalit `(kind, provider)` juftligiga o'zgartirildi |
| Pydantic v2: `RegisterRequest._strong_password(value)` chaqirig'i ishlamaydi | `field_validator` atributni `PydanticDescriptorProxy` ga aylantiradi | Tekshiruv modul darajasidagi `validate_password_strength()` funksiyasiga ajratildi |

## 4. Keyingi test bosqichlari

- [ ] Endpoint testlari (`httpx.ASGITransport` + test DB): auth, katalog, checkout
- [ ] Integratsiya testi: checkout → webhook → enrollment → sertifikat (bitta oqimda)
- [ ] Frontend: Playwright bilan smoke testlar (login → kurs sotib olish → dars ko'rish)
- [ ] Yuklama testi: katalog qidiruvi va `/learn` endpointi (k6 yoki locust)
