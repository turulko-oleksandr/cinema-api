import pytest
from httpx import AsyncClient


class TestGenreList:
    """Test genre listing endpoint"""

    async def test_get_genres(self, client: AsyncClient, test_genre):
        """Test get all genres"""
        response = await client.get("/api/v1/genres/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_get_genres_statistics(self, client: AsyncClient, test_genre):
        """Test get genres with movie count"""
        response = await client.get("/api/v1/genres/statistics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestGenreDetail:
    """Test genre detail endpoint"""

    async def test_get_genre_by_id(self, client: AsyncClient, test_genre):
        """Test get genre by ID"""
        response = await client.get(f"/api/v1/genres/{test_genre.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_genre.id
        assert data["name"] == "Action"

    async def test_get_genre_not_found(self, client: AsyncClient):
        """Test get non-existent genre"""
        response = await client.get("/api/v1/genres/99999")
        assert response.status_code == 404


class TestGenreCreate:
    """Test genre creation endpoint"""

    async def test_create_genre_as_moderator(
        self, client: AsyncClient, moderator_headers
    ):
        """Test create genre as moderator"""
        response = await client.post(
            "/api/v1/genres/",
            headers=moderator_headers,
            json={"name": "Horror"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Horror"

    async def test_create_genre_unauthorized(self, client: AsyncClient, auth_headers):
        """Test create genre as regular user (should fail)"""
        response = await client.post(
            "/api/v1/genres/",
            headers=auth_headers,
            json={"name": "Horror"},
        )
        assert response.status_code == 403


class TestGenreUpdate:
    """Test genre update endpoint"""

    async def test_update_genre(
        self, client: AsyncClient, moderator_headers, test_genre
    ):
        """Test update genre"""
        response = await client.patch(
            f"/api/v1/genres/{test_genre.id}",
            headers=moderator_headers,
            json={"name": "Action Movies"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Action Movies"


class TestGenreDelete:
    """Test genre deletion endpoint"""

    async def test_delete_genre(
        self, client: AsyncClient, moderator_headers, test_genre
    ):
        """Test delete genre"""
        response = await client.delete(
            f"/api/v1/genres/{test_genre.id}",
            headers=moderator_headers,
        )
        assert response.status_code == 200
