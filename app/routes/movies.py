from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID

from database import User
from database.db_session import get_db
from crud.movies import (
    create_movie,
    get_movie,
    get_movie_by_uuid,
    get_movies,
    update_movie,
    delete_movie,
    search_movies,
    filter_movies,
    get_movies_by_genre,
    get_trending_movies,
    get_new_releases,
)
from schemas.movies import (
    MovieCreate,
    MovieUpdate,
    MovieResponse,
    MovieListResponse,
    PaginatedMoviesResponse,
)
from services.role_manager import get_current_user_optional, require_moderator

router = APIRouter()


@router.post(
    "/",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new movie",
)
async def create_movie_endpoint(
    movie: MovieCreate,
    user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Create a new movie with all related information."""
    try:
        new_movie = await create_movie(db, movie)
        return new_movie
    except IntegrityError as e:
        await db.rollback()
        if "uq_movie_identity" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Movie '{movie.name}' ({movie.year}, {movie.time} min) already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating movie: {str(e)}",
        )


@router.get(
    "/",
    response_model=PaginatedMoviesResponse,
    summary="Get all movies with pagination",
)
async def get_movies_endpoint(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    sort_by: str = Query("id", description="Field to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a paginated list of movies.

    - **skip**: Offset for pagination
    - **limit**: Number of movies per page
    - **sort_by**: Field to sort by (id, name, year, imdb, price, etc.)
    - **order**: Sort order (asc or desc)
    """
    movies, total = await get_movies(
        db, skip=skip, limit=limit, sort_by=sort_by, order=order
    )

    return PaginatedMoviesResponse(
        items=movies,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/search/query",
    response_model=PaginatedMoviesResponse,
    summary="Search movies",
)
async def search_movies_endpoint(
    q: str = Query(..., min_length=1, description="Search query"),
    search_in: List[str] = Query(
        ["title", "description"],
        description="Fields to search in: title, description, actors, directors",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Search movies by title, description, actors, or directors.

    - **q**: Search query string
    - **search_in**: List of fields to search (title, description, actors, directors)
    """
    movies, total = await search_movies(
        db, query_text=q, search_in=search_in, skip=skip, limit=limit
    )

    return PaginatedMoviesResponse(
        items=movies,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/filter/advanced",
    response_model=PaginatedMoviesResponse,
    summary="Filter movies by multiple criteria",
)
async def filter_movies_endpoint(
    year_from: Optional[int] = Query(None, ge=1900, le=2100),
    year_to: Optional[int] = Query(None, ge=1900, le=2100),
    imdb_min: Optional[float] = Query(None, ge=0, le=10),
    imdb_max: Optional[float] = Query(None, ge=0, le=10),
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    genre_ids: Optional[List[int]] = Query(None),
    certification_ids: Optional[List[int]] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("id"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Filter movies by multiple criteria.

    - **year_from/year_to**: Year range filter
    - **imdb_min/imdb_max**: IMDB rating range
    - **price_min/price_max**: Price range
    - **genre_ids**: List of genre IDs
    - **certification_ids**: List of certification IDs
    """
    movies, total = await filter_movies(
        db,
        year_from=year_from,
        year_to=year_to,
        imdb_min=imdb_min,
        imdb_max=imdb_max,
        price_min=price_min,
        price_max=price_max,
        genre_ids=genre_ids,
        certification_ids=certification_ids,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )

    return PaginatedMoviesResponse(
        items=movies,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/genre/{genre_id}",
    response_model=PaginatedMoviesResponse,
    summary="Get movies by genre",
)
async def get_movies_by_genre_endpoint(
    genre_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("id"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all movies filtered by a specific genre.

    - **genre_id**: ID of the genre to filter by
    """
    movies, total = await get_movies_by_genre(
        db,
        genre_id=genre_id,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No movies found for genre id {genre_id}",
        )

    return PaginatedMoviesResponse(
        items=movies,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Get movie by ID",
)
async def get_movie_endpoint(movie_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific movie by its ID with all relationships."""
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found",
        )
    return movie


@router.get(
    "/uuid/{movie_uuid}",
    response_model=MovieResponse,
    summary="Get movie by UUID",
)
async def get_movie_by_uuid_endpoint(
    movie_uuid: UUID, db: AsyncSession = Depends(get_db)
):
    """Retrieve a specific movie by its UUID."""
    movie = await get_movie_by_uuid(db, str(movie_uuid))
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with uuid {movie_uuid} not found",
        )
    return movie


@router.patch(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Update movie",
)
async def update_movie_endpoint(
    movie_id: int,
    movie: MovieUpdate,
    user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a movie's information.
    Only provided fields will be updated.
    """
    try:
        updated_movie = await update_movie(db, movie_id, movie)
        if not updated_movie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Movie with id {movie_id} not found",
            )
        return updated_movie
    except IntegrityError as e:
        await db.rollback()
        if "uq_movie_identity" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Movie with these parameters already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}",
        )


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete movie",
)
async def delete_movie_endpoint(
    movie_id: int,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Delete a movie by its ID."""
    deleted = await delete_movie(db, movie_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found",
        )
    return None


@router.get(
    "/special/trending",
    response_model=List[MovieListResponse],
    summary="Get trending movies",
)
async def get_trending_movies_endpoint(
    limit: int = Query(10, ge=1, le=50, description="Number of trending movies"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trending movies sorted by votes and IMDB rating.

    - **limit**: Number of movies to return (default: 10)
    """
    movies = await get_trending_movies(db, limit=limit)
    return movies


@router.get(
    "/special/new-releases",
    response_model=List[MovieListResponse],
    summary="Get new releases",
)
async def get_new_releases_endpoint(
    limit: int = Query(20, ge=1, le=50, description="Number of new releases"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get newest movies sorted by release year.

    - **limit**: Number of movies to return (default: 20)
    """
    movies = await get_new_releases(db, limit=limit)
    return movies
