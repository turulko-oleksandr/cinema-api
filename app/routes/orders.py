from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_session import get_db
from app.crud.orders import (
    create_order_from_cart,
    get_order,
    get_user_orders,
    get_all_orders,
    update_order_status,
    cancel_order,
    delete_order,
)
from app.schemas.orders import (
    OrderResponse,
    OrderCreate,
    OrderStatusUpdate,
    PaginatedOrdersResponse,
)
from app.database.models.models import OrderStatusEnum, User, UserGroupEnum
from app.services.role_manager import get_current_user
from app.crud.payments import get_payment_by_order_id
from app.services.stripe_service import get_stripe_service

router = APIRouter(tags=["Orders"])


def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role"""
    if current_user.group.name != UserGroupEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order from cart",
)
async def create_order(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new order from user's cart
    """
    try:
        order = await create_order_from_cart(db, current_user.id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=PaginatedOrdersResponse, summary="Get user's orders")
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatusEnum] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's orders with pagination
    """
    orders, total = await get_user_orders(
        db, current_user.id, skip=skip, limit=limit, status=status
    )

    return PaginatedOrdersResponse(items=orders, total=total, skip=skip, limit=limit)


@router.get(
    "/all", response_model=PaginatedOrdersResponse, summary="Get all orders (Admin)"
)
async def get_all_orders_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatusEnum] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all orders (admin only)
    """
    orders, total = await get_all_orders(db, skip=skip, limit=limit, status=status)

    return PaginatedOrdersResponse(items=orders, total=total, skip=skip, limit=limit)


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order by ID")
async def get_order_endpoint(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get order by ID
    """
    order = await get_order(db, order_id, current_user.id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found",
        )

    return order


@router.patch(
    "/{order_id}/status", response_model=OrderResponse, summary="Update order status"
)
async def update_order_status_endpoint(
    order_id: int,
    payload: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update order status (admin can update any, user can only cancel)
    """
    is_admin = current_user.group.name == UserGroupEnum.ADMIN

    if not is_admin:
        if payload.status != OrderStatusEnum.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Users can only cancel orders",
            )

        try:
            order = await cancel_order(db, order_id, current_user.id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        order = await update_order_status(db, order_id, payload.status)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found",
        )

    return order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete order (Admin)",
)
async def delete_order_endpoint(
    order_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete order (admin only)
    """
    deleted = await delete_order(db, order_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found",
        )

    return None


@router.post(
    "/{order_id}/checkout", summary="Create Stripe checkout session for payment"
)
async def create_checkout_session(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create Stripe Checkout session for order payment

    Returns a checkout URL that redirects user to Stripe payment page
    """
    # Get order with items
    order = await get_order(db, order_id, current_user.id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found"
        )

    # Check if order is pending
    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is already {order.status.value}. Only pending orders can be paid.",
        )

    # Check if payment already exists
    existing_payment = await get_payment_by_order_id(db, order_id)
    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already exists for this order",
        )

    # Prepare line items for Stripe
    line_items = []
    for item in order.items:
        line_items.append(
            {
                "name": item.movie.name,
                "year": item.movie.year,
                "time": item.movie.time,
                "price": float(item.price_at_order),
            }
        )

    # Create Stripe checkout session
    try:
        stripe_service = get_stripe_service()
        session = stripe_service.create_checkout_session(
            order_id=order.id,
            user_id=current_user.id,
            user_email=current_user.email,
            line_items=line_items,
        )

        return {
            "order_id": order.id,
            "checkout_url": session["checkout_url"],
            "session_id": session["session_id"],
            "expires_in": "1 hour",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{order_id}/payment-status", summary="Check payment status for order")
async def check_payment_status(
    order_id: int,
    session_id: str = Query(..., description="Stripe session ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check Stripe payment status for an order

    Used by frontend after redirect from Stripe
    """
    # Verify order belongs to user
    order = await get_order(db, order_id, current_user.id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found"
        )

    # Retrieve Stripe session
    try:
        stripe_service = get_stripe_service()
        session = stripe_service.retrieve_session(session_id)

        return {
            "order_id": order.id,
            "stripe_session_id": session["id"],
            "payment_status": session["payment_status"],
            "order_status": order.status.value,
            "amount_paid": session["amount_total"],
            "currency": session["currency"],
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
