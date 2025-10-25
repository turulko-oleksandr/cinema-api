from sqlalchemy import and_, or_
from typing import Optional, List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from app.database.models.models import (
    Genre,
    Star,
    Director,
    Movie,
)
from app.schemas import MovieCreate, MovieUpdate


async def create_movie(db: AsyncSession, movie_data: MovieCreate):
    existing = await db.execute(
        select(Movie).where(
            Movie.name == movie_data.name,
            Movie.year == movie_data.year,
            Movie.time == movie_data.time,
        )
    )
    if existing.scalar_one_or_none():
        raise IntegrityError("Movie already exists", params=None, orig=None)

    movie = Movie(
        **movie_data.model_dump(exclude={"genre_ids", "director_ids", "star_ids"})
    )
    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    if movie_data.genre_ids:
        genres = await db.execute(
            select(Genre).filter(Genre.id.in_(movie_data.genre_ids))
        )
        movie.genres = genres.scalars().all()

    if movie_data.director_ids:
        directors = await db.execute(
            select(Director).filter(Director.id.in_(movie_data.director_ids))
        )
        movie.directors = directors.scalars().all()

    if movie_data.star_ids:
        stars = await db.execute(select(Star).filter(Star.id.in_(movie_data.star_ids)))
        movie.stars = stars.scalars().all()

    await db.commit()

    result = await db.execute(
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
            selectinload(Movie.certification),
        )
        .filter(Movie.id == movie.id)
    )
    return result.scalar_one()


async def get_movie(db: AsyncSession, movie_id: int) -> Optional[Movie]:
    """Get movie by ID with all relationships"""
    query = (
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
            selectinload(Movie.certification),
        )
        .where(Movie.id == movie_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_movie_by_uuid(db: AsyncSession, movie_uuid: str):
    result = await db.execute(
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
            selectinload(Movie.certification),
        )
        .where(Movie.uuid == movie_uuid)
    )
    return result.scalar_one_or_none()


async def update_movie(db: AsyncSession, movie_id: int, movie: MovieUpdate):
    result = await db.execute(select(Movie).where(Movie.id == movie_id))
    db_movie = result.scalar_one_or_none()
    if not db_movie:
        return None

    movie_data = movie.model_dump(
        exclude_unset=True, exclude={"genre_ids", "director_ids", "star_ids"}
    )
    for key, value in movie_data.items():
        setattr(db_movie, key, value)

    if movie.genre_ids is not None:
        result = await db.execute(select(Genre).where(Genre.id.in_(movie.genre_ids)))
        db_movie.genres = result.scalars().all()

    if movie.director_ids is not None:
        result = await db.execute(
            select(Director).where(Director.id.in_(movie.director_ids))
        )
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


async def get_movies(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    order: str = "asc",
) -> tuple[List[Movie], int]:
    """
    Get movies with pagination and sorting

    Returns: (movies_list, total_count)
    """
    query = select(Movie).options(
        selectinload(Movie.genres),
        selectinload(Movie.certification),
    )

    sort_column = getattr(Movie, sort_by, Movie.id)
    if order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    count_query = select(func.count()).select_from(Movie)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    movies = result.scalars().all()

    return list(movies), total


async def search_movies(
    db: AsyncSession,
    query_text: str,
    search_in: List[str] = ["title", "description"],
    skip: int = 0,
    limit: int = 20,
) -> tuple[List[Movie], int]:
    """
    Search movies by title, description, actors, or directors

    Args:
        query_text: Search query
        search_in: Fields to search in (title, description, actors, directors)
        skip: Offset for pagination
        limit: Number of results

    Returns: (movies_list, total_count)
    """
    search_pattern = f"%{query_text.lower()}%"
    conditions = []

    if "title" in search_in:
        conditions.append(func.lower(Movie.name).like(search_pattern))

    if "description" in search_in:
        conditions.append(func.lower(Movie.description).like(search_pattern))

    query = select(Movie).options(
        selectinload(Movie.genres),
        selectinload(Movie.directors),
        selectinload(Movie.stars),
        selectinload(Movie.certification),
    )

    if "actors" in search_in:
        query = query.join(Movie.stars)
        conditions.append(func.lower(Star.name).like(search_pattern))

    if "directors" in search_in:
        query = query.join(Movie.directors)
        conditions.append(func.lower(Director.name).like(search_pattern))

    if conditions:
        query = query.where(or_(*conditions))

    query = query.distinct()

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    movies = result.scalars().all()

    return list(movies), total


