from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional

from config import get_jwt_auth_manager
from database import get_db, User, UserGroupEnum
from services.interfaces import JWTAuthManagerInterface
from exceptions import TokenExpiredError, InvalidTokenError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> User:
    """
    Dependency to get the current authorized user

    Args:
        credentials: Bearer token from the Authorization header
        db: Database session
        jwt_manager: JWT manager for decoding tokens

    Returns:
        The current user

    Raises:
        HTTPException 401: If the token is invalid
        HTTPException 403: If the user is not active
    """
    token = credentials.credentials

    try:
        # Decode the access token
        decoded = jwt_manager.decode_access_token(token)
        user_id = decoded.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get the user from the DB with relationships loaded
    stmt = select(User).options(selectinload(User.group)).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if the user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated",
        )

    return user


# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================


class RoleChecker:
    """
    Dependency class for checking user roles

    Usage:
        @router.post("/movies/", dependencies=[Depends(require_moderator)])
        async def create_movie(...):
            ...
    """

    def __init__(self, allowed_roles: list[UserGroupEnum]):
        """
        Args:
            allowed_roles: List of allowed roles for access
        """
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
    ) -> User:
        """
        Checks if the user has the required role

        Args:
            current_user: The current user

        Returns:
            User if access is granted

        Raises:
            HTTPException 403: If the user does not have the required role
        """
        # Get the user's role
        user_role = current_user.group.name

        # Check if the role is in the list of allowed roles
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {[role.value for role in self.allowed_roles]}",
            )

        return current_user


require_user = RoleChecker(
    allowed_roles=[UserGroupEnum.USER, UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN]
)

require_moderator = RoleChecker(
    allowed_roles=[UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN]
)

# Admin only
require_admin = RoleChecker(allowed_roles=[UserGroupEnum.ADMIN])


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
    jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
) -> Optional[User]:
    """
    Dependency for optionally getting the current user

    Does not raise an error if the token is missing - simply returns None

    Useful for endpoints with different behavior for authorized/anonymous users

    Args:
        credentials: Optional bearer token
        db: Database session
        jwt_manager: JWT manager

    Returns:
        User if authorized, None otherwise
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        decoded = jwt_manager.decode_access_token(token)
        user_id = decoded.get("user_id")

        if user_id is None:
            return None

        stmt = select(User).options(selectinload(User.group)).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user and user.is_active:
            return user

        return None

    except (TokenExpiredError, InvalidTokenError):
        return None


def check_user_role(user: User, required_role: UserGroupEnum) -> bool:
    """
    Utility function to check if a user has a specific role

    Args:
        user: The user to check
        required_role: The required role

    Returns:
        True if the user has the necessary role
    """
    return user.group.name == required_role


def check_user_has_any_role(user: User, roles: list[UserGroupEnum]) -> bool:
    """
    Utility function to check if a user has any of the given roles

    Args:
        user: The user to check
        roles: List of allowed roles

    Returns:
        True if the user has one of the roles
    """
    return user.group.name in roles
