from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from slugify import slugify
from sqlalchemy import func, select

import app.models  # noqa: F401
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.catalog import Category, Course, CourseModule, Lesson
from app.models.enums import (
    CourseLanguage,
    CourseLevel,
    CourseStatus,
    LessonContentType,
    OrganizationType,
    UserRole,
)
from app.models.learning import Quiz
from app.models.organization import Organization
from app.models.system import SystemSetting
from app.models.user import User

logger = logging.getLogger(__name__)

CATEGORIES = [
    ("IT va Dasturlash", "code", "Frontend, backend, mobil, DevOps va sun'iy intellekt"),
    ("Til o'rganish", "languages", "Ingliz, rus, koreys, arab va boshqa tillar"),
    ("Maktab fanlari", "graduation-cap", "Matematika, fizika, kimyo, biologiya, ona tili"),
    ("Biznes va Menejment", "briefcase", "Tadbirkorlik, moliya, loyiha boshqaruvi"),
    ("Dizayn", "palette", "UI/UX, grafik dizayn, 3D va motion"),
    ("Marketing", "megaphone", "SMM, SEO, kontent marketing, targeting"),
    ("Shaxsiy rivojlanish", "sparkles", "Vaqt boshqaruvi, notiqlik, liderlik"),
    ("Buxgalteriya", "calculator", "Soliq, 1C, moliyaviy hisobot"),
]

SYSTEM_SETTINGS = [
    (
        "commission",
        {"percent": settings.PLATFORM_COMMISSION_PERCENT},
        "Platforma komissiyasi (foizda)",
        True,
    ),
    (
        "feature_flags",
        {
            "reviews": True,
            "coupons": True,
            "gamification": False,
            "live_lessons": False,
            "ai_subtitles": False,
            "referral": False,
        },
        "Funksiyalarni bosqichma-bosqich yoqish (ADDITIONAL_FEATURES 5)",
        True,
    ),
    (
        "locales",
        {"default": "uz", "available": ["uz", "ru", "en"]},
        "Interfeys tillari",
        True,
    ),
    (
        "payout",
        {"min_amount": 100000, "currency": "UZS"},
        "Minimal pul yechish summasi",
        False,
    ),
]


async def ensure_categories() -> int:
    created = 0
    async with AsyncSessionLocal() as db:
        for index, (name, icon, description) in enumerate(CATEGORIES):
            slug = slugify(name)[:140]
            exists = await db.scalar(select(Category.id).where(Category.slug == slug))
            if exists:
                continue
            db.add(
                Category(
                    name=name,
                    slug=slug,
                    icon=icon,
                    description=description,
                    order_index=index,
                )
            )
            created += 1
        await db.commit()
    logger.info("Kategoriyalar: +%s yaratildi", created)
    return created


async def ensure_settings() -> int:
    created = 0
    async with AsyncSessionLocal() as db:
        for key, value, description, is_public in SYSTEM_SETTINGS:
            exists = await db.scalar(select(SystemSetting.id).where(SystemSetting.key == key))
            if exists:
                continue
            db.add(
                SystemSetting(key=key, value=value, description=description, is_public=is_public)
            )
            created += 1
        await db.commit()
    logger.info("Tizim sozlamalari: +%s yaratildi", created)
    return created


async def ensure_superadmin() -> User | None:
    async with AsyncSessionLocal() as db:
        email = settings.FIRST_SUPERADMIN_EMAIL.lower()
        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            if existing.role is not UserRole.admin:
                existing.role = UserRole.admin
                await db.commit()
                logger.info("Mavjud foydalanuvchi admin qilindi: %s", email)
            return existing

        admin = User(
            full_name="Zehno Super Admin",
            email=email,
            hashed_password=hash_password(settings.FIRST_SUPERADMIN_PASSWORD),
            role=UserRole.admin,
            is_active=True,
            email_verified_at=datetime.now(UTC),
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        logger.info("Super-admin yaratildi: %s", email)
        return admin


async def ensure_demo_content() -> None:
    async with AsyncSessionLocal() as db:
        courses_count = await db.scalar(select(func.count(Course.id)))
        if courses_count and courses_count > 0:
            logger.info("Demo kontent allaqachon mavjud (kurslar: %s)", courses_count)
            return

        org = await db.scalar(select(Organization).where(Organization.slug == "zehno-academy"))
        if org is None:
            org = Organization(
                name="Zehno Academy",
                slug="zehno-academy",
                type=OrganizationType.training_center,
                description="Zehno platformasining namunaviy o'quv markazi",
                contact_email="academy@zehno.uz",
                is_verified=True,
            )
            db.add(org)
            await db.flush()

        teacher = await db.scalar(select(User).where(User.email == "ustoz@zehno.uz"))
        if teacher is None:
            teacher = User(
                full_name="Aziz Karimov",
                email="ustoz@zehno.uz",
                hashed_password=hash_password("Ustoz12345!"),
                role=UserRole.org_admin,
                organization_id=org.id,
                bio=(
                    "10 yildan ortiq tajribaga ega dasturchi va ustoz. "
                    "5000+ o'quvchiga frontend va backend yo'nalishlarini o'rgatgan."
                ),
                email_verified_at=datetime.now(UTC),
            )
            db.add(teacher)
            await db.flush()
            org.owner_id = teacher.id

        student = await db.scalar(select(User).where(User.email == "talaba@zehno.uz"))
        if student is None:
            student = User(
                full_name="Malika Yusupova",
                email="talaba@zehno.uz",
                hashed_password=hash_password("Talaba12345!"),
                role=UserRole.student,
                email_verified_at=datetime.now(UTC),
            )
            db.add(student)

        b2b_org = await db.scalar(select(Organization).where(Organization.slug == "demo-tech-llc"))
        if b2b_org is None:
            b2b_org = Organization(
                name="Demo Tech LLC",
                slug="demo-tech-llc",
                type=OrganizationType.b2b_client,
                description="Namunaviy korporativ mijoz",
                contact_email="hr@demotech.uz",
                seats_purchased=25,
                is_verified=True,
            )
            db.add(b2b_org)
            await db.flush()

        manager = await db.scalar(select(User).where(User.email == "hr@demotech.uz"))
        if manager is None:
            manager = User(
                full_name="Dilshod Rahimov",
                email="hr@demotech.uz",
                hashed_password=hash_password("Manager12345!"),
                role=UserRole.b2b_manager,
                organization_id=b2b_org.id,
                email_verified_at=datetime.now(UTC),
            )
            db.add(manager)
            await db.flush()
            b2b_org.owner_id = manager.id

        await db.commit()

        it_category = await db.scalar(select(Category).where(Category.slug == "it-va-dasturlash"))
        lang_category = await db.scalar(select(Category).where(Category.slug == "til-organish"))
        design_category = await db.scalar(select(Category).where(Category.slug == "dizayn"))

        demo_courses = [
            {
                "title": "Frontend dasturlash: HTML, CSS va JavaScript",
                "subtitle": "Noldan boshlab zamonaviy veb-saytlar yaratishni o'rganing",
                "description": (
                    "Bu kursda siz veb-dasturlashning asoslarini o'rganasiz: HTML semantikasi, "
                    "CSS Flexbox/Grid, responsive dizayn va JavaScript asoslari. "
                    "Kurs oxirida o'z portfolio saytingizni yaratasiz."
                ),
                "price": Decimal("450000"),
                "discount_price": Decimal("299000"),
                "level": CourseLevel.beginner,
                "category": it_category,
                "cover_url": "https://images.unsplash.com/photo-1547658719-da2b51169166?w=800",
                "what_you_learn": [
                    "HTML5 semantik teglar bilan to'g'ri struktura qurish",
                    "CSS Flexbox va Grid orqali istalgan layoutni yasash",
                    "JavaScript bilan interaktiv elementlar yaratish",
                    "Responsive (mobil-birinchi) dizayn printsiplari",
                    "Git va GitHub bilan ishlash",
                ],
                "requirements": ["Kompyuter va internet", "Maxsus bilim talab qilinmaydi"],
                "target_audience": ["Boshlang'ich dasturchilar", "Kasb almashtirmoqchi bo'lganlar"],
                "modules": [
                    (
                        "1-modul. HTML asoslari",
                        [
                            ("Kirish: veb qanday ishlaydi", 480, True),
                            ("HTML strukturasi va teglar", 920, False),
                            ("Formalar va tablitsalar", 760, False),
                            ("Amaliyot: birinchi sahifa", 1200, False),
                        ],
                    ),
                    (
                        "2-modul. CSS va layout",
                        [
                            ("CSS selektorlar va kaskad", 840, False),
                            ("Flexbox chuqur", 1100, False),
                            ("CSS Grid bilan layout", 1050, False),
                            ("Responsive dizayn", 980, False),
                        ],
                    ),
                    (
                        "3-modul. JavaScript asoslari",
                        [
                            ("O'zgaruvchilar va tiplar", 900, False),
                            ("Funksiyalar va massivlar", 1150, False),
                            ("DOM bilan ishlash", 1300, False),
                            ("Yakuniy loyiha: portfolio sayt", 1800, False),
                        ],
                    ),
                ],
                "quiz_after": "3-modul. JavaScript asoslari",
                "featured": True,
                "bestseller": True,
            },
            {
                "title": "Ingliz tili: IELTS 7.0+ ga tayyorgarlik",
                "subtitle": "Speaking, Writing, Reading va Listening bo'yicha to'liq strategiya",
                "description": (
                    "IELTS imtihonining har bir bo'limi uchun amaliy strategiyalar, "
                    "namunaviy javoblar tahlili va 40+ mashq. Kurs 8 haftaga mo'ljallangan."
                ),
                "price": Decimal("600000"),
                "level": CourseLevel.intermediate,
                "category": lang_category,
                "cover_url": "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=800",
                "what_you_learn": [
                    "Writing Task 1 va 2 uchun tayyor strukturalar",
                    "Speaking Part 2 da 2 daqiqa ravon gapirish",
                    "Reading'da vaqtni to'g'ri boshqarish",
                    "Listening'da tez-tez uchraydigan tuzoqlar",
                ],
                "requirements": ["Ingliz tili B1 darajasi"],
                "modules": [
                    (
                        "1-modul. Imtihon strukturasi",
                        [
                            ("IELTS formati va baholash", 600, True),
                            ("Tayyorgarlik rejasi tuzish", 720, False),
                        ],
                    ),
                    (
                        "2-modul. Writing",
                        [
                            ("Task 1: grafiklarni tavsiflash", 1200, False),
                            ("Task 2: esse strukturasi", 1350, False),
                            ("Grammatik xatolar tahlili", 900, False),
                        ],
                    ),
                    (
                        "3-modul. Speaking",
                        [
                            ("Part 1: shaxsiy savollar", 850, False),
                            ("Part 2: cue card strategiyasi", 1100, False),
                            ("Part 3: munozara", 950, False),
                        ],
                    ),
                ],
                "featured": True,
            },
            {
                "title": "UI/UX dizayn: Figma'da noldan portfolioga",
                "subtitle": "Mobil va veb interfeyslar dizayni + real loyihalar",
                "description": (
                    "Figma vositalari, dizayn tizimi (design system) qurish, prototiplash "
                    "va portfolio uchun 3 ta real keys."
                ),
                "price": Decimal("0"),
                "level": CourseLevel.beginner,
                "category": design_category,
                "cover_url": "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800",
                "what_you_learn": [
                    "Figma'da tez ishlash (komponentlar, auto-layout)",
                    "Rang va tipografiya tanlash printsiplari",
                    "Foydalanuvchi oqimlarini (user flow) loyihalash",
                ],
                "modules": [
                    (
                        "1-modul. Figma asoslari",
                        [
                            ("Interfeys bilan tanishuv", 540, True),
                            ("Auto-layout va komponentlar", 980, False),
                            ("Design system yaratish", 1240, False),
                        ],
                    ),
                    (
                        "2-modul. Amaliy loyiha",
                        [
                            ("Mobil ilova ekranlari", 1500, False),
                            ("Prototip va animatsiya", 1100, False),
                        ],
                    ),
                ],
                "language": CourseLanguage.uz,
            },
        ]

        for data in demo_courses:
            course = Course(
                owner_id=teacher.id,
                organization_id=org.id,
                category_id=data["category"].id if data.get("category") else None,
                title=data["title"],
                slug=slugify(data["title"])[:200],
                subtitle=data["subtitle"],
                description=data["description"],
                cover_url=data.get("cover_url"),
                price=data["price"],
                discount_price=data.get("discount_price"),
                level=data["level"],
                language=data.get("language", CourseLanguage.uz),
                status=CourseStatus.published,
                published_at=datetime.now(UTC) - timedelta(days=7),
                what_you_learn=data.get("what_you_learn"),
                requirements=data.get("requirements"),
                target_audience=data.get("target_audience"),
                is_featured=data.get("featured", False),
                is_bestseller=data.get("bestseller", False),
                rating_avg=4.8 if data.get("bestseller") else 4.6,
                rating_count=124 if data.get("bestseller") else 38,
                students_count=1240 if data.get("bestseller") else 210,
            )
            db.add(course)
            await db.flush()

            total_duration = 0
            total_lessons = 0
            for module_index, (module_title, lessons) in enumerate(data["modules"]):
                module = CourseModule(
                    course_id=course.id, title=module_title, order_index=module_index
                )
                db.add(module)
                await db.flush()

                for lesson_index, (lesson_title, duration, is_preview) in enumerate(lessons):
                    lesson = Lesson(
                        module_id=module.id,
                        title=lesson_title,
                        content_type=LessonContentType.video,
                        order_index=lesson_index,
                        duration_seconds=duration,
                        is_preview=is_preview,
                    )
                    db.add(lesson)
                    total_duration += duration
                    total_lessons += 1

                await db.flush()

                if data.get("quiz_after") == module_title:
                    quiz_lesson = Lesson(
                        module_id=module.id,
                        title="Yakuniy test",
                        content_type=LessonContentType.quiz,
                        order_index=len(lessons),
                        duration_seconds=600,
                    )
                    db.add(quiz_lesson)
                    await db.flush()
                    db.add(
                        Quiz(
                            lesson_id=quiz_lesson.id,
                            title="Kurs bo'yicha yakuniy test",
                            passing_score=60,
                            questions=[
                                {
                                    "id": "q1",
                                    "text": (
                                        "HTML'da sahifaning asosiy kontenti "
                                        "uchun qaysi teg ishlatiladi?"
                                    ),
                                    "type": "single",
                                    "options": [
                                        {"id": "a", "text": "<main>"},
                                        {"id": "b", "text": "<div>"},
                                        {"id": "c", "text": "<section>"},
                                        {"id": "d", "text": "<article>"},
                                    ],
                                    "correct": ["a"],
                                    "points": 1,
                                },
                                {
                                    "id": "q2",
                                    "text": (
                                        "Flexbox'da elementlarni gorizontal markazlashtirish uchun?"
                                    ),
                                    "type": "single",
                                    "options": [
                                        {"id": "a", "text": "align-items: center"},
                                        {"id": "b", "text": "justify-content: center"},
                                        {"id": "c", "text": "text-align: center"},
                                    ],
                                    "correct": ["b"],
                                    "points": 1,
                                },
                                {
                                    "id": "q3",
                                    "text": (
                                        "JavaScript'da massiv metodlarini tanlang (bir nechta):"
                                    ),
                                    "type": "multiple",
                                    "options": [
                                        {"id": "a", "text": "map()"},
                                        {"id": "b", "text": "filter()"},
                                        {"id": "c", "text": "parseInt()"},
                                        {"id": "d", "text": "reduce()"},
                                    ],
                                    "correct": ["a", "b", "d"],
                                    "points": 2,
                                },
                            ],
                        )
                    )
                    total_lessons += 1
                    total_duration += 600

            course.lessons_count = total_lessons
            course.duration_seconds = total_duration

        await db.commit()
        logger.info("Demo kontent yaratildi: %s kurs", len(demo_courses))


async def run_seed(with_demo: bool = True) -> None:
    await ensure_categories()
    await ensure_settings()
    await ensure_superadmin()
    if with_demo:
        await ensure_demo_content()
    logger.info("Seed yakunlandi")
