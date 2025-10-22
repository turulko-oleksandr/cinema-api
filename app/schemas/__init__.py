from .movies import (
    MovieBase,
    MovieCreate,
    MovieUpdate,
    MovieResponse,
    MovieListResponse,
    PaginatedMoviesResponse,
    MovieSearchParams,
    MovieFilterParams,
    MovieSortParams,
)
from .genres import (
    GenreBase,
    GenreCreate,
    GenreUpdate,
    GenreResponse,
    GenreWithCountResponse,
)
from .certifications import (
    CertificationBase,
    CertificationCreate,
    CertificationUpdate,
    CertificationResponse,
)
from .stars import StarBase, StarCreate, StarUpdate, StarResponse
from .directors import DirectorBase, DirectorCreate, DirectorUpdate, DirectorResponse

__all__ = [
    # Genre schemas
    "GenreBase",
    "GenreCreate",
    "GenreUpdate",
    "GenreResponse",
    # Star schemas
    "StarBase",
    "StarCreate",
    "StarUpdate",
    "StarResponse",
    # Director schemas
    "DirectorBase",
    "DirectorCreate",
    "DirectorUpdate",
    "DirectorResponse",
    # Certification schemas
    "CertificationBase",
    "CertificationCreate",
    "CertificationUpdate",
    "CertificationResponse",
    # Movie schemas
    "MovieBase",
    "MovieCreate",
    "MovieUpdate",
    "MovieResponse",
    "MovieListResponse",
]
