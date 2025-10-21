from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DirectorBase(BaseModel):
    name: str = Field(..., max_length=255)


class DirectorCreate(DirectorBase):
    pass


class DirectorUpdate(DirectorBase):
    name: Optional[str] = Field(None, max_length=255)


class DirectorResponse(DirectorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

