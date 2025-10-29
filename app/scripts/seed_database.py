"""
Database seeding script for Cinema API
Populates database with test data for development and testing purposes
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload

from ..config.dependencies import get_settings
from ..database.models.models import (
    Base,
    User,
    UserGroup,
    UserProfile,
    UserGroupEnum,
    GenderEnum,
    Genre,
    Star,
    Director,
    Certification,
    Movie,
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatusEnum,
    Payment,
    PaymentItem,
    PaymentStatusEnum,
)
from app.services.passwords import hash_password

settings = get_settings()

# Create async engine for seeding
engine = create_async_engine(settings.ASYNC_PGSQL_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ============================================================================
# SEED DATA
# ============================================================================

GENRES_DATA = [
    "Action",
    "Adventure",
    "Animation",
    "Biography",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Family",
    "Fantasy",
    "Film-Noir",
    "History",
    "Horror",
    "Music",
    "Musical",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Sport",
    "Thriller",
    "War",
    "Western",
]

CERTIFICATIONS_DATA = ["G", "PG", "PG-13", "R", "NC-17", "U", "UA", "A", "Not Rated"]

DIRECTORS_DATA = [
    "Christopher Nolan",
    "Steven Spielberg",
    "Martin Scorsese",
    "Quentin Tarantino",
    "Francis Ford Coppola",
    "James Cameron",
    "Ridley Scott",
    "Peter Jackson",
    "David Fincher",
    "Wes Anderson",
    "Denis Villeneuve",
    "Greta Gerwig",
    "Jordan Peele",
    "Bong Joon-ho",
    "Guillermo del Toro",
    "Edgar Wright",
    "Damien Chazelle",
    "Rian Johnson",
    "Taika Waititi",
    "Sam Mendes",
]

STARS_DATA = [
    "Leonardo DiCaprio",
    "Tom Hanks",
    "Meryl Streep",
    "Robert De Niro",
    "Al Pacino",
    "Brad Pitt",
    "Johnny Depp",
    "Christian Bale",
    "Scarlett Johansson",
    "Natalie Portman",
    "Cate Blanchett",
    "Morgan Freeman",
    "Denzel Washington",
    "Samuel L. Jackson",
    "Matt Damon",
    "Jennifer Lawrence",
    "Ryan Gosling",
    "Emma Stone",
    "Timothée Chalamet",
    "Margot Robbie",
    "Tom Cruise",
    "Will Smith",
    "Keanu Reeves",
    "Hugh Jackman",
    "Chris Hemsworth",
]

MOVIES_DATA = [
    {
        "name": "The Shawshank Redemption",
        "year": 1994,
        "time": 142,
        "imdb": 9.3,
        "votes": 2800000,
        "meta_score": 82,
        "gross": 28341469,
        "description": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
        "certification": "R",
        "genres": ["Drama"],
        "directors": ["Frank Darabont"],
        "stars": ["Tim Robbins", "Morgan Freeman"],
    },
    {
        "name": "The Godfather",
        "year": 1972,
        "time": 175,
        "imdb": 9.2,
        "votes": 1900000,
        "meta_score": 100,
        "gross": 134966411,
        "description": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
        "certification": "R",
        "genres": ["Crime", "Drama"],
        "directors": ["Francis Ford Coppola"],
        "stars": ["Marlon Brando", "Al Pacino"],
    },
    {
        "name": "The Dark Knight",
        "year": 2008,
        "time": 152,
        "imdb": 9.0,
        "votes": 2700000,
        "meta_score": 84,
        "gross": 534858444,
        "description": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
        "certification": "PG-13",
        "genres": ["Action", "Crime", "Drama"],
        "directors": ["Christopher Nolan"],
        "stars": ["Christian Bale", "Heath Ledger"],
    },
    {
        "name": "Inception",
        "year": 2010,
        "time": 148,
        "imdb": 8.8,
        "votes": 2400000,
        "meta_score": 74,
        "gross": 292576195,
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
        "certification": "PG-13",
        "genres": ["Action", "Sci-Fi", "Thriller"],
        "directors": ["Christopher Nolan"],
        "stars": ["Leonardo DiCaprio", "Tom Hardy"],
    },
    {
        "name": "Pulp Fiction",
        "year": 1994,
        "time": 154,
        "imdb": 8.9,
        "votes": 2100000,
        "meta_score": 94,
        "gross": 107928762,
        "description": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
        "certification": "R",
        "genres": ["Crime", "Drama"],
        "directors": ["Quentin Tarantino"],
        "stars": ["John Travolta", "Samuel L. Jackson"],
    },
    {
        "name": "Forrest Gump",
        "year": 1994,
        "time": 142,
        "imdb": 8.8,
        "votes": 2200000,
        "meta_score": 82,
        "gross": 330455270,
        "description": "The presidencies of Kennedy and Johnson, the Vietnam War, and other historical events unfold from the perspective of an Alabama man with an IQ of 75.",
        "certification": "PG-13",
        "genres": ["Drama", "Romance"],
        "directors": ["Robert Zemeckis"],
        "stars": ["Tom Hanks", "Robin Wright"],
    },
    {
        "name": "The Matrix",
        "year": 1999,
        "time": 136,
        "imdb": 8.7,
        "votes": 1900000,
        "meta_score": 73,
        "gross": 171479930,
        "description": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
        "certification": "R",
        "genres": ["Action", "Sci-Fi"],
        "directors": ["Lana Wachowski", "Lilly Wachowski"],
        "stars": ["Keanu Reeves", "Laurence Fishburne"],
    },
    {
        "name": "Interstellar",
        "year": 2014,
        "time": 169,
        "imdb": 8.6,
        "votes": 1800000,
        "meta_score": 74,
        "gross": 188020017,
        "description": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
        "certification": "PG-13",
        "genres": ["Adventure", "Drama", "Sci-Fi"],
        "directors": ["Christopher Nolan"],
        "stars": ["Matthew McConaughey", "Anne Hathaway"],
    },
    {
        "name": "Parasite",
        "year": 2019,
        "time": 132,
        "imdb": 8.5,
        "votes": 900000,
        "meta_score": 96,
        "gross": 53369749,
        "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
        "certification": "R",
        "genres": ["Comedy", "Drama", "Thriller"],
        "directors": ["Bong Joon-ho"],
        "stars": ["Song Kang-ho", "Lee Sun-kyun"],
    },
    {
        "name": "The Silence of the Lambs",
        "year": 1991,
        "time": 118,
        "imdb": 8.6,
        "votes": 1500000,
        "meta_score": 85,
        "gross": 130742922,
        "description": "A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer.",
        "certification": "R",
        "genres": ["Crime", "Drama", "Thriller"],
        "directors": ["Jonathan Demme"],
        "stars": ["Jodie Foster", "Anthony Hopkins"],
    },
]

USERS_DATA = [
    {
        "email": "admin@cinema.com",
        "password": "Admin123!",
        "group": UserGroupEnum.ADMIN,
        "first_name": "Admin",
        "last_name": "User",
        "gender": GenderEnum.MAN,
        "is_active": True,
    },
    {
        "email": "moderator@cinema.com",
        "password": "Moderator123!",
        "group": UserGroupEnum.MODERATOR,
        "first_name": "Moderator",
        "last_name": "User",
        "gender": GenderEnum.WOMAN,
        "is_active": True,
    },
    {
        "email": "john.doe@example.com",
        "password": "User123!",
        "group": UserGroupEnum.USER,
        "first_name": "John",
        "last_name": "Doe",
        "gender": GenderEnum.MAN,
        "is_active": True,
    },
    {
        "email": "jane.smith@example.com",
        "password": "User123!",
        "group": UserGroupEnum.USER,
        "first_name": "Jane",
        "last_name": "Smith",
        "gender": GenderEnum.WOMAN,
        "is_active": True,
    },
    {
        "email": "bob.wilson@example.com",
        "password": "User123!",
        "group": UserGroupEnum.USER,
        "first_name": "Bob",
        "last_name": "Wilson",
        "gender": GenderEnum.MAN,
        "is_active": True,
    },
    {
        "email": "alice.johnson@example.com",
        "password": "User123!",
        "group": UserGroupEnum.USER,
        "first_name": "Alice",
        "last_name": "Johnson",
        "gender": GenderEnum.WOMAN,
        "is_active": True,
    },
]


# ============================================================================
# SEEDING FUNCTIONS
# ============================================================================


async def clear_database(session: AsyncSession):
    """Clear all data from database"""
    print("Clearing database...")

    # Delete in correct order to avoid foreign key constraints
    await session.execute(text("DELETE FROM payment_items"))
    await session.execute(text("DELETE FROM payments"))
    await session.execute(text("DELETE FROM order_items"))
    await session.execute(text("DELETE FROM orders"))
    await session.execute(text("DELETE FROM cart_items"))
    await session.execute(text("DELETE FROM carts"))
    await session.execute(text("DELETE FROM movie_genres"))
    await session.execute(text("DELETE FROM movie_directors"))
    await session.execute(text("DELETE FROM movie_stars"))
    await session.execute(text("DELETE FROM movies"))
    await session.execute(text("DELETE FROM genres"))
    await session.execute(text("DELETE FROM directors"))
    await session.execute(text("DELETE FROM stars"))
    await session.execute(text("DELETE FROM certifications"))
    await session.execute(text("DELETE FROM refresh_tokens"))
    await session.execute(text("DELETE FROM password_reset_tokens"))
    await session.execute(text("DELETE FROM activation_tokens"))
    await session.execute(text("DELETE FROM user_profiles"))
    await session.execute(text("DELETE FROM users"))
    await session.execute(text("DELETE FROM user_groups"))

    await session.commit()
    print("Database cleared successfully")


async def seed_user_groups(session: AsyncSession) -> dict:
    """Seed user groups"""
    print("Seeding user groups...")

    groups = {}
    for group_name in UserGroupEnum:
        group = UserGroup(name=group_name)
        session.add(group)
        groups[group_name] = group

    await session.commit()

    # Refresh to get IDs
    for group in groups.values():
        await session.refresh(group)

    print(f"Created {len(groups)} user groups")
    return groups


async def seed_users(session: AsyncSession, groups: dict) -> List[User]:
    """Seed users with profiles"""
    print("Seeding users...")

    users = []
    for user_data in USERS_DATA:
        user = User(
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            is_active=user_data["is_active"],
            group_id=groups[user_data["group"]].id,
        )
        session.add(user)
        await session.flush()

        profile = UserProfile(
            user_id=user.id,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            gender=user_data["gender"],
            date_of_birth=datetime(1990, 1, 1)
            + timedelta(days=random.randint(0, 10000)),
            info=f"Test user profile for {user_data['first_name']} {user_data['last_name']}",
        )
        session.add(profile)

        # Create cart for each user
        cart = Cart(user_id=user.id)
        session.add(cart)

        users.append(user)

    await session.commit()

    # Refresh all users
    for user in users:
        await session.refresh(user)

    print(f"Created {len(users)} users with profiles and carts")
    return users


async def seed_genres(session: AsyncSession) -> dict:
    """Seed movie genres"""
    print("Seeding genres...")

    genres = {}
    for genre_name in GENRES_DATA:
        genre = Genre(name=genre_name)
        session.add(genre)
        genres[genre_name] = genre

    await session.commit()

    # Refresh to get IDs
    for genre in genres.values():
        await session.refresh(genre)

    print(f"Created {len(genres)} genres")
    return genres


async def seed_certifications(session: AsyncSession) -> dict:
    """Seed movie certifications"""
    print("Seeding certifications...")

    certifications = {}
    for cert_name in CERTIFICATIONS_DATA:
        cert = Certification(name=cert_name)
        session.add(cert)
        certifications[cert_name] = cert

    await session.commit()

    # Refresh to get IDs
    for cert in certifications.values():
        await session.refresh(cert)

    print(f"Created {len(certifications)} certifications")
    return certifications


async def seed_directors(session: AsyncSession) -> dict:
    """Seed directors"""
    print("Seeding directors...")

    directors = {}
    for director_name in DIRECTORS_DATA:
        director = Director(name=director_name)
        session.add(director)
        directors[director_name] = director

    # Add additional directors from movies data
    for movie_data in MOVIES_DATA:
        for director_name in movie_data["directors"]:
            if director_name not in directors:
                director = Director(name=director_name)
                session.add(director)
                directors[director_name] = director

    await session.commit()

    # Refresh to get IDs
    for director in directors.values():
        await session.refresh(director)

    print(f"Created {len(directors)} directors")
    return directors


async def seed_stars(session: AsyncSession) -> dict:
    """Seed actors/stars"""
    print("Seeding stars...")

    stars = {}
    for star_name in STARS_DATA:
        star = Star(name=star_name)
        session.add(star)
        stars[star_name] = star

    # Add additional stars from movies data
    for movie_data in MOVIES_DATA:
        for star_name in movie_data["stars"]:
            if star_name not in stars:
                star = Star(name=star_name)
                session.add(star)
                stars[star_name] = star

    await session.commit()

    # Refresh to get IDs
    for star in stars.values():
        await session.refresh(star)

    print(f"Created {len(stars)} stars")
    return stars


async def seed_movies(
    session: AsyncSession,
    genres: dict,
    certifications: dict,
    directors: dict,
    stars: dict,
) -> List[Movie]:
    """Seed movies with relationships"""
    print("Seeding movies...")

    movies = []
    for movie_data in MOVIES_DATA:
        # Generate random price between 5.99 and 19.99
        price = Decimal(random.uniform(5.99, 19.99)).quantize(Decimal("0.01"))

        movie = Movie(
            name=movie_data["name"],
            year=movie_data["year"],
            time=movie_data["time"],
            imdb=Decimal(str(movie_data["imdb"])),
            votes=movie_data["votes"],
            meta_score=(
                Decimal(str(movie_data["meta_score"]))
                if movie_data.get("meta_score")
                else None
            ),
            gross=(
                Decimal(str(movie_data["gross"])) if movie_data.get("gross") else None
            ),
            description=movie_data["description"],
            price=price,
            certification_id=certifications[movie_data["certification"]].id,
        )

        # Add genres
        for genre_name in movie_data["genres"]:
            if genre_name in genres:
                movie.genres.append(genres[genre_name])

        # Add directors
        for director_name in movie_data["directors"]:
            if director_name in directors:
                movie.directors.append(directors[director_name])

        # Add stars
        for star_name in movie_data["stars"]:
            if star_name in stars:
                movie.stars.append(stars[star_name])

        session.add(movie)
        movies.append(movie)

    await session.commit()

    # Refresh all movies
    for movie in movies:
        await session.refresh(movie)

    print(f"Created {len(movies)} movies")
    return movies


async def seed_cart_items(
    session: AsyncSession, users: List[User], movies: List[Movie]
):
    """Seed cart items for users"""
    print("Seeding cart items...")

    cart_items_count = 0

    # Skip admin and moderator (first 2 users)
    for user in users[2:]:
        # Get user's cart with eager loading
        stmt = select(Cart).where(Cart.user_id == user.id)
        result = await session.execute(stmt)
        cart = result.scalar_one()

        # Add random movies to cart (1-3 movies)
        num_items = random.randint(1, 3)
        selected_movies = random.sample(movies, min(num_items, len(movies)))

        for movie in selected_movies:
            cart_item = CartItem(
                cart_id=cart.id,
                movie_id=movie.id,
            )
            session.add(cart_item)
            cart_items_count += 1

    await session.commit()
    print(f"Created {cart_items_count} cart items")


async def seed_orders(session: AsyncSession, users: List[User], movies: List[Movie]):
    """Seed orders with items and payments"""
    print("Seeding orders...")

    orders_count = 0
    payments_count = 0

    # Skip admin and moderator (first 2 users)
    for user in users[2:]:
        # Create 1-3 orders per user
        num_orders = random.randint(1, 3)

        for _ in range(num_orders):
            # Random order status
            status = random.choice([OrderStatusEnum.PAID, OrderStatusEnum.PENDING])

            # Select random movies for order (1-4 movies)
            num_items = random.randint(1, 4)
            selected_movies = random.sample(movies, min(num_items, len(movies)))

            total_amount = sum(movie.price for movie in selected_movies)

            order = Order(
                user_id=user.id,
                status=status,
                total_amount=total_amount,
                created_at=datetime.now(timezone.utc)
                - timedelta(days=random.randint(0, 30)),
            )
            session.add(order)
            await session.flush()

            # Create order items
            order_items = []
            for movie in selected_movies:
                order_item = OrderItem(
                    order_id=order.id,
                    movie_id=movie.id,
                    price_at_order=movie.price,
                )
                session.add(order_item)
                order_items.append(order_item)

            await session.flush()

            # Create payment if order is paid
            if status == OrderStatusEnum.PAID:
                payment = Payment(
                    user_id=user.id,
                    order_id=order.id,
                    session_id=f"sess_{random.randint(100000, 999999)}",
                    payment_intent_id=f"pi_{random.randint(100000, 999999)}",
                    status=PaymentStatusEnum.SUCCESSFUL,
                    amount=total_amount,
                    external_payment_id=f"ch_{random.randint(100000, 999999)}",
                )
                session.add(payment)
                await session.flush()

                # Create payment items
                for order_item in order_items:
                    payment_item = PaymentItem(
                        payment_id=payment.id,
                        order_item_id=order_item.id,
                        price_at_payment=order_item.price_at_order,
                    )
                    session.add(payment_item)

                payments_count += 1

            orders_count += 1

    await session.commit()
    print(f"Created {orders_count} orders and {payments_count} payments")


# ============================================================================
# MAIN SEEDING FUNCTION
# ============================================================================


async def seed_all():
    """Seed all database tables"""
    async with AsyncSessionLocal() as session:
        try:
            print("Starting database seeding...")
            print("=" * 80)

            # Clear existing data
            await clear_database(session)

            # Seed in correct order
            groups = await seed_user_groups(session)
            users = await seed_users(session, groups)
            genres = await seed_genres(session)
            certifications = await seed_certifications(session)
            directors = await seed_directors(session)
            stars = await seed_stars(session)
            movies = await seed_movies(
                session, genres, certifications, directors, stars
            )
            await seed_cart_items(session, users, movies)
            await seed_orders(session, users, movies)

            print("=" * 80)
            print("Database seeding completed successfully!")
            print("\nTest User Credentials:")
            print("-" * 80)
            for user_data in USERS_DATA:
                print(f"Email: {user_data['email']}")
                print(f"Password: {user_data['password']}")
                print(f"Role: {user_data['group'].value}")
                print("-" * 80)

        except Exception as e:
            print(f"Error during seeding: {e}")
            await session.rollback()
            raise


async def seed_minimal():
    """Seed only essential data (groups, certifications, genres)"""
    async with AsyncSessionLocal() as session:
        try:
            print("Starting minimal database seeding...")

            groups = await seed_user_groups(session)
            await seed_genres(session)
            await seed_certifications(session)
            await seed_directors(session)
            await seed_stars(session)

            print("Minimal seeding completed successfully!")

        except Exception as e:
            print(f"Error during minimal seeding: {e}")
            await session.rollback()
            raise


# ============================================================================
# CLI EXECUTION
# ============================================================================


def main():
    """Main execution function"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--minimal":
        print("Running minimal seed...")
        asyncio.run(seed_minimal())
    else:
        print("Running full seed...")
        asyncio.run(seed_all())


if __name__ == "__main__":
    main()
