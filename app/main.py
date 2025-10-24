from fastapi import FastAPI
from routes import *
from database.models.models import Base
from database.db_session import engine


app = FastAPI(title="Cinema", description="")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


api_version_prefix = "/api/v1"

app.include_router(
    accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["Accounts"]
)
app.include_router(movie_router, prefix=f"{api_version_prefix}/movies", tags=["Movies"])
app.include_router(
    genres_router, prefix=f"{api_version_prefix}/genres", tags=["Genres"]
)
app.include_router(
    directors_router, prefix=f"{api_version_prefix}/directors", tags=["Directors"]
)
app.include_router(stars_router, prefix=f"{api_version_prefix}/stars", tags=["Stars"])
app.include_router(
    certifications_router,
    prefix=f"{api_version_prefix}/certifications",
    tags=["Certifications"],
)
app.include_router(cart.router, prefix="/api/v1/cart", tags=["Cart"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
