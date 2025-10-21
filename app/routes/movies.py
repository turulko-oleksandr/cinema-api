# routes/movies.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from database.db_session import get_db
from crud.movies import (
    create_movie,
    get_movie,
    get_movie_by_uuid,
    get_movies,
    update_movie,
    delete_movie,
)
from schemas.movies import (
    MovieCreate,
    MovieUpdate,
    MovieResponse,
    MovieListResponse,
)

router = APIRouter()


@router.post(
    "/",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new movie"
)
async def create_movie_endpoint(
        movie: MovieCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    Create a new movie with the following information:

    - **name**: Movie title
    - **year**: Release year
    - **time**: Duration in minutes
    - **imdb**: IMDB rating (0-10)
    - **votes**: Number of votes
    - **meta_score**: Metacritic score (optional)
    - **gross**: Box office gross (optional)
    - **description**: Movie description
    - **price**: Movie price
    - **certification_id**: Certification ID
    - **genre_ids**: List of genre IDs
    - **director_ids**: List of director IDs
    - **star_ids**: List of star IDs
    """
    try:
        new_movie = await create_movie(db, movie)
        return new_movie
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating movie: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[MovieListResponse],
    summary="Get all movies"
)
async def get_movies_endpoint(
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
        db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of all movies with pagination.
    """
    movies = await get_movies(db, skip=skip, limit=limit)
    return movies


@router.get(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Get movie by ID"
)
async def get_movie_endpoint(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific movie by its ID.
    """
    movie = await get_movie(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found"
        )
    return movie


@router.get(
    "/uuid/{movie_uuid}",
    response_model=MovieResponse,
    summary="Get movie by UUID"
)
async def get_movie_by_uuid_endpoint(
        movie_uuid: UUID,
        db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific movie by its UUID.
    """
    movie = await get_movie_by_uuid(db, str(movie_uuid))
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with uuid {movie_uuid} not found"
        )
    return movie


@router.put(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Update movie"
)
async def update_movie_endpoint(
        movie_id: int,
        movie: MovieUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    Update a movie's information.

    Only provided fields will be updated.
    """
    updated_movie = await update_movie(db, movie_id, movie)
    if not updated_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found"
        )
    return updated_movie


@router.patch(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Partially update movie"
)
async def patch_movie_endpoint(
        movie_id: int,
        movie: MovieUpdate,
        db: AsyncSession = Depends(get_db)
):
    """
    Partially update a movie's information.

    Only provided fields will be updated.
    """
    updated_movie = await update_movie(db, movie_id, movie)
    if not updated_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found"
        )
    return updated_movie


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete movie"
)
async def delete_movie_endpoint(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    """
    Delete a movie by its ID.
    """
    deleted_movie = await delete_movie(db, movie_id)
    if not deleted_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found"
        )
    return None