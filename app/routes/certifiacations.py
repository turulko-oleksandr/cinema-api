from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud import (
    get_certifications,
    create_certification,
    get_certification,
    update_certification,
    delete_certification,
)
from database.db_session import get_db
from database.models import User
from schemas import CertificationResponse, CertificationCreate, CertificationUpdate
from services.role_manager import require_moderator

router = APIRouter(tags=["Certifications"])


@router.get("/", response_model=List[CertificationResponse], status_code=200)
async def get_certifications_endpoint(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=100, description="Maximum number of records to return"
    ),
):
    certifications = await get_certifications(db, skip, limit)
    return certifications


@router.get(
    "/{certification_id}", response_model=CertificationResponse, status_code=200
)
async def get_certification_endpoint(
    certification_id: int, db: AsyncSession = Depends(get_db)
):
    certification = await get_certification(db, certification_id)
    if certification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification with ID {certification_id} not found",
        )
    return certification


@router.post("/", response_model=CertificationResponse, status_code=201)
async def create_certification_endpoint(
    certification: CertificationCreate,
    user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_certification = await create_certification(db, certification)
        return new_certification
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating certification: {str(e)}",
        )


@router.patch(
    "/{certification_id}", response_model=CertificationResponse, status_code=200
)
async def update_certification_endpoint(
    certification_id: int,
    certification_update: CertificationUpdate,
    user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    updated_certification = await update_certification(
        db, certification_id, certification_update
    )
    if updated_certification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification with ID {certification_id} not found",
        )
    return updated_certification


@router.delete(
    "/{certification_id}", response_model=CertificationResponse, status_code=200
)
async def delete_certification_endpoint(
    certification_id: int,
    user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    deleted_certification = await delete_certification(db, certification_id)
    if deleted_certification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification with ID {certification_id} not found",
        )
    return deleted_certification
