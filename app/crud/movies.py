from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from database.models.models import (
    Genre, Star, Director, Movie,
)
from schemas import (
    MovieCreate, MovieUpdate
)


async def create_movie(db: AsyncSession, movie: MovieCreate):
    movie_data = movie.model_dump(exclude={'genre_ids', 'director_ids', 'star_ids'})
    new_movie = Movie(**movie_data)

    # Add relationships
    if movie.genre_ids:
        result = await db.execute(select(Genre).where(Genre.id.in_(movie.genre_ids)))
        new_movie.genres = result.scalars().all()

    if movie.director_ids:
        result = await db.execute(select(Director).where(Director.id.in_(movie.director_ids)))
        new_movie.directors = result.scalars().all()

    if movie.star_ids:
        result = await db.execute(select(Star).where(Star.id.in_(movie.star_ids)))
        new_movie.stars = result.scalars().all()

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie


async def get_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
            selectinload(Movie.certification)
        )
        .where(Movie.id == movie_id)
    )
    return result.scalar_one_or_none()


async def get_movie_by_uuid(db: AsyncSession, movie_uuid: str):
    result = await db.execute(
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
            selectinload(Movie.certification)
        )
        .where(Movie.uuid == movie_uuid)
    )
    return result.scalar_one_or_none()


async def get_movies(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
            selectinload(Movie.certification)
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None

    movie_data = movie.model_dump(exclude_unset=True, exclude={'genre_ids', 'director_ids', 'star_ids'})
    for key, value in movie_data.items():
        setattr(db_movie, key, value)

    # Update relationships if provided
    if movie.genre_ids is not None:
        result = await db.execute(select(Genre).where(Genre.id.in_(movie.genre_ids)))
        db_movie.genres = result.scalars().all()

    if movie.director_ids is not None:
        result = await db.execute(select(Director).where(Director.id.in_(movie.director_ids)))
        db_movie.directors = result.scalars().all()

    if movie.star_ids is not None:
        result = await db.execute(select(Star).where(Star.id.in_(movie.star_ids)))
        db_movie.stars = result.scalars().all()

    await db.commit()
    await db.refresh(db_movie)
    return db_movie


async def delete_movie(db: AsyncSession, movie_id: int):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None

    await db.delete(db_movie)
    await db.commit()
    return db_movie
