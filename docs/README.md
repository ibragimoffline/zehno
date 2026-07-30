# Hujjatlar

| Fayl | Mazmuni |
|---|---|
| [STACK_DECISIONS.md](STACK_DECISIONS.md) | Texnologik qarorlar, spetsifikatsiyadan farqlar, hali qilinmagan ishlar ro'yxati |
| `ARCHITECTURE.md` | **Boshlang'ich spetsifikatsiya** — arxitektura, DB sxemasi, integratsiyalar strategiyasi, implementatsiya rejasi |
| `FRONTEND_UX_UI.md` | **Boshlang'ich spetsifikatsiya** — dizayn tizimi, sahifalar wireframe'lari, komponent tavsiyalari |
| `ADDITIONAL_FEATURES.md` | **Boshlang'ich spetsifikatsiya** — Phase 2-4 uchun qo'shimcha funksiyalar va ustuvorlik |

> Uchta spetsifikatsiya fayli loyiha boshlanishida tashqi hujjat sifatida berilgan.
> Ularni shu papkaga ko'chirib qo'ying.
>
> Kod izohsiz yozilgan (loyiha talabi) — spetsifikatsiya bo'limlari bilan bog'lanish
> quyidagi jadval orqali ta'minlanadi.

## Spetsifikatsiya ↔ kod xaritasi

| Spetsifikatsiya bo'limi | Implementatsiya |
|---|---|
| ARCHITECTURE 2 (RBAC) | `apps/api/app/core/deps.py` (`require_roles`), `app/models/enums.py` |
| ARCHITECTURE 4 (modulli monolit) | `apps/api/app/modules/*` |
| ARCHITECTURE 6 (adapter pattern) | `apps/api/app/integrations/*` + `factory.py` |
| ARCHITECTURE 6.1 (video) | `integrations/video/{base,mock,peertube,kinescope,bunny}.py` |
| ARCHITECTURE 6.2 (CRM) | `integrations/crm/*` + `worker/tasks/crm.py` |
| ARCHITECTURE 6.3 (to'lov) | `integrations/payment/{payme,click,mock}.py` |
| ARCHITECTURE 6.4 (Telegram) | `integrations/notification/telegram.py` + `app/bot/main.py` |
| ARCHITECTURE 7 (DB sxemasi) | `apps/api/app/models/*.py` |
| ARCHITECTURE 8 (API) | `apps/api/app/api/v1/router.py` |
| ARCHITECTURE 9 (sertifikat) | `modules/certificates/service.py` + `worker/tasks/certificates.py` |
| ARCHITECTURE 10 (xavfsizlik) | `core/security.py`, `core/rate_limit.py`, `modules/media/router.py` |
| FRONTEND_UX_UI 1 (dizayn tizimi) | `apps/web/tailwind.config.ts` + `app/globals.css` |
| FRONTEND_UX_UI 3 (landing) | `apps/web/app/(marketing)/page.tsx` |
| FRONTEND_UX_UI 4 (katalog/kurs) | `app/(marketing)/courses/` |
| FRONTEND_UX_UI 5 (Course Player) | `app/(student)/learn/[courseId]/` + `components/player/` |
| FRONTEND_UX_UI 6 (ustoz paneli) | `app/(teacher)/teacher/` |
| FRONTEND_UX_UI 7 (super-admin) | `app/(super-admin)/super-admin/` (`data-theme="admin"`) |
| FRONTEND_UX_UI 8 (B2B) | `app/(b2b)/b2b/` |
| FRONTEND_UX_UI 9 (a11y) | `components/ui/input.tsx` (`Field`), `components/player/video-player.tsx` (klaviatura) |
| ADDITIONAL_FEATURES 3.3 (kupon) | `modules/commerce/` (`Coupon`, `/teacher/coupons`) |
| ADDITIONAL_FEATURES 5 (feature flags, audit) | `models/system.py` + `/super-admin/settings`, `/super-admin/logs` |
