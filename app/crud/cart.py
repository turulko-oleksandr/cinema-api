from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_
from sqlalchemy.orm import selectinload

from database.models.models import (
    Cart,
    CartItem,
    Movie,
    User,
    Order,
    OrderItem,
    OrderStatusEnum,
)


async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
    """Get user's cart or create if doesn't exist"""
    stmt = select(Cart).where(Cart.user_id == user_id)
    result = await db.execute(stmt)
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    return cart


async def get_cart_with_items(db: AsyncSession, user_id: int) -> Optional[Cart]:
    """Get user's cart with all items and movies"""
    stmt = (
        select(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.certification),
            selectinload(Cart.items)
            .selectinload(CartItem.movie)
            .selectinload(Movie.genres),
        )
        .where(Cart.user_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def is_movie_purchased(db: AsyncSession, user_id: int, movie_id: int) -> bool:
    """Check if the user has already purchased this movie."""
    stmt = (
        select(OrderItem)
        .join(Order)
        .where(
            Order.user_id == user_id,
            OrderItem.movie_id == movie_id,
            Order.status == OrderStatusEnum.PAID,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def add_item_to_cart(db: AsyncSession, user_id: int, movie_id: int) -> CartItem:
    """
    Add movie to user's cart.
    Validation: Movie must exist, not be purchased, and not already be in cart.
    """
    stmt = select(Movie).where(Movie.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        raise ValueError(f"Movie with id {movie_id} not found")

    if await is_movie_purchased(db, user_id, movie_id):
        raise ValueError("Repeat purchases are not allowed for this movie.")

    cart = await get_or_create_cart(db, user_id)

    stmt = select(CartItem).where(
        CartItem.cart_id == cart.id, CartItem.movie_id == movie_id
    )
    result = await db.execute(stmt)
    existing_item = result.scalar_one_or_none()

    if existing_item:
        raise ValueError("Movie already in cart.")

    cart_item = CartItem(cart_id=cart.id, movie_id=movie_id)

    db.add(cart_item)
    await db.commit()
    await db.refresh(cart_item)

    stmt = (
        select(CartItem)
        .options(
            selectinload(CartItem.movie).selectinload(Movie.certification),
            selectinload(CartItem.movie).selectinload(Movie.genres),
        )
        .where(CartItem.id == cart_item.id)
    )
    result = await db.execute(stmt)
    cart_item = result.scalar_one()

    return cart_item


async def remove_item_from_cart(db: AsyncSession, user_id: int, movie_id: int) -> bool:
    """Remove movie from user's cart"""
    cart = await get_or_create_cart(db, user_id)

    stmt = delete(CartItem).where(
        CartItem.cart_id == cart.id, CartItem.movie_id == movie_id
    )
    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount > 0


async def clear_cart(db: AsyncSession, user_id: int) -> bool:
    """Remove all items from user's cart"""
    cart = await get_or_create_cart(db, user_id)

    stmt = delete(CartItem).where(CartItem.cart_id == cart.id)
    await db.execute(stmt)
    await db.commit()

    return True


async def get_cart_total(db: AsyncSession, user_id: int) -> dict:
    """Calculate cart total price and item count"""
    cart = await get_cart_with_items(db, user_id)

    if not cart or not cart.items:
        return {"total_items": 0, "total_price": 0.0}

    total_price = sum(item.movie.price for item in cart.items)

    return {"total_items": len(cart.items), "total_price": float(total_price)}
