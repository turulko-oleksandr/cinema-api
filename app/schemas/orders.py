from pydantic import BaseModel, ConfigDict, Field
from typing import List
from datetime import datetime
from decimal import Decimal

from database.models.models import OrderStatusEnum
from .movies import MovieListResponse


class OrderItemBase(BaseModel):
    movie_id: int
    price_at_order: Decimal


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    movie: MovieListResponse

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    status: OrderStatusEnum
    total_amount: Decimal


class OrderCreate(BaseModel):
    """Create order from cart (no fields needed)"""

    pass


class OrderStatusUpdate(BaseModel):
    status: OrderStatusEnum


class OrderResponse(OrderBase):
    id: int
    user_id: int
    created_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedOrdersResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
