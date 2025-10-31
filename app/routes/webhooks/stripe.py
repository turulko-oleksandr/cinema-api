from fastapi import APIRouter, Request, HTTPException, status, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db_session import get_db
from app.services.stripe_service import get_stripe_service
from app.crud.orders import update_order_status, get_order
from app.crud.payments import create_payment_from_session, get_payment_by_session_id
from app.database.models.models import OrderStatusEnum, PaymentStatusEnum
from app.tasks.email_tasks import send_order_confirmation_email_task

router = APIRouter(tags=["Stripe"])


@router.post("/stripe", summary="Stripe webhook handler")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Stripe webhook events

    Important: Configure this URL in your Stripe Dashboard
    Webhook endpoint: https://app.com/api/v1/webhooks/stripe
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )

    # Verify webhook signature
    try:
        stripe_service = get_stripe_service()
        event = stripe_service.verify_webhook_signature(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Handle different event types
    event_type = event["type"]

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]

        # Extract metadata
        order_id = int(session["metadata"]["order_id"])
        user_id = int(session["metadata"]["user_id"])

        # Check if payment already recorded
        existing_payment = await get_payment_by_session_id(db, session["id"])
        if existing_payment:
            return {"status": "success", "message": "Payment already recorded"}

        # Create payment record
        await create_payment_from_session(
            db=db,
            session_id=session["id"],
            order_id=order_id,
            user_id=user_id,
            amount=session["amount_total"] / 100,
            currency=session["currency"],
            payment_intent_id=session["payment_intent"],
            status=PaymentStatusEnum.SUCCESSFUL.value,
        )

        # Update order status
        await update_order_status(db, order_id, OrderStatusEnum.PAID)

        # Get order details for email
        order = await get_order(db, order_id)
        if order:
            items = [
                {
                    "name": item.movie.name,
                    "year": item.movie.year,
                    "price": float(item.price_at_order),
                }
                for item in order.items
            ]

            # Send confirmation email asynchronously
            send_order_confirmation_email_task.delay(
                session["customer_email"], order_id, float(order.total_amount), items
            )

    elif event_type == "checkout.session.expired":
        session = event["data"]["object"]
        order_id = int(session["metadata"]["order_id"])

        # Cancel order if session expired
        await update_order_status(db, order_id, OrderStatusEnum.CANCELED)

    elif event_type == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        pass

    return {"status": "success"}
