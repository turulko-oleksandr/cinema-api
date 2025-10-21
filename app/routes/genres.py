from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import get_genres, create_genre, get_genre, update_genre, delete_genre
from database.db_session import get_db
from schemas import GenreResponse, GenreCreate, GenreUpdate

router = APIRouter(tags=["Genres"])


@router.get("/", response_model=List[GenreResponse], status_code=200)
async def get_genres_endpoint(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=100, description="Maximum number of records to return"
    ),
):
    genres = await get_genres(db, skip, limit)
    return genres


@router.get("/{genre_id}", response_model=GenreResponse, status_code=200)
async def get_genre_endpoint(genre_id: int, db: AsyncSession = Depends(get_db)):
    genre = await get_genre(db, genre_id)
    if genre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Genre with ID {genre_id} not found",
        )
    return genre


@router.post("/", response_model=GenreResponse, status_code=201)
async def create_genre_endpoint(
    genre: GenreCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        new_genre = await create_genre(db, genre)
        return new_genre
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating genre: {str(e)}",
        )


@router.patch("/{genre_id}", response_model=GenreResponse, status_code=200)
async def update_genre_endpoint(
    genre_id: int, genre_update: GenreUpdate, db: AsyncSession = Depends(get_db)
):
    updated_genre = await update_genre(db, genre_id, genre_update)
    if updated_genre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Genre with ID {genre_id} not found",
        )
    return updated_genre


@router.delete("/{genre_id}", response_model=GenreResponse, status_code=200)
async def delete_genre_endpoint(genre_id: int, db: AsyncSession = Depends(get_db)):
    deleted_genre = await delete_genre(db, genre_id)
    if deleted_genre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Genre with ID {genre_id} not found",
        )
    return deleted_genre

