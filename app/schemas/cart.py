from pydantic import BaseModel, ConfigDict, Field
from typing import List
from datetime import datetime
from decimal import Decimal

from .movies import MovieListResponse


class CartItemBase(BaseModel):
    movie_id: int


class CartItemCreate(CartItemBase):
    pass


class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    movie_id: int
    movie: MovieListResponse
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartBase(BaseModel):
    user_id: int


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CartTotalResponse(BaseModel):
    total_items: int = Field(..., description="Number of items in cart")
    total_price: float = Field(..., description="Total price of all items")

    model_config = ConfigDict(from_attributes=True)
