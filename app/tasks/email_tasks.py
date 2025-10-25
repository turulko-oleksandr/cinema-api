from app.celery_app import celery_app
from app.notifications.email_service import get_email_service


@celery_app.task(bind=True, max_retries=3)
def send_activation_email_task(self, to_email: str, activation_token: str):
    """Celery task to send activation email"""
    try:
        email_service = get_email_service()
        success = email_service.send_activation_email(to_email, activation_token)
        if not success:
            raise Exception("Failed to send email")
        return {"status": "sent", "email": to_email}
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_password_reset_email_task(self, to_email: str, reset_token: str):
    """Celery task to send password reset email"""
    try:
        email_service = get_email_service()
        success = email_service.send_password_reset_email(to_email, reset_token)
        if not success:
            raise Exception("Failed to send email")
        return {"status": "sent", "email": to_email}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_order_confirmation_email_task(
    self, to_email: str, order_id: int, total_amount: float, items: list
):
    """Celery task to send order confirmation email"""
    try:
        email_service = get_email_service()
        success = email_service.send_order_confirmation_email(
            to_email, order_id, total_amount, items
        )
        if not success:
            raise Exception("Failed to send email")
        return {"status": "sent", "email": to_email, "order_id": order_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_password_changed_email_task(self, to_email: str):
    """Celery task to send password changed notification"""
    try:
        email_service = get_email_service()
        success = email_service.send_password_changed_email(to_email)
        if not success:
            raise Exception("Failed to send email")
        return {"status": "sent", "email": to_email}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))
