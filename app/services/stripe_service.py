import stripe
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone

from app.config.settings import Settings


class StripeService:
    def __init__(self, settings: Settings):
        self.settings = settings
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.base_url = settings.FRONTEND_URL or "http://localhost:3000"

    def create_checkout_session(
        self,
        order_id: int,
        user_id: int,
        user_email: str,
        line_items: List[Dict],
    ) -> Dict:
        """
        Create Stripe Checkout Session

        Args:
            order_id: Order ID
            user_id: User ID
            user_email: User email
            line_items: [{"name": "Movie", "year": 2024, "price": 9.99}]

        Returns:
            {"session_id": "...", "checkout_url": "..."}
        """
        try:
            # Prepare line items for Stripe
            stripe_line_items = []
            for item in line_items:
                stripe_line_items.append(
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": item["name"],
                                "description": f"{item.get('year', 'N/A')} • {item.get('time', 'N/A')} min",
                            },
                            "unit_amount": int(
                                float(item["price"]) * 100
                            ),  # Convert to cents
                        },
                        "quantity": 1,
                    }
                )

            # Create Stripe session
            session = stripe.checkout.Session.create(
                line_items=stripe_line_items,
                metadata={
                    "order_id": str(order_id),
                    "user_id": str(user_id),
                },
                mode="payment",
                success_url=f"{self.base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{self.base_url}/payment/cancel?order_id={order_id}",
                customer_email=user_email,
                expires_at=int(
                    (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
                ),
            )

            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "payment_status": session.payment_status,
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {str(e)}")

    def retrieve_session(self, session_id: str) -> Dict:
        """Retrieve Stripe session details"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "id": session.id,
                "payment_status": session.payment_status,
                "amount_total": session.amount_total / 100,  # Convert from cents
                "currency": session.currency,
                "customer_email": session.customer_email,
                "payment_intent": session.payment_intent,
                "metadata": session.metadata,
            }
        except stripe.error.StripeError as e:
            raise ValueError(f"Stripe error: {str(e)}")

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> Dict:
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")


_stripe_service = None


def get_stripe_service() -> StripeService:
    global _stripe_service
    if _stripe_service is None:
        from config.settings import Settings

        _stripe_service = StripeService(Settings())
    return _stripe_service
