from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class OrderItem(BaseModel):
    name: str
    quantity: int
    price: float

class Order(BaseModel):
    merchant_transaction_id: str
    phonepe_transaction_id: str | None = None
    user_id: str
    items: List[OrderItem]
    total_amount: int # Amount in paisa
    status: str = Field(default="PENDING")
    created_at: datetime = Field(default_factory=datetime.utcnow)
