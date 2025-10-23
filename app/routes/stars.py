from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import get_stars, create_star, get_star, update_star, delete_star
from database import User
from database.db_session import get_db
from schemas import StarResponse, StarCreate, StarUpdate
from services.role_manager import require_moderator

router = APIRouter(tags=["Stars"])


@router.get("/", response_model=List[StarResponse], status_code=200)
async def get_stars_endpoint(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=100, description="Maximum number of records to return"
    ),
):
    stars = await get_stars(db, skip, limit)
    return stars


@router.get("/{star_id}", response_model=StarResponse, status_code=200)
async def get_star_endpoint(star_id: int, db: AsyncSession = Depends(get_db)):
    star = await get_star(db, star_id)
    if star is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Star with ID {star_id} not found",
        )
    return star


@router.post("/", response_model=StarResponse, status_code=201)
async def create_star_endpoint(
    star: StarCreate,
    user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_star = await create_star(db, star)
        return new_star
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating star: {str(e)}",
        )


@router.patch("/{star_id}", response_model=StarResponse, status_code=200)
async def update_star_endpoint(
    star_id: int,
    star_update: StarUpdate,
    user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    updated_star = await update_star(db, star_id, star_update)
    if updated_star is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Star with ID {star_id} not found",
        )
    return updated_star


@router.delete("/{star_id}", response_model=StarResponse, status_code=200)
async def delete_star_endpoint(
    star_id: int,
    user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    deleted_star = await delete_star(db, star_id)
    if deleted_star is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Star with ID {star_id} not found",
        )
    return deleted_star
