
export type UserRole = "student" | "teacher" | "org_admin" | "b2b_manager" | "admin";
export type CourseStatus = "draft" | "pending" | "published" | "rejected" | "archived";
export type CourseLevel = "beginner" | "intermediate" | "advanced";
export type CourseLanguage = "uz" | "ru" | "en";
export type LessonContentType = "video" | "pdf" | "quiz" | "text";
export type VideoAssetStatus = "pending_upload" | "processing" | "ready" | "failed";
export type EnrollmentStatus = "active" | "completed" | "expired" | "cancelled";
export type EnrollmentSource = "individual" | "b2b_bulk" | "manual" | "free";
export type OrderStatus = "pending" | "paid" | "failed" | "cancelled" | "refunded";
export type PaymentStatus = "pending" | "paid" | "failed" | "refunded" | "cancelled";
export type IntegrationHealth = "ok" | "degraded" | "error" | "disabled";
export type IntegrationKind = "video" | "payment" | "crm" | "notification" | "storage";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ApiMessage {
  message: string;
  ok: boolean;
}

export interface User {
  id: string;
  full_name: string;
  email: string;
  phone?: string | null;
  role: UserRole;
  organization_id?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  locale: string;
  is_active: boolean;
  telegram_chat_id?: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
  expires_at: string;
  expires_in: number;
}

export interface AuthResponse {
  user: User;
  tokens: TokenPair;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  icon?: string | null;
  description?: string | null;
  order_index: number;
  courses_count: number;
}

export interface CourseOwner {
  id: string;
  full_name: string;
  avatar_url?: string | null;
  bio?: string | null;
}

export interface CourseCard {
  id: string;
  title: string;
  slug: string;
  subtitle?: string | null;
  cover_url?: string | null;
  price: string;
  discount_price?: string | null;
  currency: string;
  level: CourseLevel;
  language: CourseLanguage;
  rating_avg: number;
  rating_count: number;
  students_count: number;
  lessons_count: number;
  duration_seconds: number;
  is_bestseller: boolean;
  is_featured: boolean;
  owner?: CourseOwner | null;
  category?: Category | null;
  is_enrolled: boolean;
}

export interface LessonPublic {
  id: string;
  title: string;
  description?: string | null;
  content_type: LessonContentType;
  order_index: number;
  duration_seconds: number;
  is_preview: boolean;
  has_video: boolean;
  has_quiz: boolean;
}

export interface LessonDetail extends LessonPublic {
  text_content?: string | null;
  attachments?: Array<Record<string, unknown>> | null;
  video?: { id: string; provider: string; status: VideoAssetStatus; thumbnail_url?: string | null } | null;
  completed: boolean;
  watch_seconds: number;
  last_position_seconds: number;
  is_locked: boolean;
}

export interface ModulePublic {
  id: string;
  title: string;
  description?: string | null;
  order_index: number;
  lessons: LessonPublic[];
  duration_seconds: number;
}

export interface ModuleDetail {
  id: string;
  title: string;
  description?: string | null;
  order_index: number;
  lessons: LessonDetail[];
}

export interface CourseDetail extends CourseCard {
  description?: string | null;
  status: CourseStatus;
  what_you_learn?: string[] | null;
  requirements?: string[] | null;
  target_audience?: string[] | null;
  has_certificate: boolean;
  sequential_progress: boolean;
  completion_threshold: number;
  modules: ModulePublic[];
  organization_id?: string | null;
  published_at?: string | null;
  created_at: string;
}

