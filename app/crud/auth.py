from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime

from database.models import (
    User,
    UserGroup,
    UserGroupEnum,
    ActivationToken,
    PasswordResetToken,
    RefreshToken,
    UserProfile,
)
from app.core.security import (
    get_password_hash,
    verify_password,
    generate_token,
    get_activation_token_expiry,
    get_password_reset_token_expiry,
    get_refresh_token_expiry,
    is_token_expired,
)
from app.services.email import email_service


# ============================================================================
# USER OPERATIONS
# ============================================================================


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    query = select(User).options(selectinload(User.group)).where(User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID with relationships"""
    query = (
        select(User)
        .options(
            selectinload(User.group),
            selectinload(User.profile),
        )
        .where(User.id == user_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    group_name: UserGroupEnum = UserGroupEnum.USER,
) -> User:
    """
    Create a new user

    Args:
        db: Database session
        email: User's email
        password: Plain password
        group_name: User group (default: USER)

    Returns:
        Created user
    """
    # Get user group
    group_query = select(UserGroup).where(UserGroup.name == group_name)
    group_result = await db.execute(group_query)
    group = group_result.scalar_one_or_none()

    if not group:
        # Create default group if not exists
        group = UserGroup(name=group_name)
        db.add(group)
        await db.flush()

    # Create user
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        is_active=False,  # Inactive until email verification
        group_id=group.id,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create empty profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    await db.commit()

    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """
    Authenticate user by email and password

    Args:
        db: Database session
        email: User's email
        password: Plain password

    Returns:
        User if authenticated, None otherwise
    """
    user = await get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    if not user.is_active:
        return None

    return user


# ============================================================================
# ACTIVATION TOKEN OPERATIONS
# ============================================================================


async def create_activation_token(db: AsyncSession, user_id: int) -> str:
    """
    Create activation token for user

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Token string
    """
    # Delete existing token if any
    await db.execute(delete(ActivationToken).where(ActivationToken.user_id == user_id))

    # Create new token
    token_str = generate_token()
    token = ActivationToken(
        user_id=user_id,
        token=token_str,
        expires_at=get_activation_token_expiry(),
    )

    db.add(token)
    await db.commit()

    return token_str


async def verify_activation_token(db: AsyncSession, token: str) -> Optional[User]:
    """
    Verify activation token and activate user

    Args:
        db: Database session
        token: Activation token string

    Returns:
        Activated user or None if invalid
    """
    query = (
        select(ActivationToken)
        .options(selectinload(ActivationToken.user))
        .where(ActivationToken.token == token)
    )
    result = await db.execute(query)
    activation_token = result.scalar_one_or_none()

    if not activation_token:
        return None

    # Check if token expired
    if is_token_expired(activation_token.expires_at):
        return None

    # Activate user
    user = activation_token.user
    user.is_active = True

    # Delete token
    await db.delete(activation_token)
    await db.commit()
    await db.refresh(user)

    return user


async def delete_expired_activation_tokens(db: AsyncSession) -> int:
    """
    Delete all expired activation tokens (for Celery task)

    Returns:
        Number of deleted tokens
    """
    query = delete(ActivationToken).where(
        ActivationToken.expires_at < datetime.utcnow()
    )
    result = await db.execute(query)
    await db.commit()
    return result.rowcount


# ============================================================================
# PASSWORD RESET TOKEN OPERATIONS
# ============================================================================


async def create_password_reset_token(db: AsyncSession, user_id: int) -> str:
    """
    Create password reset token for user

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Token string
    """
    # Delete existing token if any
    await db.execute(
        delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
    )

    # Create new token
    token_str = generate_token()
    token = PasswordResetToken(
        user_id=user_id,
        token=token_str,
        expires_at=get_password_reset_token_expiry(),
    )

    db.add(token)
    await db.commit()

    return token_str


async def verify_password_reset_token(db: AsyncSession, token: str) -> Optional[User]:
    """
    Verify password reset token

    Args:
        db: Database session
        token: Reset token string

    Returns:
        User if token valid, None otherwise
    """
    query = (
        select(PasswordResetToken)
        .options(selectinload(PasswordResetToken.user))
        .where(PasswordResetToken.token == token)
    )
    result = await db.execute(query)
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        return None

    # Check if token expired
    if is_token_expired(reset_token.expires_at):
        return None

    return reset_token.user


async def reset_password(
    db: AsyncSession, token: str, new_password: str
) -> Optional[User]:
    """
    Reset user password using token

    Args:
        db: Database session
        token: Reset token string
        new_password: New plain password

    Returns:
        User if successful, None otherwise
    """
    query = (
        select(PasswordResetToken)
        .options(selectinload(PasswordResetToken.user))
        .where(PasswordResetToken.token == token)
    )
    result = await db.execute(query)
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        return None

    # Check if token expired
    if is_token_expired(reset_token.expires_at):
        return None

    # Update password
    user = reset_token.user
    user.hashed_password = get_password_hash(new_password)

    # Delete token
    await db.delete(reset_token)
    await db.commit()
    await db.refresh(user)

    # Send confirmation email
    email_service.send_password_changed_email(user.email)

    return user


async def change_password(
    db: AsyncSession, user_id: int, old_password: str, new_password: str
) -> bool:
    """
    Change user password (when user knows old password)

    Args:
        db: Database session
        user_id: User ID
        old_password: Current password
        new_password: New password

    Returns:
        True if successful, False otherwise
    """
    user = await get_user_by_id(db, user_id)

    if not user:
        return False

    # Verify old password
    if not verify_password(old_password, user.hashed_password):
        return False

    # Update password
    user.hashed_password = get_password_hash(new_password)
    await db.commit()

    # Send confirmation email
    email_service.send_password_changed_email(user.email)

    return True


# ============================================================================
# REFRESH TOKEN OPERATIONS
# ============================================================================


async def create_refresh_token_db(
    db: AsyncSession, user_id: int, token: str
) -> RefreshToken:
    """
    Store refresh token in database

    Args:
        db: Database session
        user_id: User ID
        token: Refresh token string

    Returns:
        Created RefreshToken
    """
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=get_refresh_token_expiry(),
    )

    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)

    return refresh_token


async def get_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    """
    Get refresh token from database

    Args:
        db: Database session
        token: Token string

    Returns:
        RefreshToken or None
    """
    query = (
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(RefreshToken.token == token)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def delete_refresh_token(db: AsyncSession, token: str) -> bool:
    """
    Delete refresh token (logout)

    Args:
        db: Database session
        token: Token string

    Returns:
        True if deleted
    """
    query = delete(RefreshToken).where(RefreshToken.token == token)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0


async def delete_user_refresh_tokens(db: AsyncSession, user_id: int) -> int:
    """
    Delete all refresh tokens for user (logout from all devices)

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Number of deleted tokens
    """
    query = delete(RefreshToken).where(RefreshToken.user_id == user_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount
