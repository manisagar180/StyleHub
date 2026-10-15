from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CartProductResponse(BaseModel):
    id: int
    name: str
    category: str
    price: Decimal
    image_url: str | None = None
    stock: int

    model_config = ConfigDict(from_attributes=True)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: CartProductResponse
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_items: int
    total_price: Decimal