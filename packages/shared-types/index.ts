/**
 * Umumiy tiplar.
 *
 * Hozircha barcha API tiplari `apps/web/lib/types.ts` da saqlanadi. Mobil ilova
 * (React Native) yoki ikkinchi client qo'shilganda ular shu paketga ko'chiriladi
 * va `apps/web` dan re-export qilinadi.
 *
 * Manba: apps/api dagi Pydantic sxemalari (`app/modules/<name>/schemas.py`).
 */

/** Barcha ro'yxat endpointlari qaytaradigan sahifalash konverti. */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

/** Backend xato javobining yagona formati. */
export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
