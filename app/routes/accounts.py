import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext
from app.tasks.email_tasks import (
    send_activation_email_task,
    send_password_reset_email_task,
    send_password_changed_email_task,
)
from app.config.dependencies import get_settings
from app.database import (
    User,
    ActivationToken,
    PasswordResetToken,
    RefreshToken,
    UserGroup,
    UserGroupEnum,
)
from app.database import get_db
from app.schemas.users import (
    UserRegistrationRequestSchema,
    UserLoginRequestSchema,
    UserLoginResponseSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
    PasswordResetRequestSchema,
    PasswordResetCompleteRequestSchema,
    UserActivationRequestSchema,
    MessageResponseSchema,
)
from app.services.interfaces import JWTAuthManagerInterface
from app.exceptions import TokenExpiredError, InvalidTokenError
from app.config.dependencies import get_jwt_auth_manager
from app.services.passwords import validate_password, hash_password, verify_password

router = APIRouter(tags=["Accounts"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register/", status_code=201)
async def register_user(
    payload: UserRegistrationRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
):
    """Register a new user"""
    validate_password(payload.password)

    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user:
        raise HTTPException(
            status_code=409,
            detail=f"A user with this email {payload.email} already exists.",
        )

    stmt_group = select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    result_group = await db.execute(stmt_group)
    user_group = result_group.scalars().first()

    if not user_group:
        raise HTTPException(status_code=500, detail="Default user group not found.")

    hashed_password = hash_password(payload.password)

    new_user = User(
        email=payload.email,
        hashed_password=hashed_password,
        is_active=False,
        group_id=user_group.id,
    )

    db.add(new_user)

    try:
        await db.commit()
        await db.refresh(new_user)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred during user creation: {str(e)}"
        )

    token_value = jwt_manager.create_access_token(
        {"user_id": new_user.id}, timedelta(minutes=30)
    )

    activation_token = ActivationToken(
        user_id=new_user.id,
        token=token_value,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    db.add(activation_token)
    await db.commit()

    send_activation_email_task.delay(new_user.email, token_value)

    return {"email": new_user.email, "id": new_user.id}


@router.post("/activate/", response_model=MessageResponseSchema)
async def activate_user(
    payload: UserActivationRequestSchema, db: AsyncSession = Depends(get_db)
):
    """Activate user account"""
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=400, detail="Invalid or expired activation token."
        )

    if user.is_active:
        raise HTTPException(status_code=400, detail="User account is already active.")

    stmt_token = select(ActivationToken).where(ActivationToken.user_id == user.id)
    result_token = await db.execute(stmt_token)
    token = result_token.scalars().first()

    if not token or token.token != payload.token:
        raise HTTPException(
            status_code=400, detail="Invalid or expired activation token."
        )

    token_expires = token.expires_at
    if token_expires.tzinfo is None:
        token_expires = token_expires.replace(tzinfo=timezone.utc)

    if token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400, detail="Invalid or expired activation token."
        )

    user.is_active = True
    await db.delete(token)
    await db.commit()
    await db.refresh(user)

    return {"message": "User account activated successfully."}


@router.post("/login/", response_model=UserLoginResponseSchema, status_code=201)
async def login_user(
    payload: UserLoginRequestSchema,
    db: AsyncSession = Depends(get_db),
    settings=Depends(get_settings),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
):
    """Login user"""
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is not activated.")

    access_token = jwt_manager.create_access_token(
        {"user_id": user.id}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token_value = jwt_manager.create_refresh_token(
        {"user_id": user.id}, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(refresh_token)

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="An error occurred while processing the request."
        )

    return {"access_token": access_token, "refresh_token": refresh_token_value}


@router.post("/refresh/", response_model=TokenRefreshResponseSchema)
async def refresh_access_token(
    payload: TokenRefreshRequestSchema,
    db: AsyncSession = Depends(get_db),
    settings=Depends(get_settings),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
):
    """Refresh access token"""
    try:
        decoded = jwt_manager.decode_refresh_token(payload.refresh_token)
        user_id = decoded.get("user_id")
    except TokenExpiredError:
        raise HTTPException(status_code=400, detail="Token has expired.")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    stmt_token = select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    result_token = await db.execute(stmt_token)
    token_record = result_token.scalars().first()

    if not token_record:
        raise HTTPException(status_code=401, detail="Refresh token not found.")

    stmt_user = select(User).where(User.id == user_id)
    result_user = await db.execute(stmt_user)
    user = result_user.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_access_token = jwt_manager.create_access_token(
        {"user_id": user.id}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": new_access_token, "refresh_token": payload.refresh_token}


@router.post(
    "/password-reset/request/", response_model=MessageResponseSchema, status_code=200
)
async def request_password_reset(
    payload: PasswordResetRequestSchema,
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
):
    """Request password reset"""
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        return {
            "message": "If you are registered, you will receive an email with instructions."
        }

    delete_stmt = delete(PasswordResetToken).where(
        PasswordResetToken.user_id == user.id
    )
    await db.execute(delete_stmt)

    token_value = jwt_manager.create_access_token(
        {"user_id": user.id}, timedelta(minutes=15)
    )

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token_value,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )

    db.add(reset_token)
    await db.commit()

    send_password_reset_email_task.delay(user.email, token_value)

    return {
        "message": "If you are registered, you will receive an email with instructions."
    }


@router.post(
    "/reset-password/complete/", response_model=MessageResponseSchema, status_code=200
)
async def complete_password_reset(
    payload: PasswordResetCompleteRequestSchema, db: AsyncSession = Depends(get_db)
):
    """Complete password reset"""
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid email or token.")

    stmt_token = select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    result_token = await db.execute(stmt_token)
    token_record = result_token.scalars().first()

    if not token_record or token_record.token != payload.token:
        if token_record:
            await db.delete(token_record)
            await db.commit()
        raise HTTPException(status_code=400, detail="Invalid email or token.")

    token_expires = token_record.expires_at
    if token_expires.tzinfo is None:
        token_expires = token_expires.replace(tzinfo=timezone.utc)

    if token_expires < datetime.now(timezone.utc):
        await db.delete(token_record)
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid email or token.")

    validate_password(payload.password)

    user.hashed_password = hash_password(payload.password)
    await db.delete(token_record)

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="An error occurred while resetting the password."
        )
    send_password_changed_email_task.delay(user.email)
    return {"message": "Password reset successfully."}
