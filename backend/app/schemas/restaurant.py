from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class RestaurantDetails(BaseModel):
    """
    Pydantic schema for validating and serializing the core details of the restaurant.
    This model is used to manage the content for the 'About Us' page.
    """
    name: str = Field(
        ..., 
        max_length=100,
        examples=["HFC Restaurant"],
        description="The official name of the restaurant."
    )
    
    about_text: str = Field(
        ..., 
        description="A warm, engaging paragraph about the restaurant's story, mission, or atmosphere."
    )
    
    gallery_image_urls: List[HttpUrl] = Field(
        default=[], 
        description="A list of public URLs for the photo gallery on the 'About Us' page."
    )

    class Config:
        """Pydantic model configuration."""
        # This allows the model to be created from database objects
        from_attributes = True
        # Provides an example for the API documentation
        json_schema_extra = {
            "example": {
                "name": "HFC Restaurant & Bar",
                "about_text": "Welcome to HFC, where culinary passion meets timeless elegance. Our mission is to provide an unforgettable dining experience...",
                "gallery_image_urls": [
                    "https://images.unsplash.com/photo-1552566626-52f8b828add9",
                    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4"
                ]
            }
        }
