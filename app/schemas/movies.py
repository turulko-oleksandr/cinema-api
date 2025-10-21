from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from schemas.genres import GenreResponse
from schemas.certifications import CertificationResponse
from schemas.directors import DirectorResponse
from schemas.stars import StarResponse


class MovieBase(BaseModel):
    name: str = Field(..., max_length=500)
    year: int = Field(..., ge=1800, le=2100)
    time: int = Field(..., gt=0, description="Duration in minutes")
    imdb: Decimal = Field(..., ge=0, le=10, decimal_places=1)
    votes: int = Field(..., ge=0)
    meta_score: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=1)
    gross: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    description: str
    price: Decimal = Field(..., ge=0, decimal_places=2)
    certification_id: int


class MovieCreate(MovieBase):
    genre_ids: List[int] = Field(default_factory=list)
    director_ids: List[int] = Field(default_factory=list)
    star_ids: List[int] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    year: Optional[int] = Field(None, ge=1800, le=2100)
    time: Optional[int] = Field(None, gt=0)
    imdb: Optional[Decimal] = Field(None, ge=0, le=10, decimal_places=1)
    votes: Optional[int] = Field(None, ge=0)
    meta_score: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=1)
    gross: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    certification_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None


class MovieResponse(MovieBase):
    id: int
    uuid: UUID
    certification: CertificationResponse
    genres: List[GenreResponse] = []
    directors: List[DirectorResponse] = []
    stars: List[StarResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MovieListResponse(BaseModel):
    id: int
    uuid: UUID
    name: str
    year: int
    time: int
    imdb: Decimal
    votes: int
    price: Decimal
    certification: CertificationResponse
    genres: List[GenreResponse] = []

    model_config = ConfigDict(from_attributes=True)
