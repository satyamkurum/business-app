from fastapi import APIRouter, Body, Depends, HTTPException, status, Response
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.chat_agent_service import get_ai_response
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.db.mongodb import get_database
from app.core.security import get_api_key, get_current_user
from uuid import uuid4

# --- Helper Function for Clean Data Formatting ---
def format_chat_for_frontend(chat: dict) -> dict:
    """
    Converts MongoDB's complex data types (ObjectId, datetime) into simple,
    JSON-friendly strings that the React frontend can easily understand.
    This function is the key to creating a reliable data contract.
    """
    if "_id" in chat:
        chat["_id"] = str(chat["_id"])
    
    if "created_at" in chat and isinstance(chat["created_at"], datetime):
        chat["created_at"] = chat["created_at"].isoformat()
    
    for message in chat.get("messages", []):
        if "timestamp" in message and isinstance(message["timestamp"], datetime):
            message["timestamp"] = message["timestamp"].isoformat()
            
    return chat

# --- Pydantic Models for clarity ---
class ChatRequest(BaseModel):
    session_id: str
    question: str
    chat_history: List[Dict[str, Any]]

router = APIRouter()

# --- Public Endpoint for Customer Chatbot ---
@router.post("/", tags=["Chatbot"])
async def handle_chat(request: ChatRequest):
    """Receives a question from any user and returns the AI's response."""
    response = await get_ai_response(
        request.session_id, request.question, request.chat_history
    )
    return {"answer": response}

# --- Secure Endpoints for Logged-in Customers ---
@router.post("/contact-owner", status_code=status.HTTP_201_CREATED, tags=["Customer Actions"])
async def send_message_to_owner(
    message: str = Body(..., embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Allows a logged-in customer to send a direct message to the owner."""
    user_name = current_user.get('name', 'a logged-in user')
    new_chat = {
        "session_id": str(uuid4()),
        "user_id": current_user.get("firebase_uid"),
        "messages": [{
            "sender": "user",
            "text": f"Direct message from {user_name}: {message}",
            "timestamp": datetime.utcnow()
        }],
        "status": "escalated",
        "created_at": datetime.utcnow()
    }
    await db["chats"].insert_one(new_chat)
    return {"status": "success", "message": "Your message has been sent."}

@router.get("/my-messages", response_model=List[Dict], tags=["Customer Actions"])
async def get_my_messages(
    db: AsyncIOMotorClient = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Fetches all chats for the currently logged-in user."""
    user_firebase_uid = current_user.get("firebase_uid")
    chats_cursor = db["chats"].find({"user_id": user_firebase_uid}).sort("created_at", -1)
    chats_list = await chats_cursor.to_list(length=100)
    return [format_chat_for_frontend(chat) for chat in chats_list]

# --- Secure Endpoints for Owner Dashboard ---
@router.get("/escalated", response_model=List[Dict], tags=["Owner Actions"])
async def list_escalated_chats(
    db: AsyncIOMotorClient = Depends(get_database),
    api_key: str = Depends(get_api_key)
):
    """Retrieve all chats with 'escalated' status. Requires admin API key."""
    chats_cursor = db["chats"].find({"status": "escalated"}).sort("created_at", -1)
    chats_list = await chats_cursor.to_list(length=100)
    return [format_chat_for_frontend(chat) for chat in chats_list]

@router.post("/escalated/reply", tags=["Owner Actions"])
async def reply_to_chat(
    chat_id: str = Body(...),
    reply_text: str = Body(...),
    db: AsyncIOMotorClient = Depends(get_database),
    api_key: str = Depends(get_api_key)
):
    """Allows an owner to reply to an escalated chat. Requires admin API key."""
    try:
        chat_oid = ObjectId(chat_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid chat_id format")

    new_message = {"sender": "human", "text": reply_text, "timestamp": datetime.utcnow()}
    
    result = await db["chats"].update_one(
        {"_id": chat_oid},
        {"$push": {"messages": new_message}, "$set": {"status": "closed"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    return {"status": "success", "message": "Reply sent and chat closed."}

