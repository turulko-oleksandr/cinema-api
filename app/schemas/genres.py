from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class GenreBase(BaseModel):
    name: str = Field(..., max_length=100)


class GenreCreate(GenreBase):
    pass


class GenreUpdate(GenreBase):
    name: Optional[str] = Field(None, max_length=100)


class GenreResponse(GenreBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
