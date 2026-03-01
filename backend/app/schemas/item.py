from pydantic import BaseModel


class ItemOut(BaseModel):
    id: int
    name: str
    price_usd: float
    stock_qty: int

    class Config:
        from_attributes = True