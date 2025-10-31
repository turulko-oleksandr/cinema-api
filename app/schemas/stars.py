from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class StarBase(BaseModel):
    name: str = Field(..., max_length=255)


class StarCreate(StarBase):
    pass


class StarUpdate(StarBase):
    name: Optional[str] = Field(None, max_length=255)


class StarResponse(StarBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
