from fastapi import APIRouter, Depends, HTTPException, Body, status
from motor.motor_asyncio import AsyncIOMotorClient
from firebase_admin import auth
from app.db.mongodb import get_database
from app.schemas.user import User
from app.core.security import get_current_user # Assuming this is your dependency
from typing import List
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("/sync-user", response_model=User, tags=["Authentication"])
async def sync_user(
    token: str = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Receives a Firebase ID token, verifies it, and efficiently creates or updates the user in MongoDB using an upsert operation.
    """
    print("\n--- Received API call for /sync-user ---")
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name', email)
        
        # OPTIMIZED: Use find_one_and_update with upsert=True.
        # This is an atomic operation that is more efficient than a separate find and insert.
        user_data = await db["users"].find_one_and_update(
            {"firebase_uid": uid},
            {
                "$setOnInsert": {
                    "email": email,
                    "name": name,
                    "role": "customer",
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True,
            return_document=True
        )
        print(f"--- User {email} synced successfully ---")
        return User(**user_data).model_dump()
        
    except Exception as e:
        print(f"--- ERROR in /sync-user: {e} ---")
        raise HTTPException(status_code=400, detail=f"User sync failed: {e}")

@router.get("/users", response_model=List[User], tags=["Owner Actions"])
async def get_all_users(
    db: AsyncIOMotorClient = Depends(get_database),
    current_owner: dict = Depends(get_current_user) # Secure endpoint
):
    """ Get all users (admin/owner only). """
    if current_owner.get("role") not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    users_cursor = db["users"].find({})
    users = await users_cursor.to_list(length=None)
    return [User(**user).model_dump() for user in users]

@router.get("/user/{user_id}", response_model=User, tags=["Owner Actions"])
async def get_user_by_id(
    user_id: str,
    db: AsyncIOMotorClient = Depends(get_database),
    current_user: dict = Depends(get_current_user) # CORRECTED: Use the standard security dependency
):
    """ Get a specific user by their MongoDB ID. """
    # Permission check: an owner/admin can see anyone, but a regular user can only see themselves.
    if (current_user.get("role") not in ["admin", "owner"] and 
        str(current_user["_id"]) != user_id):
        raise HTTPException(status_code=403, detail="Access denied.")
        
    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    user = await db["users"].find_one({"_id": object_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return User(**user).model_dump()

@router.put("/user/{user_id}/role", response_model=User, tags=["Owner Actions"])
async def update_user_role(
    user_id: str,
    role: str = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    current_user: dict = Depends(get_current_user) # Secure endpoint
):
    """ Update a user's role (owner/admin only). """
    if current_user.get("role") not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    valid_roles = ["customer", "admin", "owner"]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
        
    updated_user = await db["users"].find_one_and_update(
        {"_id": object_id},
        {"$set": {"role": role, "updated_at": datetime.utcnow()}},
        return_document=True
    )
    
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return User(**updated_user).model_dump()

