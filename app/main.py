import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    accounts_router,
    movie_router,
    genres_router,
    directors_router,
    stars_router,
    certifications_router,
    cart_router,
    orders_router,
    stripe_router,
)
from app.routes.webhooks import stripe

load_dotenv()
app = FastAPI(
    title="Cinema API", description="API for Online Cinema Platform", version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(cart_router, prefix="/api/v1/cart", tags=["Cart"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(stripe_router, prefix="/api/v1/webhooks/stripe", tags=["Stripe"])


@app.get("/")
async def root():
    return {"message": "Welcome to Cinema API", "docs": "/docs", "redoc": "/redoc"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
