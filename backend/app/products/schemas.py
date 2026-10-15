from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Department = Literal["Men", "Women", "Kids"]


class ProductResponse(BaseModel):
    id: int
    name: str
    department: Department
    category: str
    description: str
    price: Decimal = Field(ge=0)
    stock: int = Field(ge=0)
    image_url: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)