async def filter_movies(
    db: AsyncSession,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    imdb_min: Optional[float] = None,
    imdb_max: Optional[float] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    genre_ids: Optional[List[int]] = None,
    certification_ids: Optional[List[int]] = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    order: str = "asc",
) -> tuple[List[Movie], int]:
    """
    Filter movies by multiple criteria

    Returns: (movies_list, total_count)
    """
    query = select(Movie).options(
        selectinload(Movie.genres),
        selectinload(Movie.certification),
    )

    conditions = []

    if year_from is not None:
        conditions.append(Movie.year >= year_from)
    if year_to is not None:
        conditions.append(Movie.year <= year_to)

    if imdb_min is not None:
        conditions.append(Movie.imdb >= imdb_min)
    if imdb_max is not None:
        conditions.append(Movie.imdb <= imdb_max)

    if price_min is not None:
        conditions.append(Movie.price >= price_min)
    if price_max is not None:
        conditions.append(Movie.price <= price_max)

    if certification_ids:
        conditions.append(Movie.certification_id.in_(certification_ids))

    if genre_ids:
        query = query.join(Movie.genres).where(Genre.id.in_(genre_ids))

    if conditions:
        query = query.where(and_(*conditions))

    query = query.distinct()

    sort_column = getattr(Movie, sort_by, Movie.id)
    if order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    movies = result.scalars().all()

    return list(movies), total


async def filter_movies(
    db: AsyncSession,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    imdb_min: Optional[float] = None,
    imdb_max: Optional[float] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    genre_ids: Optional[List[int]] = None,
    certification_ids: Optional[List[int]] = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    order: str = "asc",
) -> tuple[List[Movie], int]:
    """
    Filter movies by multiple criteria

    Returns: (movies_list, total_count)
    """
    query = select(Movie).options(
        selectinload(Movie.genres),
        selectinload(Movie.certification),
    )

    conditions = []

    if year_from is not None:
        conditions.append(Movie.year >= year_from)
    if year_to is not None:
        conditions.append(Movie.year <= year_to)

    if imdb_min is not None:
        conditions.append(Movie.imdb >= imdb_min)
    if imdb_max is not None:
        conditions.append(Movie.imdb <= imdb_max)

    if price_min is not None:
        conditions.append(Movie.price >= price_min)
    if price_max is not None:
        conditions.append(Movie.price <= price_max)

    if certification_ids:
        conditions.append(Movie.certification_id.in_(certification_ids))

    if genre_ids:
        query = query.join(Movie.genres).where(Genre.id.in_(genre_ids))

    if conditions:
        query = query.where(and_(*conditions))

    query = query.distinct()

    sort_column = getattr(Movie, sort_by, Movie.id)
    if order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    movies = result.scalars().all()

    return list(movies), total


async def get_movies_by_genre(
    db: AsyncSession,
    genre_id: int,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    order: str = "asc",
) -> tuple[List[Movie], int]:
    """
    Get movies filtered by specific genre

    Returns: (movies_list, total_count)
    """
    query = (
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.certification),
        )
        .join(Movie.genres)
        .where(Genre.id == genre_id)
    )

    sort_column = getattr(Movie, sort_by, Movie.id)
    if order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    movies = result.scalars().all()

    return list(movies), total


async def get_trending_movies(db: AsyncSession, limit: int = 10) -> List[Movie]:
    """
    Get trending movies (sorted by votes and IMDB rating)
    """
    query = (
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.certification),
        )
        .order_by(Movie.votes.desc(), Movie.imdb.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_new_releases(db: AsyncSession, limit: int = 20) -> List[Movie]:
    """
    Get newest movies (sorted by year)
    """
    query = (
        select(Movie)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.certification),
        )
        .order_by(Movie.year.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return list(result.scalars().all())
