from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.database.models.models import GenderEnum


class UserProfileBase(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[datetime] = None
    info: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class UserProfileCreate(UserProfileBase):
    """Schema for creating user profile"""

    pass


class UserProfileUpdate(UserProfileBase):
    """Schema for updating user profile"""

    pass


class UserProfileResponse(UserProfileBase):
    """Schema for user profile response"""

    id: int
    user_id: int
    avatar: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class AvatarUploadResponse(BaseModel):
    """Response after avatar upload"""

    avatar: str
    avatar_url: str
    message: str = "Avatar uploaded successfully"
