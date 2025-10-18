from fastapi import FastAPI
from app.routes import *
from database.models.models import Base
from database.session_sqlite import engine


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app = FastAPI(title="Cinema", description="")

api_version_prefix = "/api/v1"

app.include_router(
    accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"]
)
app.include_router(movie_router, prefix=f"{api_version_prefix}/movies", tags=["Movies"])
