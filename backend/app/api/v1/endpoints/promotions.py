# backend/app/api/v1/endpoints/promotions.py

from fastapi import APIRouter, Depends, HTTPException, status, Response
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import List

from app.db.mongodb import get_database
from app.schemas.promotion import Promotion, PromotionCreate

router = APIRouter()

@router.post("/", response_model=Promotion, status_code=status.HTTP_201_CREATED, tags=["Promotions"])
async def create_promotion(promo: PromotionCreate, db: AsyncIOMotorClient = Depends(get_database)):
    promo_dict = promo.model_dump()
    result = await db["promotions"].insert_one(promo_dict)
    created_promo = await db["promotions"].find_one({"_id": result.inserted_id})
    return Promotion.model_validate(created_promo)

@router.get("/", response_model=List[Promotion], tags=["Promotions"])
async def list_promotions(db: AsyncIOMotorClient = Depends(get_database)):
    promos_cursor = db["promotions"].find()
    promos = await promos_cursor.to_list(length=100)
    return [Promotion.model_validate(promo) for promo in promos]

@router.put("/{promo_id}", response_model=Promotion, tags=["Promotions"])
async def update_promotion(promo_id: str, promo_update: PromotionCreate, db: AsyncIOMotorClient = Depends(get_database)):
    try:
        promo_oid = ObjectId(promo_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    
    update_data = promo_update.model_dump(exclude_unset=True)
    result = await db["promotions"].update_one({"_id": promo_oid}, {"$set": update_data})

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Promotion with id {promo_id} not found")
        
    updated_promo = await db["promotions"].find_one({"_id": promo_oid})
    return Promotion.model_validate(updated_promo)

@router.delete("/{promo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Promotions"])
async def delete_promotion(promo_id: str, db: AsyncIOMotorClient = Depends(get_database)):
    try:
        promo_oid = ObjectId(promo_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    result = await db["promotions"].delete_one({"_id": promo_oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Promotion with id {promo_id} not found")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)