# backend/app/schemas/category.py

from pydantic import BaseModel, Field, BeforeValidator
from typing import Annotated

# This is the magic that allows Pydantic to handle MongoDB's ObjectId
# It tells Pydantic: "Before you validate this field, if it's an ObjectId,
# just convert it to a string."
PyObjectId = Annotated[str, BeforeValidator(str)]

class CategoryBase(BaseModel):
    """Shared base attributes for a category."""
    name: str = Field(..., max_length=100, examples=["Tandoori Starters"])
    description: str | None = Field(default=None, max_length=300, examples=["Chargrilled appetizers from our clay oven."])
    display_order: int = Field(..., gt=0, examples=[1])

class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass

class Category(CategoryBase):
    """Schema for reading a category from the database."""
    # We now use our custom PyObjectId type for the id field.
    id: PyObjectId = Field(alias="_id")

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        from_attributes = True
        json_encoders = {
            # This is an alternative way to handle ObjectId, but the
            # BeforeValidator is often cleaner. Good to have for reference.
            # ObjectId: str 
        }