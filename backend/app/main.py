from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.auth import router as auth_router
from app.cart.router import router as cart_router
from app.database import Base, engine
from app.orders.router import router as orders_router
from app.orders.webhook import router as payments_router
from app.products.router import router as products_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create missing tables without deleting existing data.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="StyleHub API",
    description="Backend API for the StyleHub Fashion Mini Store",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the local React/Vite frontend to access the FastAPI API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Welcome to StyleHub API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(auth_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)