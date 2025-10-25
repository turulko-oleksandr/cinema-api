from app.celery_app import celery_app
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from app.config.settings import Settings
from app.database.models.models import ActivationToken, PasswordResetToken

settings = Settings()

# Sync engine for Celery
engine = create_engine(settings.SYNC_PGSQL_DB_LINK)
SessionLocal = sessionmaker(bind=engine)


@celery_app.task
def cleanup_expired_tokens():
    """Clean up expired activation and password reset tokens"""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Delete expired activation tokens
        activation_result = db.execute(
            delete(ActivationToken).where(ActivationToken.expires_at < now)
        )

        # Delete expired password reset tokens
        reset_result = db.execute(
            delete(PasswordResetToken).where(PasswordResetToken.expires_at < now)
        )

        db.commit()

        return {
            "activation_tokens_deleted": activation_result.rowcount,
            "reset_tokens_deleted": reset_result.rowcount,
            "timestamp": now.isoformat(),
        }
    except Exception as e:
        db.rollback()
        print(f"Error cleaning up tokens: {e}")
        return {"error": str(e)}
    finally:
        db.close()
