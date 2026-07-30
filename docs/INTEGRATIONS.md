# Integratsiyalarni ulash qo'llanmasi

Har bir tashqi xizmat adapter orqali ulanadi — kodga tegilmaydi, faqat `.env` o'zgaradi.
Provayder almashtirilgach API konteynerini qayta ishga tushirish kerak:

```bash
docker compose restart api worker beat
```

Holatni tekshirish: **Super-admin → Integratsiyalar** (`/super-admin/integrations`) yoki
`GET /api/v1/admin/integrations`.

---

## 1. Video — PeerTube (bepul, self-hosted)

MVP uchun asosiy tanlov. Kalit sotib olish shart emas, lekin alohida server resursi kerak
(transkodlash CPU talab qiladi).

### Ishga tushirish

```bash
# 1. Asosiy stack ko'tarilgan bo'lishi kerak (tarmoq shu yerda yaratiladi)
docker compose up -d

# 2. PeerTube
docker compose -f docker-compose.peertube.yml up -d

# 3. Dastlabki admin parolini loglardan olish
docker compose -f docker-compose.peertube.yml logs peertube | grep -i "User password"
```

Panel: http://localhost:9010 (`root` / loglardan olingan parol).

### Kanal yaratish

PeerTube'da video kanalga yuklanadi. Admin sifatida kirib **My channels → Create channel**
qiling yoki adapter avtomatik ravishda foydalanuvchining birinchi kanalini topadi
(`PEERTUBE_CHANNEL_ID` bo'sh qoldirilsa).

### `.env`

```bash
VIDEO_PROVIDER=peertube
PEERTUBE_BASE_URL=http://peertube:9000      # konteynerlar orasidagi manzil
PEERTUBE_PUBLIC_URL=http://localhost:9010   # PeerTube o'zini shu manzil deb biladi
PEERTUBE_USERNAME=root
PEERTUBE_PASSWORD=<loglardan olingan parol>
PEERTUBE_CHANNEL_ID=                        # bo'sh = birinchi kanal
```

> **Nega ikkita URL kerak?** PeerTube kiruvchi so'rovdagi `Host` sarlavhasini o'z
> sozlamasi bilan solishtiradi va mos kelmasa **403** qaytaradi
> (`Getting client tokens for host peertube:9000 is forbidden`). Adapter shuning uchun
> ichki manzilga so'rov yuborayotganda `Host: localhost:9010` sarlavhasini qo'shadi.
> Brauzerga qaytariladigan playback havolalari esa `PEERTUBE_PUBLIC_URL` asosida bo'ladi.

Production'da ikkalasi bir xil domen bo'ladi (`https://video.zehno.uz`) va bu sarlavha
avtomatik ravishda qo'shilmaydi.

### Tarmoq

PeerTube alohida compose loyihasida ishlaydi, shuning uchun u asosiy stack tarmog'iga
(`zehno_default`) ham ulanadi — `api` konteyneri `http://peertube:9000` orqali murojaat
qila oladi. Ya'ni **avval `docker compose up -d`**, keyin PeerTube ko'tariladi.

### Qanday ishlaydi

1. Ustoz video yuklaydi → `POST /api/v1/lessons/{id}/video`
2. Adapter PeerTube'ga **`privacy=private`** bilan yuklaydi
3. Celery `poll_video_status` transkodlash tugashini kuzatadi (30 sek interval)
4. Talaba darsni ochganda → `POST /api/v1/videos/{id}/token` orqali **10 daqiqalik**
   `videoFileToken` olinadi va HLS manifest havolasiga qo'shiladi

Production'da PeerTube uchun alohida VPS tavsiya etiladi.

### Tekshirilgan natija

Ushbu oqim lokal stack'da to'liq sinovdan o'tgan (PeerTube 7.3.0):

| Qadam | Natija |
|---|---|
| `api` → PeerTube ulanishi | ✅ `/api/v1/config` 200 |
| Parol grant orqali token olish | ✅ `access_token` |
| Kanalni avtomatik aniqlash | ✅ `Main root channel` (id=1) |
| Video yuklash (188 KB mp4) | ✅ `uuid` qaytdi, `status=processing` |
| Celery `poll_video_status` | ✅ `ready` ga o'tdi |
| Signed HLS manifest | ✅ 200, `#EXTM3U` |
| Tokensiz o'sha havola | ✅ **403** — himoya ishlayapti |
| Preview darsi, mehmon | ✅ 200 (bepul ko'rish) |
| Preview emas, mehmon | ✅ 403 «Videoni ko'rish uchun tizimga kiring» |
| Preview emas, sotib olmagan | ✅ 403 «Bu kursni sotib olmagansiz» |
| Preview emas, sotib olgan | ✅ 200, signed URL |

---

## 2. Video — Kinescope / Bunny Stream (pullik alternativa)

### Kinescope — tekshirilgan

Token olingach `PROJECT_ID` ni API'dan olish mumkin:

```bash
curl -s https://api.kinescope.io/v1/projects \
  -H "Authorization: Bearer <KINESCOPE_API_KEY>" | jq '.data[] | {id, name}'
```

Sinov natijasi (real token bilan):

| Qadam | Natija |
|---|---|
| `/v1/projects` | ✅ 200, loyiha topildi |
| Video yuklash (188 KB) | ✅ `uuid`, `status=processing` |
| Transkodlash | ✅ `ready` |
| HLS master playlist | ✅ 200 (`kinescope.io/<id>/master.m3u8`) |
| Thumbnail | ✅ CDN havolasi |
| Embed kod | ✅ `iframe` |

```bash
# Kinescope
VIDEO_PROVIDER=kinescope
KINESCOPE_API_KEY=...          # kinescope.io → Settings → API
KINESCOPE_PROJECT_ID=...       # yuqoridagi curl orqali

# Bunny Stream
VIDEO_PROVIDER=bunny
BUNNY_STREAM_LIBRARY_ID=...    # bunny.net → Stream → Library
BUNNY_STREAM_API_KEY=...
BUNNY_STREAM_CDN_HOSTNAME=vz-xxxx.b-cdn.net
BUNNY_STREAM_TOKEN_KEY=...     # Token Authentication kaliti (ixtiyoriy)
```

---

## 3. To'lov — Payme

### Kalitlarni olish

1. https://business.paycom.uz da merchant sifatida ro'yxatdan o'ting
2. Kassa yarating → **Kassa sozlamalari** dan `MERCHANT_ID` va `KEY` (test/production alohida)
3. **Endpoint URL** maydoniga webhook manzilini yozing:

```
https://<sizning-domeningiz>/api/v1/payments/webhook/payme
```

### `.env`

```bash
PAYMENT_PROVIDER=payme
PAYMENT_SANDBOX=true                        # production'da false
PAYME_MERCHANT_ID=...
PAYME_MERCHANT_KEY=...
PAYME_CHECKOUT_URL=https://checkout.paycom.uz
```

### Muhim

- Payme **JSON-RPC** protokoli: `CheckPerformTransaction` → `CreateTransaction` →
  `PerformTransaction`. Barchasi bitta webhook endpointiga keladi.
- Avtorizatsiya: `Authorization: Basic base64("Paycom:<KEY>")` — adapter tekshiradi,
  noto'g'ri bo'lsa `-32504` qaytaradi.
- Summalar **tiyin**da (1 so'm = 100 tiyin) — konvertatsiya adapterda.
- Lokal test uchun webhook'ni ochish: `ngrok http 8000`.

---

## 4. To'lov — Click

### Kalitlarni olish

1. https://merchant.click.uz da ro'yxatdan o'ting
2. Servis yarating → `SERVICE_ID`, `MERCHANT_ID`, `SECRET_KEY`, `MERCHANT_USER_ID`
3. **Prepare URL** va **Complete URL** maydonlariga bir xil manzilni yozing:

```
https://<sizning-domeningiz>/api/v1/payments/webhook/click
```

### `.env`

```bash
PAYMENT_PROVIDER=click
CLICK_MERCHANT_ID=...
CLICK_SERVICE_ID=...
CLICK_SECRET_KEY=...
CLICK_MERCHANT_USER_ID=...
CLICK_CHECKOUT_URL=https://my.click.uz/services/pay
```

### Muhim

- Ikki bosqich: `action=0` (Prepare) → `action=1` (Complete).
- Imzo MD5: `click_trans_id + service_id + SECRET_KEY + merchant_trans_id
  [+ merchant_prepare_id] + amount + action + sign_time`.
- Adapter imzoni tekshiradi; xato bo'lsa `error=-1 (SIGN CHECK FAILED)`.

---

## 5. CRM — Bitrix24 (bepul tarif)

### Webhook olish

1. Bitrix24 portalingizda: **Ilovalar → Ishlab chiquvchilar → Boshqa → Kiruvchi webhook**
2. **Ruxsatlar (scope) — eng muhim qadam:** `crm` katagini belgilang
3. Hosil bo'lgan URL: `https://<portal>.bitrix24.ru/rest/1/<token>/`

> ⚠️ **`crm` ruxsati belgilanmasa** webhook faqat `profile` va `scope` metodlarini ochadi —
> kompaniya/kontakt yaratishga urinilganda Bitrix24 `401 insufficient_scope` qaytaradi.
> Tekshirish:
>
> ```bash
> curl -s "<WEBHOOK_URL>scope.json"
> # {"result":[""]}      → ruxsat yo'q, webhookni tahrirlang
> # {"result":["crm"]}   → to'g'ri
> ```
>
> Adapter bu holatni aniqlab, B2B panelidagi CRM loglariga tushunarli xabar yozadi:
> *«webhook tokenida yetarli ruxsat yo'q… `crm` ruxsatini belgilang»*.

### `.env`

```bash
CRM_PROVIDER=bitrix24
BITRIX24_WEBHOOK_URL=https://<portal>.bitrix24.ru/rest/1/<token>/
```

### Tashkilot darajasida yoqish

CRM sinxroni **har bir tashkilot uchun alohida** yoqiladi:

```
PATCH /api/v1/organizations/{id}/crm
{ "crm_sync_enabled": true, "crm_provider": "bitrix24" }
```

yoki B2B panel → CRM sinxron bo'limidan.

### Nima yuboriladi

| Hodisa | CRM'da |
|---|---|
| Yangi enrollment | Company + Contact yaratiladi/yangilanadi |
| Progress 25 / 50 / 75 / 100% | Contact timeline'ga izoh |
| Sertifikat berilishi | Timeline izohiga sertifikat kodi |

Loglar: B2B panel → CRM sinxron, yoki `crm_sync_log` jadvali.

---

## 6. CRM — EspoCRM (self-hosted, cheklovsiz)

```bash
CRM_PROVIDER=espocrm
ESPOCRM_BASE_URL=https://crm.example.uz
ESPOCRM_API_KEY=...    # Administration → API Users → yangi user → API Key
```

---

## 7. Telegram bot (bepul)

### Token olish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` → bot nomi va username kiriting
3. Qaytgan tokenni nusxalang: `123456789:AAH...`

### `.env`

```bash
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456789:AAH...
TELEGRAM_BOT_USERNAME=zehno_uz_bot     # @ belgisisiz
```

Keyin: `docker compose restart telegram-bot worker`

### Foydalanuvchi qanday ulanadi

1. Profil → Telegram → **Ulanish kodini olish** (`POST /api/v1/auth/telegram/link-code`)
2. Botda `/start KOD` yuboriladi
3. `telegram_chat_id` saqlanadi — endi barcha xabarlar shu chatga keladi

### Qanday xabarlar boradi

| Shablon | Qachon |
|---|---|
| `payment_success` | To'lov tasdiqlangach |
| `certificate_ready` | Sertifikat generatsiya qilingach |
| `course_moderated` | Kurs tasdiqlangan/rad etilgan (ustozga) |
| `learning_reminder` | Har kuni 19:00 — 3 kundan beri faolsiz talabalarga |
| `weekly_b2b_report` | Har dushanba 09:00 — B2B menejerlarga |

Bot buyruqlari: `/start`, `/progress`, `/stop`, `/help`.

---

## 8. Fayl saqlash — MinIO / S3

Standart holatda MinIO Docker Compose ichida ishlaydi. Bulutga o'tish uchun:

```bash
# Cloudflare R2
S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
S3_PUBLIC_ENDPOINT_URL=https://cdn.zehno.uz
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET=zehno
S3_USE_SSL=true
```

`S3_PUBLIC_ENDPOINT_URL` — brauzer ko'radigan manzil (sertifikat PDF havolalari shu asosda).

---

## Tekshirish tartibi

```bash
# 1. Provayderlar to'g'ri yuklanganmi
curl -s http://localhost:8000/health | jq .providers

# 2. Har birini healthcheck qilish (super-admin tokeni bilan)
curl -s -X POST http://localhost:8000/api/v1/admin/integrations/healthcheck \
  -H "Authorization: Bearer <ADMIN_TOKEN>" | jq

# 3. Panelda ko'rish
open http://localhost:3000/super-admin/integrations
```

Healthcheck har 10 daqiqada Celery beat orqali avtomatik ishlaydi va natija
`integration_statuses` jadvaliga yoziladi.
