from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.models import Certification
from schemas.certifications import CertificationCreate, CertificationUpdate


async def create_certification(db: AsyncSession, certification: CertificationCreate):
    new_certification = Certification(**certification.model_dump())
    db.add(new_certification)
    await db.commit()
    await db.refresh(new_certification)
    return new_certification


async def get_certification(db: AsyncSession, certification_id: int):
    result = await db.execute(
        select(Certification)
        .options(selectinload(Certification.movies))
        .where(Certification.id == certification_id)
    )
    return result.scalar_one_or_none()


async def get_certifications(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Certification).offset(skip).limit(limit))
    return result.scalars().all()


async def update_certification(db: AsyncSession, certification_id: int, certification: CertificationUpdate):
    result = await db.execute(select(Certification).where(Certification.id == certification_id))
    db_certification = result.scalar_one_or_none()
    if not db_certification:
        return None

    for key, value in certification.model_dump(exclude_unset=True).items():
        setattr(db_certification, key, value)

    await db.commit()
    await db.refresh(db_certification)
    return db_certification


async def delete_certification(db: AsyncSession, certification_id: int):
    result = await db.execute(select(Certification).where(Certification.id == certification_id))
    db_certification = result.scalar_one_or_none()
    if not db_certification:
        return None

    await db.delete(db_certification)
    await db.commit()
    return db_certification

