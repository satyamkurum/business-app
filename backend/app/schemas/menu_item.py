# backend/app/schemas/menu_item.py

from pydantic import BaseModel, Field, BeforeValidator
from typing import List, Optional, Annotated

# Re-use our custom ObjectId type
PyObjectId = Annotated[str, BeforeValidator(str)]

class Pricing(BaseModel):
    size: str = Field(..., max_length=50, examples=["Full"])
    price: float = Field(..., gt=0, examples=[450.00])

class DietaryInfo(BaseModel):
    is_vegan_available: bool = False
    is_gluten_free: bool = False
    is_jain_available: bool = False

class CustomizationOption(BaseModel):
    option_name: str = Field(..., max_length=100, examples=["Spice Level"])
    choices: List[str] = Field(..., examples=[["Mild", "Medium", "Spicy"]])

class MenuItemBase(BaseModel):
    name: str = Field(..., max_length=100, examples=["Shahi Paneer Pasanda"])
    description: str = Field(..., max_length=500)
    category_id: str = Field(..., examples=["67e4e8d3e9d8f1e3c5d6e7f8"])
    pricing: List[Pricing]
    image_url: Optional[str] = Field(default=None, examples=["https://cdn.example.com/paneer.jpg"])
    tags: List[str] = Field(default=[], examples=[["Bestseller", "Creamy"]])
    dietary_info: DietaryInfo
    customization_options: List[CustomizationOption] = Field(default=[])
    key_ingredients: List[str] = Field(default=[])
    is_available: bool = True
    prep_time_minutes: Optional[int] = Field(default=None, gt=0)

class MenuItemCreate(MenuItemBase):
    pass

class MenuItem(MenuItemBase):
    # Use our custom type for the id field here as well
    id: PyObjectId = Field(..., alias="_id")

    class Config:
        populate_by_name = True
        from_attributes = True