from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    total_amount: Decimal
    currency: str
    status: str
    stripe_payment_intent_id: str | None = None
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class PaymentIntentResponse(BaseModel):
    order_id: int
    payment_intent_id: str
    client_secret: str
    amount: int
    currency: str