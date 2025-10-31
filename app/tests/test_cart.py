import pytest
from httpx import AsyncClient


class TestCart:
    """Test cart endpoints"""

    async def test_get_empty_cart(self, client: AsyncClient, auth_headers, test_user):
        """Test get empty cart"""
        response = await client.get("/api/v1/cart/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 0

    async def test_add_item_to_cart(
        self, client: AsyncClient, auth_headers, test_movie
    ):
        """Test add movie to cart"""
        response = await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["movie_id"] == test_movie.id

    async def test_add_duplicate_item(
        self, client: AsyncClient, auth_headers, test_movie
    ):
        """Test add duplicate movie to cart"""
        # Add first time
        await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        # Add second time (should fail)
        response = await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        assert response.status_code == 409

    async def test_remove_item_from_cart(
        self, client: AsyncClient, auth_headers, test_movie
    ):
        """Test remove movie from cart"""
        # Add item first
        await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        # Remove item
        response = await client.delete(
            f"/api/v1/cart/items/{test_movie.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    async def test_clear_cart(self, client: AsyncClient, auth_headers, test_movie):
        """Test clear entire cart"""
        # Add item first
        await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        # Clear cart
        response = await client.delete("/api/v1/cart/", headers=auth_headers)
        assert response.status_code == 204

    async def test_get_cart_total(self, client: AsyncClient, auth_headers, test_movie):
        """Test get cart total"""
        # Add item first
        await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        # Get total
        response = await client.get("/api/v1/cart/total", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_price" in data
        assert "total_items" in data
        assert data["total_items"] == 1
