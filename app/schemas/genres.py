from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class GenreBase(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


class GenreCreate(GenreBase):
    pass


class GenreUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)

    model_config = ConfigDict(from_attributes=True)


class GenreResponse(GenreBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class GenreWithCountResponse(BaseModel):
    """Genre with movie count"""

    id: int
    name: str
    movie_count: int = Field(..., description="Number of movies in this genre")

    model_config = ConfigDict(from_attributes=True)
