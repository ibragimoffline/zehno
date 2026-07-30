from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession, client_ip
from app.core.exceptions import AuthenticationError
from app.core.rate_limit import auth_rate_limit
from app.modules.auth.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TelegramLinkResponse,
    TokenPair,
    UpdateProfileRequest,
    UserPublic,
)
from app.modules.auth.service import AuthService
from app.schemas.common import Message

router = APIRouter(prefix="/auth", tags=["Auth"])


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="lax",
        domain=settings.REFRESH_COOKIE_DOMAIN or None,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        domain=settings.REFRESH_COOKIE_DOMAIN or None,
        path="/",
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ro'yxatdan o'tish",
    dependencies=[Depends(auth_rate_limit)],
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> AuthResponse:
    service = AuthService(db)
    user = await service.register(payload)
    tokens = await service.issue_tokens(
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip(request),
    )
    if tokens.refresh_token:
        _set_refresh_cookie(response, tokens.refresh_token)
    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Tizimga kirish",
    dependencies=[Depends(auth_rate_limit)],
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> AuthResponse:
    service = AuthService(db)
    user = await service.authenticate(payload)
    tokens = await service.issue_tokens(
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip(request),
    )
    if tokens.refresh_token:
        _set_refresh_cookie(response, tokens.refresh_token)
    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Access tokenni yangilash",
    dependencies=[Depends(auth_rate_limit)],
)
async def refresh(
    request: Request,
    response: Response,
    db: DbSession,
    payload: RefreshRequest | None = None,
) -> TokenPair:
    raw_token = (payload.refresh_token if payload else None) or request.cookies.get(
        settings.REFRESH_COOKIE_NAME
    )
    if not raw_token:
        raise AuthenticationError("Refresh token yuborilmadi")

    service = AuthService(db)
    _, tokens = await service.rotate_refresh_token(
        raw_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip(request),
    )
    if tokens.refresh_token:
        _set_refresh_cookie(response, tokens.refresh_token)
    return tokens


@router.post("/logout", response_model=Message, summary="Chiqish")
async def logout(
    request: Request,
    response: Response,
    db: DbSession,
    payload: RefreshRequest | None = None,
) -> Message:
    raw_token = (payload.refresh_token if payload else None) or request.cookies.get(
        settings.REFRESH_COOKIE_NAME
    )
    if raw_token:
        await AuthService(db).revoke_refresh_token(raw_token)
    _clear_refresh_cookie(response)
    return Message(message="Tizimdan chiqdingiz")


@router.post("/logout-all", response_model=Message, summary="Barcha qurilmalardan chiqish")
async def logout_all(user: CurrentUser, response: Response, db: DbSession) -> Message:
    await AuthService(db).revoke_all_sessions(user.id)
    _clear_refresh_cookie(response)
    return Message(message="Barcha sessiyalar yopildi")


@router.get("/me", response_model=UserPublic, summary="Joriy foydalanuvchi")
async def me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)


@router.patch("/me", response_model=UserPublic, summary="Profilni tahrirlash")
async def update_me(payload: UpdateProfileRequest, user: CurrentUser, db: DbSession) -> UserPublic:
    updated = await AuthService(db).update_profile(user, payload)
    return UserPublic.model_validate(updated)


@router.post("/change-password", response_model=Message, summary="Parolni o'zgartirish")
async def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUser,
    response: Response,
    db: DbSession,
) -> Message:
    await AuthService(db).change_password(user, payload.current_password, payload.new_password)
    _clear_refresh_cookie(response)
    return Message(message="Parol o'zgartirildi. Iltimos qaytadan kiring")


@router.post(
    "/telegram/link-code",
    response_model=TelegramLinkResponse,
    summary="Telegram botga ulanish kodi",
)
async def telegram_link_code(user: CurrentUser, db: DbSession) -> TelegramLinkResponse:
    code = await AuthService(db).create_telegram_link_code(user)
    bot_username = settings.TELEGRAM_BOT_USERNAME
    deep_link = f"https://t.me/{bot_username}?start={code}" if bot_username else None
    return TelegramLinkResponse(
        link_code=code,
        deep_link=deep_link,
        instructions=(f"Botni oching va /start buyrug'ini kod bilan yuboring: /start {code}"),
    )
