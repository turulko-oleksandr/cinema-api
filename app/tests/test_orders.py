# app/tests/test_orders.py

"""
Tests for order endpoints
"""

import pytest
from httpx import AsyncClient


class TestOrderCreation:
    """Test order creation"""

    async def test_create_order_from_cart(
        self, client: AsyncClient, auth_headers, test_movie
    ):
        """Test create order from cart"""
        # Add item to cart
        await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        # Create order
        response = await client.post("/api/v1/orders/", headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "status" in data
        assert data["status"] == "pending"

    async def test_create_order_empty_cart(self, client: AsyncClient, auth_headers):
        """Test create order with empty cart (should fail)"""
        response = await client.post("/api/v1/orders/", headers=auth_headers)
        assert response.status_code == 400


class TestOrderList:
    """Test order listing"""

    async def test_get_user_orders(self, client: AsyncClient, auth_headers, test_movie):
        """Test get user's orders"""
        # Create order first
        await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        await client.post("/api/v1/orders/", headers=auth_headers)

        # Get orders
        response = await client.get("/api/v1/orders/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestOrderDetail:
    """Test order detail"""

    async def test_get_order_by_id(self, client: AsyncClient, auth_headers, test_movie):
        """Test get order by ID"""
        # Create order first
        await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        create_response = await client.post("/api/v1/orders/", headers=auth_headers)
        order_id = create_response.json()["id"]

        # Get order
        response = await client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id


class TestOrderStatus:
    """Test order status updates"""

    async def test_cancel_order(self, client: AsyncClient, auth_headers, test_movie):
        """Test cancel pending order"""
        # Create order
        await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        create_response = await client.post("/api/v1/orders/", headers=auth_headers)
        order_id = create_response.json()["id"]

        # Cancel order
        response = await client.patch(
            f"/api/v1/orders/{order_id}/status",
            headers=auth_headers,
            json={"status": "canceled"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "canceled"


class TestAdminOrders:
    """Test admin order operations"""

    async def test_get_all_orders_as_admin(
        self, client: AsyncClient, admin_headers, test_movie, auth_headers
    ):
        """Test get all orders as admin"""
        # Create order as regular user
        await client.post(
            "/api/v1/cart/items",
            headers=auth_headers,
            json={"movie_id": test_movie.id},
        )
        await client.post("/api/v1/orders/", headers=auth_headers)

        # Get all orders as admin
        response = await client.get("/api/v1/orders/all", headers=admin_headers)
        assert response.status_code == 200

    async def test_get_all_orders_unauthorized(self, client: AsyncClient, auth_headers):
        """Test get all orders as regular user (should fail)"""
        response = await client.get("/api/v1/orders/all", headers=auth_headers)
        assert response.status_code == 403
