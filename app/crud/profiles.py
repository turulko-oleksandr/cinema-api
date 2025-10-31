from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.models.models import UserProfile, User


async def get_user_profile(db: AsyncSession, user_id: int) -> Optional[UserProfile]:
    """Get user profile by user_id"""
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_user_profile(db: AsyncSession, user_id: int) -> UserProfile:
    """Get user profile or create if doesn't exist"""
    profile = await get_user_profile(db, user_id)

    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return profile


async def update_user_profile(
    db: AsyncSession, user_id: int, profile_data: dict
) -> UserProfile:
    """Update user profile with provided data"""
    profile = await get_or_create_user_profile(db, user_id)

    # Update only provided fields
    for field, value in profile_data.items():
        if value is not None or field in profile_data:
            setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return profile


async def update_user_avatar(
    db: AsyncSession, user_id: int, avatar_path: str
) -> UserProfile:
    """Update user avatar path"""
    profile = await get_or_create_user_profile(db, user_id)
    print("DEBUG user_id:", user_id)
    # Store old avatar path for potential cleanup
    old_avatar = profile.avatar

    profile.avatar = avatar_path
    await db.commit()
    await db.refresh(profile)

    return profile, old_avatar


async def delete_user_avatar(db: AsyncSession, user_id: int) -> Optional[str]:
    """Delete user avatar and return old avatar path"""
    profile = await get_user_profile(db, user_id)

    if not profile or not profile.avatar:
        return None

    old_avatar = profile.avatar
    profile.avatar = None

    await db.commit()
    await db.refresh(profile)

    return old_avatar
