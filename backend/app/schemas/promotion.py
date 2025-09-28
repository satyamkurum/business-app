# backend/app/schemas/promotion.py
from pydantic import BaseModel, Field, BeforeValidator
from typing import Annotated, List, Optional
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class PromotionBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    start_date: datetime
    end_date: datetime
    discount_percentage: Optional[int] = Field(default=None, gt=0, le=100)
    image_url: Optional[str] = Field(default=None, description="A public URL for the promotion's banner image.") # <-- ADD THIS

class PromotionCreate(PromotionBase):
    pass

class Promotion(PromotionBase):
    id: PyObjectId = Field(alias="_id")

    class Config:
        populate_by_name = True
        from_attributes = True