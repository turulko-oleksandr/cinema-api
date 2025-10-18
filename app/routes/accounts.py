from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.session_postresql import get_db
from database.models.models import User

router = APIRouter()


@router.get("/")
async def root(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count(User.id)))
    count_of_users = result.scalar()
    return {"users_count": count_of_users}
