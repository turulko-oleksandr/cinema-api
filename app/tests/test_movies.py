import pytest
from httpx import AsyncClient
from decimal import Decimal


class TestMovieList:
    """Test movie listing endpoint"""

    async def test_get_movies(self, client: AsyncClient, test_movie):
        """Test get all movies"""
        response = await client.get("/api/v1/movies/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0

    async def test_get_movies_pagination(self, client: AsyncClient, test_movie):
        """Test movies pagination"""
        response = await client.get("/api/v1/movies/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10


class TestMovieDetail:
    """Test movie detail endpoint"""

    async def test_get_movie_by_id(self, client: AsyncClient, test_movie):
        """Test get movie by ID"""
        response = await client.get(f"/api/v1/movies/{test_movie.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_movie.id
        assert data["name"] == "Test Movie"

    async def test_get_movie_not_found(self, client: AsyncClient):
        """Test get non-existent movie"""
        response = await client.get("/api/v1/movies/99999")
        assert response.status_code == 404


class TestMovieCreate:
    """Test movie creation endpoint"""

    async def test_create_movie_as_moderator(
        self, client: AsyncClient, moderator_headers, test_genre, test_certification
    ):
        """Test create movie as moderator"""
        response = await client.post(
            "/api/v1/movies/",
            headers=moderator_headers,
            json={
                "name": "New Movie",
                "year": 2024,
                "time": 120,
                "imdb": 8.0,
                "votes": 10000,
                "description": "New movie description",
                "price": 12.99,
                "certification_id": test_certification.id,
                "genre_ids": [test_genre.id],
                "director_ids": [],
                "star_ids": [],
            },
        )

        if response.status_code != 201:
            print(f"Помилка 400: {response.json()}")

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Movie"

    async def test_create_movie_unauthorized(self, client: AsyncClient, auth_headers):
        """Test create movie as regular user (should fail)"""
        response = await client.post(
            "/api/v1/movies/",
            headers=auth_headers,
            json={
                "name": "New Movie",
                "year": 2024,
                "time": 120,
                "imdb": 8.0,
                "votes": 10000,
                "description": "New movie description",
                "price": 12.99,
                "certification_id": 1,
            },
        )
        assert response.status_code == 403


class TestMovieUpdate:
    """Test movie update endpoint"""

    async def test_update_movie(
        self, client: AsyncClient, moderator_headers, test_movie
    ):
        """Test update movie"""
        response = await client.patch(
            f"/api/v1/movies/{test_movie.id}",
            headers=moderator_headers,
            json={"name": "Updated Movie Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Movie Name"

    async def test_update_movie_unauthorized(
        self, client: AsyncClient, auth_headers, test_movie
    ):
        """Test update movie as regular user (should fail)"""
        response = await client.patch(
            f"/api/v1/movies/{test_movie.id}",
            headers=auth_headers,
            json={"name": "Updated Movie Name"},
        )
        assert response.status_code == 403


class TestMovieDelete:
    """Test movie deletion endpoint"""

    async def test_delete_movie(
        self, client: AsyncClient, moderator_headers, test_movie
    ):
        """Test delete movie"""
        response = await client.delete(
            f"/api/v1/movies/{test_movie.id}",
            headers=moderator_headers,
        )
        assert response.status_code == 204

    async def test_delete_movie_unauthorized(
        self, client: AsyncClient, auth_headers, test_movie
    ):
        """Test delete movie as regular user (should fail)"""
        response = await client.delete(
            f"/api/v1/movies/{test_movie.id}",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestMovieSearch:
    """Test movie search endpoint"""

    async def test_search_movies(self, client: AsyncClient, test_movie):
        """Test search movies"""
        response = await client.get("/api/v1/movies/search/query?q=Test")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0

    async def test_search_movies_no_results(self, client: AsyncClient):
        """Test search with no results"""
        response = await client.get("/api/v1/movies/search/query?q=NonExistentMovie")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


class TestMovieFilter:
    """Test movie filtering endpoint"""

    async def test_filter_movies_by_year(self, client: AsyncClient, test_movie):
        """Test filter movies by year"""
        response = await client.get(
            "/api/v1/movies/filter/advanced?year_from=2024&year_to=2024"
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_filter_movies_by_imdb(self, client: AsyncClient, test_movie):
        """Test filter movies by IMDB rating"""
        response = await client.get(
            "/api/v1/movies/filter/advanced?imdb_min=8.0&imdb_max=9.0"
        )
        assert response.status_code == 200


class TestMovieSpecial:
    """Test special movie endpoints"""

    async def test_get_trending_movies(self, client: AsyncClient, test_movie):
        """Test get trending movies"""
        response = await client.get("/api/v1/movies/special/trending")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_new_releases(self, client: AsyncClient, test_movie):
        """Test get new releases"""
        response = await client.get("/api/v1/movies/special/new-releases")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
