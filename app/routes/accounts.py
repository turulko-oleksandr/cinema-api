from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_session import get_db
from database.models.models import User

router = APIRouter()

# Test db connection in endpoints
@router.get("/count")
async def get_user_count(db: AsyncSession = Depends(get_db)):

    query = select(func.count()).select_from(User)

    result = await db.execute(query)
    user_count = result.scalar_one()

    return {"user_count": user_count}
