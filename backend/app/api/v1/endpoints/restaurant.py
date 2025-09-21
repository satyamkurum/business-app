# backend/app/api/v1/endpoints/restaurant.py
# backend/app/api/v1/endpoints/restaurant.py
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List

from app.db.mongodb import get_database
from app.schemas.faq import FAQ, FAQUpdate

router = APIRouter()

# This helper function is fine, but we won't use it as a dependency in the path operation.
async def get_restaurant_doc(db: AsyncIOMotorClient):
    restaurant = await db["restaurants"].find_one()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant document not found in the database.")
    return restaurant

@router.get("/faqs/", response_model=List[FAQ], tags=["FAQs"])
async def get_faqs(db: AsyncIOMotorClient = Depends(get_database)):
    # Call the helper function inside the endpoint logic instead
    restaurant = await get_restaurant_doc(db)
    # Safely get the 'faqs' list, returning an empty list if it doesn't exist
    return restaurant.get("faqs", [])

@router.put("/faqs/", response_model=List[FAQ], tags=["FAQs"])
async def update_faqs(faq_update: FAQUpdate, db: AsyncIOMotorClient = Depends(get_database)):
    # Call the helper function to ensure the document exists
    restaurant = await get_restaurant_doc(db)
    
    # Convert the list of Pydantic models to a list of dictionaries
    faqs_dict_list = [faq.model_dump() for faq in faq_update.faqs]
    
    # Update the 'faqs' field in the restaurant document
    await db["restaurants"].update_one(
        {"_id": restaurant["_id"]},
        {"$set": {"faqs": faqs_dict_list}}
    )
    
    # Fetch the updated document to return the new list of FAQs
    updated_restaurant = await get_restaurant_doc(db)
    return updated_restaurant.get("faqs", [])