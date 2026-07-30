"""Ilova xatolari va global exception handlerlar.

Barcha xato javoblari bir xil shaklda qaytadi — frontend uchun qulay:

```json
{"error": {"code": "not_found", "message": "Kurs topilmadi", "details": null}}
```
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Ilovaning barcha biznes-xatolari uchun asos."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"
    message: str = "Xatolik yuz berdi"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "Ma'lumot topilmadi"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "Bunday ma'lumot allaqachon mavjud"


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_error"
    message = "Kiritilgan ma'lumot noto'g'ri"


class AuthenticationError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthenticated"
    message = "Autentifikatsiya talab qilinadi"


class PermissionDeniedError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "permission_denied"
    message = "Bu amal uchun ruxsat yo'q"


class PaymentError(AppError):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    code = "payment_error"
    message = "To'lovda xatolik"


class IntegrationError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "integration_error"
    message = "Tashqi xizmat bilan bog'lanishda xatolik"

    def __init__(self, message: str | None = None, *, provider: str | None = None, **kwargs: Any):
        self.provider = provider
        super().__init__(message, **kwargs)


class RateLimitError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"
    message = "So'rovlar soni chegarasidan oshdi"


def error_response(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"error": {"code": code, "message": message, "details": details}}),
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            401: "unauthenticated",
            403: "permission_denied",
            404: "not_found",
            405: "method_not_allowed",
            409: "conflict",
            429: "rate_limited",
        }
        return error_response(
            exc.status_code,
            code_map.get(exc.status_code, "http_error"),
            str(exc.detail) if exc.detail else "Xatolik",
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "Kiritilgan ma'lumot noto'g'ri",
            exc.errors(),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("DB integrity error: %s", exc)
        return error_response(
            status.HTTP_409_CONFLICT,
            "conflict",
            "Ma'lumotlar bazasi cheklovi buzildi (takroriy yozuv bo'lishi mumkin)",
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Kutilmagan xatolik: %s %s", request.method, request.url.path)
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "Serverda kutilmagan xatolik yuz berdi",
        )
