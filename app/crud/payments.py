from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.models.models import Payment, PaymentItem, Order, OrderItem


async def create_payment_from_session(
    db: AsyncSession,
    session_id: str,
    order_id: int,
    user_id: int,
    amount: float,
    currency: str,
    payment_intent_id: str,
    status: str = "successful",
) -> Payment:
    """Create payment record from Stripe session"""

    # Create payment
    payment = Payment(
        user_id=user_id,
        order_id=order_id,
        session_id=session_id,
        payment_intent_id=payment_intent_id,
        amount=amount,
        currency=currency,
        status=status,
    )

    db.add(payment)
    await db.flush()

    # Get order items
    order_items = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )

    # Create payment items
    for order_item in order_items.scalars().all():
        payment_item = PaymentItem(
            payment_id=payment.id,
            order_item_id=order_item.id,
            price_at_payment=order_item.price_at_order,
        )
        db.add(payment_item)

    await db.commit()
    await db.refresh(payment)

    return payment


async def get_payment_by_session_id(
    db: AsyncSession, session_id: str
) -> Optional[Payment]:
    """Get payment by Stripe session ID"""
    stmt = select(Payment).where(Payment.session_id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_payment_by_order_id(db: AsyncSession, order_id: int) -> Optional[Payment]:
    """Get payment by order ID"""
    stmt = (
        select(Payment)
        .options(selectinload(Payment.items))
        .where(Payment.order_id == order_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
