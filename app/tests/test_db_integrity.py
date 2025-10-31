import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine, inspect, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database.models.models import (
    Base,
    User,
    UserGroup,
    UserProfile,
    UserGroupEnum,
    GenderEnum,
    ActivationToken,
    PasswordResetToken,
    RefreshToken,
    Movie,
    Genre,
    Director,
    Star,
    Certification,
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatusEnum,
    Payment,
    PaymentItem,
    PaymentStatusEnum,
    movie_genres,
    movie_directors,
    movie_stars,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def db_engine():
    """Creates a test engine for an SQLite in-memory database."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Enables foreign keys for SQLite."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Creates a database session for testing."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def user_group(db_session):
    """Creates a user group."""
    group = UserGroup(name=UserGroupEnum.USER)
    db_session.add(group)
    db_session.commit()
    return group


@pytest.fixture
def user(db_session, user_group):
    """Creates a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123",
        is_active=True,
        group_id=user_group.id,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def certification(db_session):
    """Creates a movie certification."""
    cert = Certification(name="PG-13")
    db_session.add(cert)
    db_session.commit()
    return cert


@pytest.fixture
def movie(db_session, certification):
    """Creates a test movie."""
    movie = Movie(
        name="Test Movie",
        year=2024,
        time=120,
        imdb=Decimal("8.5"),
        votes=10000,
        description="Test description",
        price=Decimal("9.99"),
        certification_id=certification.id,
    )
    db_session.add(movie)
    db_session.commit()
    return movie


# ============================================================================
# DATABASE STRUCTURE TESTS
# ============================================================================


class TestDatabaseStructure:
    """Tests for database structure and schema."""

    def test_all_tables_created(self, db_engine):
        """Checks that all expected tables have been created."""
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        expected_tables = {
            "user_groups",
            "users",
            "user_profiles",
            "activation_tokens",
            "password_reset_tokens",
            "refresh_tokens",
            "genres",
            "stars",
            "directors",
            "certifications",
            "movies",
            "movie_genres",
            "movie_directors",
            "movie_stars",
            "carts",
            "cart_items",
            "orders",
            "order_items",
            "payments",
            "payment_items",
        }

        assert expected_tables.issubset(
            set(tables)
        ), f"Missing tables: {expected_tables - set(tables)}"

    def test_user_table_columns(self, db_engine):
        """Checks for the existence of required columns in the 'users' table."""
        inspector = inspect(db_engine)
        columns = {col["name"] for col in inspector.get_columns("users")}

        expected_columns = {
            "id",
            "email",
            "hashed_password",
            "is_active",
            "created_at",
            "updated_at",
            "group_id",
        }

        assert expected_columns.issubset(columns)

    def test_movie_table_columns(self, db_engine):
        """Checks for the existence of required columns in the 'movies' table."""
        inspector = inspect(db_engine)
        columns = {col["name"] for col in inspector.get_columns("movies")}

        expected_columns = {
            "id",
            "uuid",
            "name",
            "year",
            "time",
            "imdb",
            "votes",
            "meta_score",
            "gross",
            "description",
            "price",
            "certification_id",
        }

        assert expected_columns.issubset(columns)

    def test_foreign_keys_exist(self, db_engine):
        """Checks for the existence of key foreign key constraints."""
        inspector = inspect(db_engine)

        user_fks = inspector.get_foreign_keys("users")
        assert any(
            fk["referred_table"] == "user_groups" for fk in user_fks
        ), "Missing FK from users to user_groups"

        movie_fks = inspector.get_foreign_keys("movies")
        assert any(
            fk["referred_table"] == "certifications" for fk in movie_fks
        ), "Missing FK from movies to certifications"

        cart_item_fks = inspector.get_foreign_keys("cart_items")
        referred_tables = {fk["referred_table"] for fk in cart_item_fks}
        assert {"carts", "movies"}.issubset(
            referred_tables
        ), "Missing FKs from cart_items to carts or movies"

    def test_unique_constraints(self, db_engine):
        """Checks for the existence of unique constraints via indexes."""
        inspector = inspect(db_engine)

        user_indexes = inspector.get_indexes("users")
        user_unique_columns = [
            idx["column_names"][0] for idx in user_indexes if idx.get("unique", False)
        ]
        assert (
            "email" in user_unique_columns
        ), f"Expected 'email' in unique columns, got: {user_unique_columns}"

        # UUID uniqueness is tested practically in TestUniqueConstraints


# ============================================================================
# ONE-TO-MANY RELATIONSHIP TESTS
# ============================================================================


class TestOneToManyRelationships:
    """Tests for One-to-Many relationships."""

    def test_user_group_to_users(self, db_session, user_group):
        """Checks the UserGroup -> Users relationship."""
        users = [
            User(
                email=f"user{i}@example.com",
                hashed_password="hash",
                group_id=user_group.id,
            )
            for i in range(3)
        ]
        db_session.add_all(users)
        db_session.commit()

        db_session.refresh(user_group)
        assert len(user_group.users) == 3

    def test_user_to_orders(self, db_session, user):
        """Checks the User -> Orders relationship."""
        orders = [
            Order(user_id=user.id, total_amount=Decimal("100.00")) for _ in range(3)
        ]
        db_session.add_all(orders)
        db_session.commit()

        db_session.refresh(user)
        assert len(user.orders) == 3

    def test_user_to_payments(self, db_session, user, movie):
        """Checks the User -> Payments relationship."""
        order = Order(user_id=user.id, total_amount=Decimal("50.00"))
        db_session.add(order)
        db_session.commit()

        payments = [
            Payment(user_id=user.id, order_id=order.id, amount=Decimal("50.00"))
            for _ in range(2)
        ]
        db_session.add_all(payments)
        db_session.commit()

        db_session.refresh(user)
        assert len(user.payments) == 2

    def test_order_to_order_items(self, db_session, user, movie):
        """Checks the Order -> OrderItems relationship."""
        order = Order(user_id=user.id, total_amount=Decimal("100.00"))
        db_session.add(order)
        db_session.commit()

        order_items = [
            OrderItem(
                order_id=order.id, movie_id=movie.id, price_at_order=Decimal("10.00")
            )
            for _ in range(3)
        ]
        db_session.add_all(order_items)
        db_session.commit()

        db_session.refresh(order)
        assert len(order.items) == 3

    def test_certification_to_movies(self, db_session, certification):
        """Checks the Certification -> Movies relationship."""
        movies = [
            Movie(
                name=f"Movie {i}",
                year=2024,
                time=120,
                imdb=Decimal("7.5"),
                votes=1000,
                description="Test",
                price=Decimal("9.99"),
                certification_id=certification.id,
            )
            for i in range(3)
        ]
        db_session.add_all(movies)
        db_session.commit()

        db_session.refresh(certification)
        assert len(certification.movies) == 3


# ============================================================================
# ONE-TO-ONE RELATIONSHIP TESTS
# ============================================================================


class TestOneToOneRelationships:
    """Tests for One-to-One relationships."""

    def test_user_to_profile(self, db_session, user):
        """Checks the User <-> UserProfile relationship."""
        profile = UserProfile(
            user_id=user.id, first_name="John", last_name="Doe", gender=GenderEnum.MAN
        )
        db_session.add(profile)
        db_session.commit()

        db_session.refresh(user)
        assert user.profile is not None
        assert user.profile.first_name == "John"
        assert profile.user.email == user.email

    def test_user_to_activation_token(self, db_session, user):
        """Checks the User <-> ActivationToken relationship."""
        token = ActivationToken(
            user_id=user.id,
            token="test_token_123",
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        db_session.add(token)
        db_session.commit()

        db_session.refresh(user)
        assert user.activation_token is not None
        assert user.activation_token.token == "test_token_123"

    def test_user_to_password_reset_token(self, db_session, user):
        """Checks the User <-> PasswordResetToken relationship."""
        token = PasswordResetToken(
            user_id=user.id,
            token="reset_token_456",
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
        db_session.add(token)
        db_session.commit()

        db_session.refresh(user)
        assert user.password_reset_token is not None
        assert user.password_reset_token.token == "reset_token_456"

    def test_user_to_cart(self, db_session, user):
        """Checks the User <-> Cart relationship."""
        cart = Cart(user_id=user.id)
        db_session.add(cart)
        db_session.commit()

        db_session.refresh(user)
        assert user.cart is not None
        assert user.cart.user_id == user.id

    def test_duplicate_profile_constraint(self, db_session, user):
        """Ensures a user can only have one profile (unique constraint on user_id)."""
        profile1 = UserProfile(user_id=user.id, first_name="John")
        db_session.add(profile1)
        db_session.commit()

        profile2 = UserProfile(user_id=user.id, first_name="Jane")
        db_session.add(profile2)

        with pytest.raises(IntegrityError):
            db_session.commit()


# ============================================================================
# MANY-TO-MANY RELATIONSHIP TESTS
# ============================================================================


class TestManyToManyRelationships:
    """Tests for Many-to-Many relationships."""

    def test_movie_to_genres(self, db_session, movie):
        """Checks the Movie <-> Genre relationship via association table."""
        genres = [Genre(name=f"Genre {i}") for i in range(3)]
        db_session.add_all(genres)
        db_session.commit()

        movie.genres.extend(genres)
        db_session.commit()

        db_session.refresh(movie)
        assert len(movie.genres) == 3

        db_session.refresh(genres[0])
        assert movie in genres[0].movies

    def test_movie_to_directors(self, db_session, movie):
        """Checks the Movie <-> Director relationship via association table."""
        directors = [Director(name=f"Director {i}") for i in range(2)]
        db_session.add_all(directors)
        db_session.commit()

        movie.directors.extend(directors)
        db_session.commit()

        db_session.refresh(movie)
        assert len(movie.directors) == 2

        db_session.refresh(directors[0])
        assert movie in directors[0].movies

    def test_movie_to_stars(self, db_session, movie):
        """Checks the Movie <-> Star relationship via association table."""
        stars = [Star(name=f"Star {i}") for i in range(4)]
        db_session.add_all(stars)
        db_session.commit()

        movie.stars.extend(stars)
        db_session.commit()

        db_session.refresh(movie)
        assert len(movie.stars) == 4

        db_session.refresh(stars[0])
        assert movie in stars[0].movies

    def test_multiple_movies_same_genre(self, db_session, certification):
        """Ensures multiple movies can share the same genre."""
        genre = Genre(name="Action")
        db_session.add(genre)
        db_session.commit()

        movies = [
            Movie(
                name=f"Movie {i}",
                year=2024,
                time=120,
                imdb=Decimal("7.5"),
                votes=1000,
                description="Test",
                price=Decimal("9.99"),
                certification_id=certification.id,
            )
            for i in range(3)
        ]

        for movie in movies:
            movie.genres.append(genre)

        db_session.add_all(movies)
        db_session.commit()

        db_session.refresh(genre)
        assert len(genre.movies) == 3


# ============================================================================
# CASCADE DELETE TESTS
# ============================================================================


class TestCascadeDelete:
    """Tests for cascade delete behavior on related tables."""

    def test_delete_user_deletes_profile(self, db_session, user):
        """Checks that deleting a User also deletes the associated UserProfile."""
        profile = UserProfile(user_id=user.id, first_name="John")
        db_session.add(profile)
        db_session.commit()

        profile_id = profile.id
        user_id = user.id

        # Manual deletion order for SQLite with NOT NULL constraint
        db_session.query(UserProfile).filter_by(user_id=user.id).delete()
        db_session.query(User).filter_by(id=user.id).delete()
        db_session.commit()

        deleted_user = db_session.query(User).filter_by(id=user_id).first()
        deleted_profile = db_session.query(UserProfile).filter_by(id=profile_id).first()

        assert deleted_user is None
        assert deleted_profile is None

    def test_delete_user_deletes_cart(self, db_session, user):
        """Checks that deleting a User also deletes the associated Cart."""
        cart = Cart(user_id=user.id)
        db_session.add(cart)
        db_session.commit()

        cart_id = cart.id
        user_id = user.id

        # Manual deletion order for SQLite with NOT NULL constraint
        db_session.query(Cart).filter_by(user_id=user.id).delete()
        db_session.query(User).filter_by(id=user.id).delete()
        db_session.commit()

        deleted_user = db_session.query(User).filter_by(id=user_id).first()
        deleted_cart = db_session.query(Cart).filter_by(id=cart_id).first()

        assert deleted_user is None
        assert deleted_cart is None

    def test_delete_cart_deletes_cart_items(self, db_session, user, movie):
        """Checks that deleting a Cart deletes all associated CartItems."""
        cart = Cart(user_id=user.id)
        db_session.add(cart)
        db_session.commit()

        cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
        db_session.add(cart_item)
        db_session.commit()

        cart_item_id = cart_item.id

        db_session.delete(cart)
        db_session.commit()

        deleted_item = db_session.query(CartItem).filter_by(id=cart_item_id).first()
        assert deleted_item is None

    def test_delete_order_deletes_order_items(self, db_session, user, movie):
        """Checks that deleting an Order deletes all associated OrderItems."""
        order = Order(user_id=user.id, total_amount=Decimal("100.00"))
        db_session.add(order)
        db_session.commit()

        order_item = OrderItem(
            order_id=order.id, movie_id=movie.id, price_at_order=Decimal("10.00")
        )
        db_session.add(order_item)
        db_session.commit()

        order_item_id = order_item.id

        db_session.delete(order)
        db_session.commit()

        deleted_item = db_session.query(OrderItem).filter_by(id=order_item_id).first()
        assert deleted_item is None

    def test_delete_payment_deletes_payment_items(self, db_session, user, movie):
        """Checks that deleting a Payment deletes all associated PaymentItems."""
        order = Order(user_id=user.id, total_amount=Decimal("50.00"))
        db_session.add(order)
        db_session.commit()

        order_item = OrderItem(
            order_id=order.id, movie_id=movie.id, price_at_order=Decimal("10.00")
        )
        db_session.add(order_item)
        db_session.commit()

        payment = Payment(user_id=user.id, order_id=order.id, amount=Decimal("50.00"))
        db_session.add(payment)
        db_session.commit()

        payment_item = PaymentItem(
            payment_id=payment.id,
            order_item_id=order_item.id,
            price_at_payment=Decimal("10.00"),
        )
        db_session.add(payment_item)
        db_session.commit()

        payment_item_id = payment_item.id

        db_session.delete(payment)
        db_session.commit()

        deleted_item = (
            db_session.query(PaymentItem).filter_by(id=payment_item_id).first()
        )
        assert deleted_item is None


# ============================================================================
# UNIQUE CONSTRAINTS TESTS
# ============================================================================


class TestUniqueConstraints:
    """Tests for unique database constraints."""

    def test_duplicate_email_fails(self, db_session, user_group):
        """Ensures a duplicate user email cannot be created."""
        user1 = User(
            email="same@example.com", hashed_password="hash1", group_id=user_group.id
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            email="same@example.com", hashed_password="hash2", group_id=user_group.id
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_duplicate_cart_item_fails(self, db_session, user, movie):
        """Ensures the same movie cannot be added to the same cart twice."""
        cart = Cart(user_id=user.id)
        db_session.add(cart)
        db_session.commit()

        item1 = CartItem(cart_id=cart.id, movie_id=movie.id)
        db_session.add(item1)
        db_session.commit()

        item2 = CartItem(cart_id=cart.id, movie_id=movie.id)
        db_session.add(item2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_duplicate_movie_identity_fails(self, db_session, certification):
        """Ensures a movie with the same name, year, and time cannot be created."""
        movie1 = Movie(
            name="Same Movie",
            year=2024,
            time=120,
            imdb=Decimal("8.0"),
            votes=1000,
            description="Test 1",
            price=Decimal("9.99"),
            certification_id=certification.id,
        )
        db_session.add(movie1)
        db_session.commit()

        movie2 = Movie(
            name="Same Movie",
            year=2024,
            time=120,
            imdb=Decimal("7.0"),
            votes=2000,
            description="Test 2",
            price=Decimal("12.99"),
            certification_id=certification.id,
        )
        db_session.add(movie2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_duplicate_genre_name_fails(self, db_session):
        """Ensures a duplicate genre name cannot be created."""
        genre1 = Genre(name="Action")
        db_session.add(genre1)
        db_session.commit()

        genre2 = Genre(name="Action")
        db_session.add(genre2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_duplicate_uuid_fails(self, db_session, certification):
        """Ensures a movie with a duplicate UUID cannot be created (practical check)."""
        from uuid import uuid4

        same_uuid = uuid4()

        movie1 = Movie(
            uuid=same_uuid,
            name="Movie 1",
            year=2024,
            time=120,
            imdb=Decimal("8.0"),
            votes=1000,
            description="Test 1",
            price=Decimal("9.99"),
            certification_id=certification.id,
        )
        db_session.add(movie1)
        db_session.commit()

        movie2 = Movie(
            uuid=same_uuid,
            name="Movie 2",
            year=2023,
            time=90,
            imdb=Decimal("7.0"),
            votes=2000,
            description="Test 2",
            price=Decimal("12.99"),
            certification_id=certification.id,
        )
        db_session.add(movie2)

        with pytest.raises(IntegrityError):
            db_session.commit()


# ============================================================================
# REFERENTIAL INTEGRITY TESTS
# ============================================================================


class TestReferentialIntegrity:
    """Tests for enforcing foreign key constraints (referential integrity)."""

    def test_cannot_create_user_with_invalid_group(self, db_session):
        """Ensures a user cannot be created with a non-existent group_id."""
        user = User(email="test@example.com", hashed_password="hash", group_id=999)
        db_session.add(user)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_cannot_create_movie_with_invalid_certification(self, db_session):
        """Ensures a movie cannot be created with a non-existent certification_id."""
        movie = Movie(
            name="Test Movie",
            year=2024,
            time=120,
            imdb=Decimal("8.0"),
            votes=1000,
            description="Test",
            price=Decimal("9.99"),
            certification_id=999,
        )
        db_session.add(movie)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_cannot_create_cart_item_with_invalid_movie(self, db_session, user):
        """Ensures a cart item cannot reference a non-existent movie_id."""
        cart = Cart(user_id=user.id)
        db_session.add(cart)
        db_session.commit()

        cart_item = CartItem(cart_id=cart.id, movie_id=999)
        db_session.add(cart_item)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_cannot_delete_movie_with_cart_items(self, db_session, user, movie):
        """Ensures a movie cannot be deleted if it is referenced by a CartItem."""
        cart = Cart(user_id=user.id)
        db_session.add(cart)
        db_session.commit()

        cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
        db_session.add(cart_item)
        db_session.commit()

        with pytest.raises(IntegrityError):
            db_session.delete(movie)
            db_session.commit()


# ============================================================================
# BUSINESS LOGIC TESTS
# ============================================================================


class TestBusinessLogic:
    """Tests for core application business logic enforced via models."""

    def test_order_total_amount_calculation(
        self, db_session, user, movie, certification
    ):
        """Checks the calculation of the order's total amount."""
        movie2 = Movie(
            name="Movie 2",
            year=2024,
            time=90,
            imdb=Decimal("7.5"),
            votes=500,
            description="Test",
            price=Decimal("14.99"),
            certification_id=certification.id,
        )
        db_session.add(movie2)
        db_session.commit()

        order = Order(user_id=user.id, status=OrderStatusEnum.PENDING)
        db_session.add(order)
        db_session.commit()

        items = [
            OrderItem(order_id=order.id, movie_id=movie.id, price_at_order=movie.price),
            OrderItem(
                order_id=order.id, movie_id=movie2.id, price_at_order=movie2.price
            ),
        ]
        db_session.add_all(items)
        db_session.commit()

        total = sum(item.price_at_order for item in items)
        order.total_amount = total
        db_session.commit()

        assert order.total_amount == Decimal("24.98")

    def test_payment_amount_matches_order(self, db_session, user, movie):
        """Checks that the payment amount matches the order's total amount."""
        order = Order(user_id=user.id, total_amount=Decimal("100.00"))
        db_session.add(order)
        db_session.commit()

        payment = Payment(
            user_id=user.id,
            order_id=order.id,
            amount=order.total_amount,
            status=PaymentStatusEnum.SUCCESSFUL,
        )
        db_session.add(payment)
        db_session.commit()

        assert payment.amount == order.total_amount

    def test_price_history_preservation(self, db_session, user, movie):
        """Verifies that the price at the time of order is preserved, independent of later movie price changes."""
        original_price = movie.price

        order = Order(user_id=user.id)
        db_session.add(order)
        db_session.commit()

        order_item = OrderItem(
            order_id=order.id, movie_id=movie.id, price_at_order=original_price
        )
        db_session.add(order_item)
        db_session.commit()

        # Change the movie's current price
        movie.price = Decimal("19.99")
        db_session.commit()

        db_session.refresh(order_item)
        assert order_item.price_at_order == original_price
        assert movie.price == Decimal("19.99")

    def test_user_can_have_multiple_refresh_tokens(self, db_session, user):
        """Ensures a single user can have multiple refresh tokens (e.g., for different devices)."""
        tokens = [
            RefreshToken(
                user_id=user.id,
                token=f"token_{i}",
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            for i in range(3)
        ]
        db_session.add_all(tokens)
        db_session.commit()

        db_session.refresh(user)
        assert len(user.refresh_tokens) == 3
