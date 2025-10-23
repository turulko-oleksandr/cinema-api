import os
from functools import lru_cache
from fastapi import Depends

from .settings import TestingSettings, Settings, BaseAppSettings
from services.interfaces import JWTAuthManagerInterface
from services.token_manager import JWTAuthManager


@lru_cache()
def get_settings() -> BaseAppSettings:
    if os.getenv("ENVIRONMENT") == "test":
        return TestingSettings()
    return Settings()


def get_jwt_auth_manager(
    settings: BaseAppSettings = Depends(get_settings),
) -> JWTAuthManagerInterface:
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )
