from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models.models import Director
from ..schemas.directors import DirectorCreate, DirectorUpdate


async def create_director(db: AsyncSession, director: DirectorCreate):
    new_director = Director(**director.model_dump())
    db.add(new_director)
    await db.commit()
    await db.refresh(new_director)
    return new_director


async def get_director(db: AsyncSession, director_id: int):
    result = await db.execute(
        select(Director)
        .options(selectinload(Director.movies))
        .where(Director.id == director_id)
    )
    return result.scalar_one_or_none()


async def get_directors(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Director).offset(skip).limit(limit))
    return result.scalars().all()


async def update_director(db: AsyncSession, director_id: int, director: DirectorUpdate):
    result = await db.execute(select(Director).where(Director.id == director_id))
    db_director = result.scalar_one_or_none()
    if not db_director:
        return None

    for key, value in director.model_dump(exclude_unset=True).items():
        setattr(db_director, key, value)

    await db.commit()
    await db.refresh(db_director)
    return db_director


async def delete_director(db: AsyncSession, director_id: int):
    result = await db.execute(select(Director).where(Director.id == director_id))
    db_director = result.scalar_one_or_none()
    if not db_director:
        return None

    await db.delete(db_director)
    await db.commit()
    return db_director
