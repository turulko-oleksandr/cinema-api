import asyncio
import pytest
import tempfile
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.main import app
from app.database.models.models import (
    Base,
    UserGroup,
    UserGroupEnum,
    User,
    Genre,
    Certification,
    Director,
    Star,
    Movie,
)
from app.database.db_session import get_db
from app.services.passwords import hash_password
from app.config.dependencies import get_settings

# Test database URL
temp_db = tempfile.NamedTemporaryFile(delete=False)
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{temp_db.name}"
# Create async test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

# Create async session factory
TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Override get_db dependency
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Create and drop tables for each test - runs automatically"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for each test"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()  # Rollback any uncommitted changes


@pytest.fixture(scope="function")
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Create test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture
async def user_groups(db_session: AsyncSession) -> dict:
    """Create user groups"""
    groups = {}
    for group_name in UserGroupEnum:
        group = UserGroup(name=group_name)
        db_session.add(group)
        groups[group_name] = group

    await db_session.commit()

    # Refresh all groups to get their IDs
    for group in groups.values():
        await db_session.refresh(group)

    return groups


@pytest.fixture
async def test_user(db_session: AsyncSession, user_groups: dict) -> User:
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("TestPass123!"),
        is_active=True,
        group_id=user_groups[UserGroupEnum.USER].id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession, user_groups: dict) -> User:
    """Create admin user"""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123!"),
        is_active=True,
        group_id=user_groups[UserGroupEnum.ADMIN].id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def moderator_user(db_session: AsyncSession, user_groups: dict) -> User:
    """Create moderator user"""
    user = User(
        email="moderator@example.com",
        hashed_password=hash_password("ModeratorPass123!"),
        is_active=True,
        group_id=user_groups[UserGroupEnum.MODERATOR].id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_genre(db_session: AsyncSession) -> Genre:
    """Create test genre"""
    genre = Genre(name="Action")
    db_session.add(genre)
    await db_session.commit()
    await db_session.refresh(genre)
    return genre


@pytest.fixture
async def test_certification(db_session: AsyncSession) -> Certification:
    """Create test certification"""
    cert = Certification(name="PG-13")
    db_session.add(cert)
    await db_session.commit()
    await db_session.refresh(cert)
    return cert


@pytest.fixture
async def test_director(db_session: AsyncSession) -> Director:
    """Create test director"""
    director = Director(name="Christopher Nolan")
    db_session.add(director)
    await db_session.commit()
    await db_session.refresh(director)
    return director


@pytest.fixture
async def test_star(db_session: AsyncSession) -> Star:
    """Create test star"""
    star = Star(name="Leonardo DiCaprio")
    db_session.add(star)
    await db_session.commit()
    await db_session.refresh(star)
    return star


@pytest.fixture
async def test_movie(
    db_session: AsyncSession,
    test_genre: Genre,
    test_certification: Certification,
    test_director: Director,
    test_star: Star,
) -> Movie:
    """Create test movie"""
    movie = Movie(
        name="Test Movie",
        year=2024,
        time=120,
        imdb=8.5,
        votes=100000,
        meta_score=85,
        gross=1000000,
        description="Test movie description",
        price=9.99,
        certification_id=test_certification.id,
    )
    movie.genres.append(test_genre)
    movie.directors.append(test_director)
    movie.stars.append(test_star)

    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================


@pytest.fixture
async def user_token(client: AsyncClient, test_user: User) -> str:
    """Get JWT token for test user"""
    response = await client.post(
        "/api/v1/accounts/login/",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
        },
    )
    assert response.status_code == 201, f"Login failed: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """Get JWT token for admin user"""
    response = await client.post(
        "/api/v1/accounts/login/",
        json={
            "email": "admin@example.com",
            "password": "AdminPass123!",
        },
    )
    assert response.status_code == 201, f"Login failed: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
async def moderator_token(client: AsyncClient, moderator_user: User) -> str:
    """Get JWT token for moderator user"""
    response = await client.post(
        "/api/v1/accounts/login/",
        json={
            "email": "moderator@example.com",
            "password": "ModeratorPass123!",
        },
    )
    assert response.status_code == 201, f"Login failed: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """Get authorization headers for test user"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Get authorization headers for admin user"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def moderator_headers(moderator_token: str) -> dict:
    """Get authorization headers for moderator user"""
    return {"Authorization": f"Bearer {moderator_token}"}
