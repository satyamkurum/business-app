from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# --- Sub-models for better organization ---

class OrderItem(BaseModel):
    """Represents a single item within a customer's order."""
    name: str
    quantity: int
    price: float

class DeliveryInfo(BaseModel):
    """Stores the details of the delivery partner for a shipped order."""
    name: str = Field(..., examples=["Rohan S."], description="Name of the delivery person.")
    phone: str = Field(..., examples=["+919988776655"], description="Contact number for the delivery person.")

# --- Main Order Schema ---

class Order(BaseModel):
    """
    The definitive schema for a customer order, including its lifecycle status and delivery details.
    This model is the single source of truth for an order's structure in the application.
    """
    merchant_transaction_id: str = Field(
        description="Our internal, unique ID for this transaction."
    )
    
    phonepe_transaction_id: Optional[str] = Field(
        default=None, 
        description="The unique transaction ID provided by PhonePe after payment."
    )
    
    user_id: str = Field(
        description="The Firebase UID of the customer who placed the order."
    )
    
    items: List[OrderItem] = Field(
        description="A list of all the items included in this order."
    )
    
    total_amount: int = Field(
        description="The final, total amount of the order in paisa (e.g., 10000 for ₹100.00)."
    )
    
    status: Literal[
        "PENDING", 
        "SUCCESS", 
        "FAILED", 
        "CONFIRMED", 
        "PREPARING", 
        "SHIPPED"
    ] = Field(
        default="PENDING",
        description="The current stage of the order in the fulfillment lifecycle."
    )
    
    delivery_info: Optional[DeliveryInfo] = Field(
        default=None,
        description="Contains delivery partner details. This is only set when the status is 'SHIPPED'."
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="The timestamp when the order was first created."
    )

    class Config:
        """Pydantic model configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "merchant_transaction_id": "tx_123456789",
                "phonepe_transaction_id": "pay_abcdef123",
                "user_id": "firebase_user_abc",
                "items": [
                    {"name": "Margherita Pizza", "quantity": 1, "price": 350.0},
                    {"name": "Hakka Noodles", "quantity": 2, "price": 250.0}
                ],
                "total_amount": 85000,
                "status": "PREPARING",
                "delivery_info": None,
                "created_at": "2025-09-28T10:00:00Z"
            }
        }

