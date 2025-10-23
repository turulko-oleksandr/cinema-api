from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from database.models.models import (
    Order,
    OrderItem,
    Cart,
    CartItem,
    Movie,
    OrderStatusEnum,
)


async def create_order_from_cart(db: AsyncSession, user_id: int) -> Order:
    """
    Create order from user's cart
    """
    stmt = (
        select(Cart)
        .options(selectinload(Cart.items).selectinload(CartItem.movie))
        .where(Cart.user_id == user_id)
    )
    result = await db.execute(stmt)
    cart = result.scalar_one_or_none()

    if not cart or not cart.items:
        raise ValueError("Cart is empty")

    total_amount = sum(item.movie.price for item in cart.items)

    order = Order(
        user_id=user_id, status=OrderStatusEnum.PENDING, total_amount=total_amount
    )

    db.add(order)
    await db.flush()

    for cart_item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            movie_id=cart_item.movie_id,
            price_at_order=cart_item.movie.price,
        )
        db.add(order_item)

    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))

    await db.commit()
    await db.refresh(order)

    stmt = (
        select(Order)
        .options(
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.certification),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.genres),
        )
        .where(Order.id == order.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_order(
    db: AsyncSession, order_id: int, user_id: Optional[int] = None
) -> Optional[Order]:
    """
    Get order by ID with items
    """
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.certification),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.genres),
        )
        .where(Order.id == order_id)
    )

    if user_id:
        stmt = stmt.where(Order.user_id == user_id)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_orders(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    status: Optional[OrderStatusEnum] = None,
) -> tuple[List[Order], int]:
    """
    Get user's orders with pagination
    """
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.certification),
            selectinload(Order.items)
            .selectinload(OrderItem.movie)
            .selectinload(Movie.genres),
        )
        .where(Order.user_id == user_id)
    )

    if status:
        stmt = stmt.where(Order.status == status)

    stmt = stmt.order_by(Order.created_at.desc())

    from sqlalchemy import func

    count_stmt = select(func.count()).select_from(Order).where(Order.user_id == user_id)
    if status:
        count_stmt = count_stmt.where(Order.status == status)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return list(orders), total


async def get_all_orders(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    status: Optional[OrderStatusEnum] = None,
) -> tuple[List[Order], int]:
    """
    Get all orders (admin)
    """
    stmt = select(Order).options(
        selectinload(Order.items)
        .selectinload(OrderItem.movie)
        .selectinload(Movie.certification),
        selectinload(Order.items)
        .selectinload(OrderItem.movie)
        .selectinload(Movie.genres),
    )

    if status:
        stmt = stmt.where(Order.status == status)

    stmt = stmt.order_by(Order.created_at.desc())

    from sqlalchemy import func

    count_stmt = select(func.count()).select_from(Order)
    if status:
        count_stmt = count_stmt.where(Order.status == status)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return list(orders), total


async def update_order_status(
    db: AsyncSession,
    order_id: int,
    status: OrderStatusEnum,
    user_id: Optional[int] = None,
) -> Optional[Order]:
    """
    Update order status
    """
    stmt = select(Order).where(Order.id == order_id)

    if user_id:
        stmt = stmt.where(Order.user_id == user_id)

    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        return None

    order.status = status
    await db.commit()
    await db.refresh(order)

    return order


async def cancel_order(
    db: AsyncSession, order_id: int, user_id: int
) -> Optional[Order]:
    """
    Cancel order (only PENDING orders)
    """
    order = await get_order(db, order_id, user_id)

    if not order:
        return None

    if order.status != OrderStatusEnum.PENDING:
        raise ValueError("Only pending orders can be cancelled")

    order.status = OrderStatusEnum.CANCELED
    await db.commit()
    await db.refresh(order)

    return order


async def delete_order(db: AsyncSession, order_id: int) -> bool:
    """
    Delete order (admin only) using ORM cascade.
    """
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        return False

    await db.delete(order)
    await db.commit()

    return True
