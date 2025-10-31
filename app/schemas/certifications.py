from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class CertificationBase(BaseModel):
    name: str = Field(..., max_length=50)


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(CertificationBase):
    name: Optional[str] = Field(None, max_length=50)


class CertificationResponse(CertificationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
