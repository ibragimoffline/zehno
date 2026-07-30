from __future__ import annotations

from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.b2b.router import router as b2b_router
from app.modules.certificates.router import router as certificates_router
from app.modules.commerce.router import router as commerce_router
from app.modules.courses.router import router as courses_router
from app.modules.media.router import router as media_router
from app.modules.organizations.router import router as organizations_router
from app.modules.progress.router import router as progress_router
from app.modules.users.router import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(organizations_router)
api_router.include_router(courses_router)
api_router.include_router(media_router)
api_router.include_router(commerce_router)
api_router.include_router(progress_router)
api_router.include_router(certificates_router)
api_router.include_router(b2b_router)
api_router.include_router(admin_router)
