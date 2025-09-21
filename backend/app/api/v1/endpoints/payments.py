import base64
import hashlib
import json
import uuid
import requests
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict
from datetime import datetime, timezone

from app.core.config import settings
from app.core.security import get_current_user, get_api_key
from app.db.mongodb import get_database

router = APIRouter()

def format_order_for_frontend(order: dict) -> dict:
    """
    Converts MongoDB's complex data types (ObjectId, datetime) into simple,
    JSON-friendly strings that the frontend can easily understand.
    """
    if "_id" in order:
        order["_id"] = str(order["_id"])
    if "created_at" in order and hasattr(order["created_at"], 'isoformat'):
        order["created_at"] = order["created_at"].isoformat()
            
    return order

@router.post("/initiate-payment", tags=["Payments"])
async def initiate_payment(
    items: List[Dict] = Body(...),
    db: AsyncIOMotorClient = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Creates an 'Order' document, constructs a secure payload for PhonePe,
    and returns a redirect URL for the frontend.
    """
    print("--- 1. Initiating Payment ---")
    merchant_transaction_id = str(uuid.uuid4())
    user_id = current_user.get("firebase_uid")
    
    # ... (Order creation logic remains the same) ...
    try:
        total_amount = sum(item['pricing'][0]['price'] * item['quantity'] for item in items)
        amount_in_paisa = int(total_amount * 100)
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=400, detail="Invalid cart item data.")

    order_items = [{"name": item['name'], "quantity": item['quantity'], "price": item['pricing'][0]['price']} for item in items]
    await db["orders"].insert_one({
        "merchant_transaction_id": merchant_transaction_id, "user_id": user_id,
        "items": order_items, "total_amount": amount_in_paisa,
        "status": "PENDING", "created_at": datetime.now(timezone.utc)
    })
    print(f"--- 2. Order {merchant_transaction_id} created in DB ---")

    callback_url = "https://webhook.site/#!/a5c2229a-25f3-4d23-9363-3b1349128d5d" # Placeholder for local testing
    
    payload = {
        "merchantId": settings.PHONEPE_MERCHANT_ID,
        "merchantTransactionId": merchant_transaction_id,
        "merchantUserId": user_id,
        "amount": amount_in_paisa,
        "redirectUrl": "http://localhost:3000/payment-status",
        "redirectMode": "POST",
        "callbackUrl": callback_url,
        "paymentInstrument": {"type": "PAY_PAGE"}
    }
    
    print("--- 3. Preparing payload for PhonePe ---")
    # --- THIS IS THE FIX (PART 1) ---
    # Use separators to create a compact JSON string with no extra whitespace.
    payload_str = json.dumps(payload, separators=(',', ':'))
    base64_payload = base64.b64encode(payload_str.encode()).decode()
    
    main_str = base64_payload + "/pg/v1/pay" + settings.PHONEPE_SALT_KEY
    sha256_hash = hashlib.sha256(main_str.encode()).hexdigest()
    verify_header = sha256_hash + "###" + str(settings.PHONEPE_SALT_INDEX)
    
    headers = {"Content-Type": "application/json", "X-VERIFY": verify_header}
    
    try:
        print("--- 4. Sending request to PhonePe Sandbox ---")
        response = requests.post(settings.PHONEPE_PAY_URL, json={"request": base64_payload}, headers=headers)
        
        # --- THIS IS THE FIX (PART 2) ---
        # Instead of just raising an error, we check the status and log the response body if it's bad.
        if response.status_code != 200:
            print(f"❌ ERROR: PhonePe returned status {response.status_code}")
            print(f"❌ RESPONSE BODY: {response.text}")
            raise HTTPException(status_code=500, detail=f"PhonePe API Error: {response.text}")

        response_data = response.json()
        
        if not response_data.get('success'):
            print(f"❌ ERROR: PhonePe API returned failure: {response_data}")
            raise HTTPException(status_code=500, detail=f"PhonePe API Error: {response_data.get('message')}")

        redirect_url = response_data['data']['instrumentResponse']['redirectInfo']['url']
        print("--- 5. Successfully received redirect URL from PhonePe ---")
        return {"redirectUrl": redirect_url}
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: Could not connect to payment provider: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@router.post("/callback", include_in_schema=False, tags=["Payments"])
async def payment_callback(request: Request, db: AsyncIOMotorClient = Depends(get_database)):
    # ... (function logic remains the same)
    try:
        encoded_response = (await request.json()).get("response")
        if not encoded_response: return {"status": "error"}

        decoded_response = json.loads(base64.b64decode(encoded_response).decode())
        
        merchant_transaction_id = decoded_response['data']['merchantTransactionId']
        payment_status = decoded_response['code']
        new_status = "SUCCESS" if payment_status == 'PAYMENT_SUCCESS' else "FAILED"
        
        await db["orders"].update_one(
            {"merchant_transaction_id": merchant_transaction_id},
            {"$set": {"status": new_status, "phonepe_response": decoded_response}}
        )
        print(f"Order {merchant_transaction_id} status updated to {new_status}")
        return {"status": "success"}

    except Exception as e:
        print(f"Error in payment callback: {e}")
        return {"status": "error"}

@router.get("/orders", response_model=List[Dict], tags=["Owner Actions"])
async def get_all_orders(
    db: AsyncIOMotorClient = Depends(get_database),
    api_key: str = Depends(get_api_key)
):
    # ... (function logic remains the same)
    orders_cursor = db["orders"].find({}).sort("created_at", -1)
    orders_list = await orders_cursor.to_list(length=200)
    
    return [format_order_for_frontend(order) for order in orders_list]

