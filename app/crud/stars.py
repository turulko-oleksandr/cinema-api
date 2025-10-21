from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.models import Star
from schemas.stars import StarCreate, StarUpdate


async def create_star(db: AsyncSession, star: StarCreate):
    new_star = Star(**star.model_dump())
    db.add(new_star)
    await db.commit()
    await db.refresh(new_star)
    return new_star


async def get_star(db: AsyncSession, star_id: int):
    result = await db.execute(
        select(Star).options(selectinload(Star.movies)).where(Star.id == star_id)
    )
    return result.scalar_one_or_none()


async def get_stars(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Star).offset(skip).limit(limit))
    return result.scalars().all()


async def update_star(db: AsyncSession, star_id: int, star: StarUpdate):
    result = await db.execute(select(Star).where(Star.id == star_id))
    db_star = result.scalar_one_or_none()
    if not db_star:
        return None

    for key, value in star.model_dump(exclude_unset=True).items():
        setattr(db_star, key, value)

    await db.commit()
    await db.refresh(db_star)
    return db_star


async def delete_star(db: AsyncSession, star_id: int):
    result = await db.execute(select(Star).where(Star.id == star_id))
    db_star = result.scalar_one_or_none()
    if not db_star:
        return None

    await db.delete(db_star)
    await db.commit()
    return db_star