export interface CourseAdminSummary extends CourseCard {
  description?: string | null;
  status: CourseStatus;
  what_you_learn?: string[] | null;
  requirements?: string[] | null;
  target_audience?: string[] | null;
  has_certificate: boolean;
  sequential_progress: boolean;
  completion_threshold: number;
  organization_id?: string | null;
  owner_id: string;
  published_at?: string | null;
  submitted_at?: string | null;
  rejection_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CourseAdminDetail extends CourseAdminSummary {
  modules: ModulePublic[];
}

export interface Review {
  id: string;
  rating: number;
  comment?: string | null;
  created_at: string;
  user?: CourseOwner | null;
}

export interface CartItem {
  id: string;
  course: CourseCard;
  created_at: string;
}

export interface CartSummary {
  items: CartItem[];
  subtotal: string;
  discount_total: string;
  total: string;
  currency: string;
  coupon_code?: string | null;
}

export interface OrderItem {
  id: string;
  course_id: string;
  course_title: string;
  unit_price: string;
  quantity: number;
}

export interface Order {
  id: string;
  order_number: string;
  status: OrderStatus;
  subtotal: string;
  discount_total: string;
  total: string;
  currency: string;
  items: OrderItem[];
  paid_at?: string | null;
  created_at: string;
}

export interface CheckoutResponse {
  order: Order;
  checkout_url: string;
  provider: string;
  payment_id: string;
  is_free: boolean;
}

export interface Enrollment {
  id: string;
  course: CourseCard;
  status: EnrollmentStatus;
  source: EnrollmentSource;
  progress_percent: number;
  completed_lessons: number;
  last_lesson_id?: string | null;
  enrolled_at: string;
  completed_at?: string | null;
  has_certificate: boolean;
}

export interface LearnCourse {
  enrollment_id: string;
  course: CourseCard;
  progress_percent: number;
  completed_lessons: number;
  total_lessons: number;
  modules: ModuleDetail[];
  current_lesson_id?: string | null;
  sequential_progress: boolean;
  certificate_code?: string | null;
}

export interface PlaybackInfo {
  url: string;
  expires_at: string;
  content_type: string;
  provider: string;
  thumbnail_url?: string | null;
}

export interface ProgressUpdateResult {
  lesson_id: string;
  completed: boolean;
  watch_seconds: number;
  last_position_seconds: number;
  course_progress_percent: number;
  course_completed: boolean;
  next_lesson_id?: string | null;
  certificate_issued: boolean;
}

export interface QuizOption {
  id: string;
  text: string;
}

export interface QuizQuestion {
  id: string;
  text: string;
  type: "single" | "multiple" | "boolean";
  options: QuizOption[];
  points: number;
}

export interface Quiz {
  id: string;
  lesson_id: string;
  title?: string | null;
  passing_score: number;
  max_attempts: number;
  time_limit_minutes?: number | null;
  questions: QuizQuestion[];
  attempts_used: number;
  best_score?: number | null;
  passed: boolean;
}

export interface QuizResult {
  score: number;
  passed: boolean;
  passing_score: number;
  correct_count: number;
  total_questions: number;
  attempt_number: number;
  details: Array<{
    question_id: string;
    correct: boolean;
    correct_answers: string[];
    given_answers: string[];
  }>;
  course_progress_percent: number;
  certificate_issued: boolean;
}

export interface Certificate {
  id: string;
  certificate_code: string;
  pdf_url?: string | null;
  verification_url?: string | null;
  issued_at: string;
  course_title?: string | null;
  course_id?: string | null;
}

export interface CertificateVerification {
  valid: boolean;
  certificate_code: string;
  student_name?: string | null;
  course_title?: string | null;
  teacher_name?: string | null;
  issued_at?: string | null;
  pdf_url?: string | null;
  message: string;
}

export interface EarningsSummary {
  gross_total: string;
  commission_total: string;
  net_total: string;
  pending_payout: string;
  paid_out: string;
  currency: string;
  sales_count: number;
  students_count: number;
}

export interface EarningsPoint {
  date: string;
  gross: string;
  net: string;
  sales: number;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  type: "school" | "teacher" | "training_center" | "b2b_client";
  description?: string | null;
  logo_url?: string | null;
  website?: string | null;
  is_verified: boolean;
  created_at: string;
  contact_email?: string | null;
  contact_phone?: string | null;
  owner_id?: string | null;
  seats_purchased?: number;
  crm_sync_enabled?: boolean;
  crm_provider?: string | null;
  members_count?: number;
  courses_count?: number;
}

export interface B2BDashboard {
  organization_id: string;
  organization_name: string;
  employees_count: number;
  seats_purchased: number;
  seats_used: number;
  enrollments_total: number;
  completed_total: number;
  avg_progress: number;
  certificates_total: number;
  active_courses: number;
  crm_sync_enabled: boolean;
  crm_last_sync_at?: string | null;
}

export interface EmployeeProgress {
  user_id: string;
  full_name: string;
  email: string;
  courses_total: number;
  courses_completed: number;
  avg_progress: number;
  certificates: number;
  last_activity?: string | null;
}

export interface PlatformKpi {
  revenue_total: string;
  revenue_month: string;
  commission_total: string;
  users_total: number;
  users_new_week: number;
  students_active: number;
  teachers_total: number;
  organizations_total: number;
  courses_published: number;
  courses_pending: number;
  enrollments_total: number;
  completions_total: number;
  certificates_total: number;
  conversion_percent: number;
  pending_payouts: number;
}

export interface RevenuePoint {
  date: string;
  revenue: string;
  commission: string;
  orders: number;
}

export interface ActivityItem {
  type: string;
  title: string;
  subtitle?: string | null;
  created_at: string;
}

export interface IntegrationStatus {
  provider: string;
  display_name: string;
  kind: IntegrationKind;
  health: IntegrationHealth;
  is_enabled: boolean;
  last_success_at?: string | null;
  last_error_at?: string | null;
  last_error_message?: string | null;
  consecutive_failures: number;
}

export interface AdminUserRow extends User {
  is_blocked: boolean;
  organization_name?: string | null;
  courses_count: number;
  enrollments_count: number;
}

export interface CrmSyncLog {
  id: string;
  provider: string;
  event_type: string;
  status: "pending" | "success" | "failed";
  external_id?: string | null;
  error_message?: string | null;
  attempts: number;
  created_at: string;
  synced_at?: string | null;
}

export interface Coupon {
  id: string;
  code: string;
  type: "percent" | "fixed";
  value: string;
  course_id?: string | null;
  max_redemptions?: number | null;
  redemptions_count: number;
  min_order_total?: string | null;
  starts_at?: string | null;
  expires_at?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface CouponValidateResponse {
  valid: boolean;
  discount: string;
  message: string;
  coupon?: Coupon | null;
}

export interface BulkEnrollResult {
  enrolled: number;
  created_users: number;
  skipped: string[];
  seats_used: number;
  seats_available?: number | null;
}

export interface SystemSetting {
  key: string;
  value: Record<string, unknown> | null;
  description?: string | null;
  is_public: boolean;
}

export interface PayoutRequest {
  id: string;
  amount: string;
  currency: string;
  status: "pending" | "approved" | "paid" | "rejected";
  admin_comment?: string | null;
  requested_at: string;
  reviewed_at?: string | null;
}

export interface TeacherStudentRow {
  id: string;
  user_id: string;
  course_id: string;
  status: EnrollmentStatus;
  progress_percent: number;
  completed_lessons: number;
  enrolled_at: string;
  completed_at?: string | null;
  user_name?: string | null;
  user_email?: string | null;
  course_title?: string | null;
}

export interface CourseFilters {
  search?: string;
  category?: string;
  level?: CourseLevel;
  language?: CourseLanguage;
  price_min?: number;
  price_max?: number;
  is_free?: boolean;
  min_rating?: number;
  teacher_id?: string;
  sort?: "newest" | "popular" | "rating" | "price_asc" | "price_desc";
  page?: number;
  per_page?: number;
}
