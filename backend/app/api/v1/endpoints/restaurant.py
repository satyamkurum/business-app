from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from app.db.mongodb import get_database
from app.schemas.faq import FAQ, FAQUpdate
from app.schemas.restaurant import RestaurantDetails
from app.core.security import get_api_key

router = APIRouter()

# This is our helper function.
async def get_restaurant_doc(db: AsyncIOMotorClient):
    restaurant = await db["restaurants"].find_one()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant details not found in the database.")
    return restaurant

@router.get("/faqs/", response_model=List[FAQ], tags=["Restaurant"])
async def get_faqs(db: AsyncIOMotorClient = Depends(get_database)):
    # CORRECTED: Call the helper with the correct name
    restaurant = await get_restaurant_doc(db)
    return restaurant.get("faqs", [])

@router.put("/faqs/", response_model=List[FAQ], tags=["Restaurant"])
async def update_faqs(faq_update: FAQUpdate, db: AsyncIOMotorClient = Depends(get_database), api_key: str = Depends(get_api_key)):
    # CORRECTED: Call the helper with the correct name
    restaurant = await get_restaurant_doc(db)
    faqs_dict = [faq.model_dump() for faq in faq_update.faqs]
    
    await db["restaurants"].update_one(
        {"_id": restaurant["_id"]},
        {"$set": {"faqs": faqs_dict}}
    )
    
    updated_restaurant = await get_restaurant_doc(db)
    return updated_restaurant.get("faqs", [])

@router.get("/details", response_model=RestaurantDetails, tags=["Restaurant"])
async def get_restaurant_details(db: AsyncIOMotorClient = Depends(get_database)):
    restaurant = await get_restaurant_doc(db)
    return RestaurantDetails(
        name=restaurant.get("name", "HFC Restaurant"),
        about_text=restaurant.get("about_text", "Welcome! Details coming soon."),
        gallery_image_urls=restaurant.get("gallery_image_urls", [])
    )

@router.put("/details", response_model=RestaurantDetails, tags=["Restaurant"])
async def update_restaurant_details(
    details: RestaurantDetails,
    db: AsyncIOMotorClient = Depends(get_database),
    api_key: str = Depends(get_api_key)
):
    """
    Updates the restaurant's core details (name, about text, gallery).
    """
    restaurant = await get_restaurant_doc(db)
    
    # --- THIS IS THE DEFINITIVE FIX ---
    # We use .model_dump(mode='json') to convert complex Pydantic types
    # like HttpUrl back into simple, database-friendly strings before saving.
    update_data = details.model_dump(mode='json')
    
    await db["restaurants"].update_one(
        {"_id": restaurant["_id"]},
        {"$set": update_data}
    )
    
    updated_restaurant = await get_restaurant_doc(db)
    return RestaurantDetails(**updated_restaurant)
