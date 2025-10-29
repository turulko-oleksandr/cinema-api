from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    accounts,
    cart,
    certifiacations,
    directors,
    genres,
    movies,
    orders,
    stars,
)
from app.routes.webhooks import stripe

app = FastAPI(
    title="Cinema API",
    description="API for Online Cinema Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production will change
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router)
app.include_router(movies.router)
app.include_router(genres.router)
app.include_router(directors.router)
app.include_router(stars.router)
app.include_router(certifiacations.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(stripe.router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Cinema API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}