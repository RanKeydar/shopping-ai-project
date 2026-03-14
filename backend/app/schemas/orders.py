from datetime import datetime

from pydantic import BaseModel, Field


class AddItemRequest(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)


class UpdateQuantityRequest(BaseModel):
    item_id: int
    quantity: int = Field(ge=0)


class CheckoutRequest(BaseModel):
    shipping_address: str = Field(min_length=3, max_length=255)


class OrderItemResponse(BaseModel):
    item_id: int
    name: str
    quantity: int
    unit_price: float
    line_total: float


class OrderResponse(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    shipping_address: str | None
    status: str
    total_price: float
    items: list[OrderItemResponse]