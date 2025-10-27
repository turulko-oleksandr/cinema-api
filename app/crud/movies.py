from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple
from app.database.models.models import Movie, Genre, Director, Star, Certification
from app.schemas.movies import MovieCreate, MovieUpdate


async def create_movie(db: AsyncSession, movie: MovieCreate) -> Movie:
    """Create a new movie with relationships"""
    new_movie = Movie(
        name=movie.name,
        year=movie.year,
        time=movie.time,
        imdb=movie.imdb,
        votes=movie.votes,
        meta_score=movie.meta_score,
        gross=movie.gross,
        description=movie.description,
        price=movie.price,
        certification_id=movie.certification_id,
    )

    # Add genres
    if movie.genre_ids:
        stmt = select(Genre).where(Genre.id.in_(movie.genre_ids))
        result = await db.execute(stmt)
        genres = result.scalars().all()
        new_movie.genres = list(genres)

    # Add directors
    if movie.director_ids:
        stmt = select(Director).where(Director.id.in_(movie.director_ids))
        result = await db.execute(stmt)
        directors = result.scalars().all()
        new_movie.directors = list(directors)

    # Add stars
    if movie.star_ids:
        stmt = select(Star).where(Star.id.in_(movie.star_ids))
        result = await db.execute(stmt)
        stars = result.scalars().all()
        new_movie.stars = list(stars)

    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    # Eagerly load all relationships
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
        )
        .where(Movie.id == new_movie.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_movie(db: AsyncSession, movie_id: int) -> Optional[Movie]:
    """Get movie by ID with all relationships"""
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
        )
        .where(Movie.id == movie_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_movie_by_uuid(db: AsyncSession, movie_uuid: str) -> Optional[Movie]:
    """Get movie by UUID with all relationships"""
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
        )
        .where(Movie.uuid == movie_uuid)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_movies(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    order: str = "asc",
) -> Tuple[List[Movie], int]:
    """Get paginated movies with relationships"""
    # Count total
    count_stmt = select(func.count(Movie.id))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get movies
    stmt = select(Movie).options(
        selectinload(Movie.certification),
        selectinload(Movie.genres),
        selectinload(Movie.directors),
        selectinload(Movie.stars),
    )

    # Add sorting
    if hasattr(Movie, sort_by):
        order_column = getattr(Movie, sort_by)
        stmt = stmt.order_by(order_column.desc() if order == "desc" else order_column)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    movies = result.scalars().all()

    return list(movies), total


async def update_movie(
    db: AsyncSession, movie_id: int, movie_update: MovieUpdate
) -> Optional[Movie]:
    """Update movie"""
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
        )
        .where(Movie.id == movie_id)
    )
    result = await db.execute(stmt)
    existing_movie = result.scalar_one_or_none()

    if not existing_movie:
        return None

    # Update basic fields
    update_data = movie_update.model_dump(
        exclude_unset=True, exclude={"genre_ids", "director_ids", "star_ids"}
    )
    for field, value in update_data.items():
        setattr(existing_movie, field, value)

    # Update genres if provided
    if movie_update.genre_ids is not None:
        stmt = select(Genre).where(Genre.id.in_(movie_update.genre_ids))
        result = await db.execute(stmt)
        genres = result.scalars().all()
        existing_movie.genres = list(genres)

    # Update directors if provided
    if movie_update.director_ids is not None:
        stmt = select(Director).where(Director.id.in_(movie_update.director_ids))
        result = await db.execute(stmt)
        directors = result.scalars().all()
        existing_movie.directors = list(directors)

    # Update stars if provided
    if movie_update.star_ids is not None:
        stmt = select(Star).where(Star.id.in_(movie_update.star_ids))
        result = await db.execute(stmt)
        stars = result.scalars().all()
        existing_movie.stars = list(stars)

    await db.commit()
    await db.refresh(existing_movie)

    # Reload with relationships
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
        )
        .where(Movie.id == movie_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def delete_movie(db: AsyncSession, movie_id: int) -> bool:
    """Delete movie"""
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        return False

    await db.delete(movie)
    await db.commit()
    return True


async def search_movies(
    db: AsyncSession,
    query_text: str,
    search_in: List[str],
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[Movie], int]:
    """Search movies by text"""
    filters = []

    if "title" in search_in:
        filters.append(Movie.name.ilike(f"%{query_text}%"))
    if "description" in search_in:
        filters.append(Movie.description.ilike(f"%{query_text}%"))

    # Count total
    count_stmt = select(func.count(Movie.id)).where(or_(*filters))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get movies
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
        )
        .where(or_(*filters))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
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
) -> Tuple[List[Movie], int]:
    """Filter movies by multiple criteria"""
    filters = []

    if year_from:
        filters.append(Movie.year >= year_from)
    if year_to:
        filters.append(Movie.year <= year_to)
    if imdb_min:
        filters.append(Movie.imdb >= imdb_min)
    if imdb_max:
        filters.append(Movie.imdb <= imdb_max)
    if price_min:
        filters.append(Movie.price >= price_min)
    if price_max:
        filters.append(Movie.price <= price_max)
    if certification_ids:
        filters.append(Movie.certification_id.in_(certification_ids))

    # Count total
    count_stmt = select(func.count(Movie.id))
    if filters:
        count_stmt = count_stmt.where(and_(*filters))

    if genre_ids:
        count_stmt = count_stmt.join(Movie.genres).where(Genre.id.in_(genre_ids))

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get movies
    stmt = select(Movie).options(
        selectinload(Movie.certification),
        selectinload(Movie.genres),
        selectinload(Movie.directors),
        selectinload(Movie.stars),
    )

    if filters:
        stmt = stmt.where(and_(*filters))

    if genre_ids:
        stmt = stmt.join(Movie.genres).where(Genre.id.in_(genre_ids))

    # Add sorting
    if hasattr(Movie, sort_by):
        order_column = getattr(Movie, sort_by)
        stmt = stmt.order_by(order_column.desc() if order == "desc" else order_column)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    movies = result.scalars().all()

    return list(movies), total


async def get_movies_by_genre(
    db: AsyncSession,
    genre_id: int,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "id",
    order: str = "asc",
) -> Tuple[List[Movie], int]:
    """Get movies by genre"""
    # Count total
    count_stmt = (
        select(func.count(Movie.id)).join(Movie.genres).where(Genre.id == genre_id)
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Get movies
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
        )
        .join(Movie.genres)
        .where(Genre.id == genre_id)
    )

    # Add sorting
    if hasattr(Movie, sort_by):
        order_column = getattr(Movie, sort_by)
        stmt = stmt.order_by(order_column.desc() if order == "desc" else order_column)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    movies = result.scalars().all()

    return list(movies), total


async def get_trending_movies(db: AsyncSession, limit: int = 10) -> List[Movie]:
    """Get trending movies (by votes and rating)"""
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
        )
        .order_by(Movie.votes.desc(), Movie.imdb.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_new_releases(db: AsyncSession, limit: int = 20) -> List[Movie]:
    """Get new releases (by year)"""
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.certification),
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
        )
        .order_by(Movie.year.desc(), Movie.id.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
