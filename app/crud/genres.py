from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.models import Genre, Movie
from schemas.genres import GenreCreate, GenreUpdate


async def create_genre(db: AsyncSession, genre: GenreCreate):
    new_genre = Genre(**genre.model_dump())
    db.add(new_genre)
    await db.commit()
    await db.refresh(new_genre)
    return new_genre


async def get_genre(db: AsyncSession, genre_id: int):
    result = await db.execute(
        select(Genre).options(selectinload(Genre.movies)).where(Genre.id == genre_id)
    )
    return result.scalar_one_or_none()


async def get_genres(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Genre).offset(skip).limit(limit))
    return result.scalars().all()


async def update_genre(db: AsyncSession, genre_id: int, genre: GenreUpdate):
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    db_genre = result.scalar_one_or_none()
    if not db_genre:
        return None

    for key, value in genre.model_dump(exclude_unset=True).items():
        setattr(db_genre, key, value)

    await db.commit()
    await db.refresh(db_genre)
    return db_genre


async def delete_genre(db: AsyncSession, genre_id: int):
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    db_genre = result.scalar_one_or_none()
    if not db_genre:
        return None

    await db.delete(db_genre)
    await db.commit()
    return db_genre


async def get_genres_with_count(db: AsyncSession) -> List[dict]:
    """
    Get all genres with movie count

    Returns: [{id, name, movie_count}]
    """
    query = (
        select(
            Genre.id,
            Genre.name,
            func.count(Movie.id).label("movie_count"),
        )
        .outerjoin(Genre.movies)
        .group_by(Genre.id, Genre.name)
        .order_by(Genre.name)
    )

    result = await db.execute(query)
    genres = result.all()

    return [
        {"id": genre.id, "name": genre.name, "movie_count": genre.movie_count}
        for genre in genres
    ]
