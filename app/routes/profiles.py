from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_session import get_db
from app.crud.profiles import (
    get_user_profile,
    get_or_create_user_profile,
    update_user_profile,
    update_user_avatar,
    delete_user_avatar,
)
from app.schemas.profiles import (
    UserProfileResponse,
    UserProfileUpdate,
    AvatarUploadResponse,
)
from app.services.role_manager import get_current_user
from app.database.models.models import User
from app.services.minio_service import get_minio_service

router = APIRouter(tags=["User Profile"])

# Allowed image types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )


@router.get("/", response_model=UserProfileResponse, summary="Get user profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile"""
    profile = await get_or_create_user_profile(db, current_user.id)

    # Add presigned URL for avatar if exists
    profile_dict = {
        "id": profile.id,
        "user_id": profile.user_id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "gender": profile.gender,
        "date_of_birth": profile.date_of_birth,
        "info": profile.info,
        "avatar": profile.avatar,
        "avatar_url": None,
    }

    if profile.avatar:
        try:
            minio_service = get_minio_service()
            profile_dict["avatar_url"] = minio_service.get_file_url(profile.avatar)
        except Exception as e:
            print(f"Error getting avatar URL: {e}")

    return profile_dict


@router.put("/", response_model=UserProfileResponse, summary="Update user profile")
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile"""
    # Convert to dict and exclude unset fields
    update_data = profile_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    profile = await update_user_profile(db, current_user.id, update_data)

    # Add presigned URL for avatar if exists
    profile_dict = {
        "id": profile.id,
        "user_id": profile.user_id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "gender": profile.gender,
        "date_of_birth": profile.date_of_birth,
        "info": profile.info,
        "avatar": profile.avatar,
        "avatar_url": None,
    }

    if profile.avatar:
        try:
            minio_service = get_minio_service()
            profile_dict["avatar_url"] = minio_service.get_file_url(profile.avatar)
        except Exception as e:
            print(f"Error getting avatar URL: {e}")

    return profile_dict


@router.post(
    "/avatar",
    response_model=AvatarUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload user avatar",
)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and update user avatar"""
    # Validate file type
    validate_image_file(file)

    # Read file data
    file_data = await file.read()

    # Validate file size
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB",
        )

    try:
        # Upload to MinIO
        minio_service = get_minio_service()
        object_name = minio_service.upload_file(
            file_data=file_data,
            file_name=file.filename,
            content_type=file.content_type,
            folder="avatars",
        )

        # Update user profile with new avatar path
        profile, old_avatar = await update_user_avatar(db, current_user.id, object_name)

        # Delete old avatar if exists
        if old_avatar:
            try:
                minio_service.delete_file(old_avatar)
            except Exception as e:
                print(f"Error deleting old avatar: {e}")

        # Get presigned URL
        avatar_url = minio_service.get_file_url(object_name)

        return AvatarUploadResponse(
            avatar=object_name,
            avatar_url=avatar_url,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading avatar: {str(e)}",
        )


@router.delete(
    "/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user avatar",
)
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete user avatar"""
    old_avatar = await delete_user_avatar(db, current_user.id)

    if not old_avatar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No avatar to delete",
        )

    # Delete from MinIO
    try:
        minio_service = get_minio_service()
        minio_service.delete_file(old_avatar)
    except Exception as e:
        print(f"Error deleting avatar from MinIO: {e}")

    return None
