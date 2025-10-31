from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.schemas.genres import GenreResponse
from app.schemas.certifications import CertificationResponse
from app.schemas.directors import DirectorResponse
from app.schemas.stars import StarResponse


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


class PaginatedMoviesResponse(BaseModel):
    """Paginated response for movies list"""

    items: List[MovieListResponse]
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of skipped items")
    limit: int = Field(..., description="Items per page")

    model_config = ConfigDict(from_attributes=True)


class MovieSearchParams(BaseModel):
    """Parameters for movie search"""

    query: str = Field(..., min_length=1, description="Search query")
    search_in: List[str] = Field(
        default=["title", "description"],
        description="Fields to search in",
    )
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class MovieFilterParams(BaseModel):
    """Parameters for movie filtering"""

    year_from: Optional[int] = Field(None, ge=1900)
    year_to: Optional[int] = Field(None, le=2100)
    imdb_min: Optional[float] = Field(None, ge=0, le=10)
    imdb_max: Optional[float] = Field(None, ge=0, le=10)
    price_min: Optional[Decimal] = Field(None, ge=0)
    price_max: Optional[Decimal] = Field(None, ge=0)
    genre_ids: Optional[List[int]] = None
    certification_ids: Optional[List[int]] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="id")
    order: str = Field(default="asc", pattern="^(asc|desc)$")


class MovieSortParams(BaseModel):
    """Parameters for movie sorting"""

    sort_by: str = Field(
        default="id",
        description="Field to sort by (id, name, year, imdb, price, votes)",
    )
    order: str = Field(default="asc", pattern="^(asc|desc)$")
