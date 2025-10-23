from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_session import get_db
from crud.cart import (
    get_cart_with_items,
    add_item_to_cart,
    remove_item_from_cart,
    clear_cart,
    get_cart_total,
)
from schemas.cart import (
    CartResponse,
    CartItemCreate,
    CartItemResponse,
    CartTotalResponse,
)
from services.role_manager import get_current_user
from database.models.models import User

router = APIRouter(tags=["Cart"])


@router.get("/", response_model=CartResponse, summary="Get user's cart")
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's cart with all items"""
    cart = await get_cart_with_items(db, current_user.id)

    if not cart:
        return CartResponse(id=0, user_id=current_user.id, items=[])

    return cart


@router.post(
    "/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
)
async def add_to_cart(
    payload: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a movie to the user's cart"""
    try:
        cart_item = await add_item_to_cart(db, current_user.id, payload.movie_id)
        return cart_item
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg)
        elif "already in cart" in error_msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)


@router.delete(
    "/items/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from cart",
)
async def remove_from_cart(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a movie from the user's cart"""
    removed = await remove_item_from_cart(db, current_user.id, movie_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with id {movie_id} not found in cart",
        )

    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT, summary="Clear cart")
async def clear_cart_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove all items from the user's cart"""
    await clear_cart(db, current_user.id)
    return None


@router.get("/total", response_model=CartTotalResponse, summary="Get cart total")
async def get_cart_total_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get total price and item count for user's cart"""
    total = await get_cart_total(db, current_user.id)
    return total
