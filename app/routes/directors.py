from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import get_directors, create_director, get_director, update_director, delete_director
from database.db_session import get_db
from schemas import DirectorResponse, DirectorCreate, DirectorUpdate

router = APIRouter(tags=["Directors"])


@router.get("/", response_model=List[DirectorResponse], status_code=200)
async def get_directors_endpoint(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=100, description="Maximum number of records to return"
    ),
):
    directors = await get_directors(db, skip, limit)
    return directors


@router.get("/{director_id}", response_model=DirectorResponse, status_code=200)
async def get_director_endpoint(director_id: int, db: AsyncSession = Depends(get_db)):
    director = await get_director(db, director_id)
    if director is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Director with ID {director_id} not found",
        )
    return director


@router.post("Director", response_model=DirectorResponse, status_code=201)
async def create_director_endpoint(
    director: DirectorCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        new_director = await create_director(db, director)
        return new_director
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating director: {str(e)}",
        )


@router.put("/{director_id}", response_model=DirectorResponse, status_code=200)
async def update_director_endpoint(
    director_id: int, director_update: DirectorUpdate, db: AsyncSession = Depends(get_db)
):
    updated_director = await update_director(db, director_id, director_update)
    if updated_director is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Director with ID {director_id} not found",
        )
    return updated_director


@router.delete("/{director_id}", response_model=DirectorResponse, status_code=200)
async def delete_director_endpoint(director_id: int, db: AsyncSession = Depends(get_db)):
    deleted_director = await delete_director(db, director_id)
    if deleted_director is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Director with ID {director_id} not found",
        )
    return deleted_director
