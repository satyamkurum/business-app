import base64
import hashlib
import json
import uuid
import requests
from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict
from datetime import datetime, timezone

from app.core.config import settings
from app.core.security import get_current_user, get_api_key
from app.db.mongodb import get_database

router = APIRouter()

# --- Environment-Specific Configuration ---
if settings.ENVIRONMENT == "PROD":
    MERCHANT_ID = settings.PHONEPE_PROD_MERCHANT_ID
    SALT_KEY = settings.PHONEPE_PROD_SALT_KEY
    SALT_INDEX = settings.PHONEPE_PROD_SALT_INDEX
    PHONEPE_HOST_URL = "https://api.phonepe.com/apis/hermes"
else:
    MERCHANT_ID = settings.PHONEPE_UAT_MERCHANT_ID
    SALT_KEY = settings.PHONEPE_UAT_SALT_KEY
    SALT_INDEX = settings.PHONEPE_UAT_SALT_INDEX
    PHONEPE_HOST_URL = "https://api-preprod.phonepe.com/apis/pg-sandbox"

PAY_API_URL = f"{PHONEPE_HOST_URL}/pg/v1/pay"
STATUS_API_URL = f"{PHONEPE_HOST_URL}/pg/v1/status/{MERCHANT_ID}"

# --- Helper Function ---
def format_order_for_frontend(order: dict) -> dict:
    if "_id" in order: order["_id"] = str(order["_id"])
    if "created_at" in order and hasattr(order["created_at"], 'isoformat'):
        order["created_at"] = order["created_at"].isoformat()
    return order

# --- Customer Payment Endpoint ---
@router.post("/initiate-payment", tags=["Payments"])
async def initiate_payment(
    items: List[Dict] = Body(...),
    db: AsyncIOMotorClient = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    try:
        merchant_transaction_id = str(uuid.uuid4())
        user_id = current_user.get("firebase_uid")
        amount_in_paisa = int(sum(item['pricing'][0]['price'] * item['quantity'] for item in items) * 100)
        
        order_items = [{"name": item['name'], "quantity": item['quantity'], "price": item['pricing'][0]['price']} for item in items]
        await db["orders"].insert_one({
            "merchant_transaction_id": merchant_transaction_id, "user_id": user_id,
            "items": order_items, "total_amount": amount_in_paisa, "status": "PENDING",
            "created_at": datetime.now(timezone.utc)
        })

        payload = {
            "merchantId": MERCHANT_ID, "merchantTransactionId": merchant_transaction_id,
            "merchantUserId": user_id, "amount": amount_in_paisa,
            "redirectUrl": "https://business-app-omega.vercel.app//payment-status",
            "redirectMode": "POST", "callbackUrl": "https://business-app-seg7.onrender.com/api/v1/payments/callback",
            "paymentInstrument": {"type": "PAY_PAGE"}
        }
        
        base64_payload = base64.b64encode(json.dumps(payload).encode()).decode()
        main_str = base64_payload + "/pg/v1/pay" + SALT_KEY
        sha256_hash = hashlib.sha256(main_str.encode()).hexdigest()
        verify_header = sha256_hash + "###" + str(SALT_INDEX)
        
        headers = {"Content-Type": "application/json", "X-VERIFY": verify_header}
        response = requests.post(PAY_API_URL, json={"request": base64_payload}, headers=headers)
        response_data = response.json()
        
        if not response_data.get('success'):
            raise HTTPException(status_code=500, detail=f"PhonePe API Error: {response_data.get('message')}")

        return {"redirectUrl": response_data['data']['instrumentResponse']['redirectInfo']['url']}
    except Exception as e:
        # This robust error handling prevents the 500 crash
        print(f"FATAL ERROR during payment initiation: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during payment initiation.")

# --- THIS IS THE NEW, MISSING ENDPOINT ---
@router.get("/my-orders", response_model=List[Dict], tags=["Customer Actions"])
async def get_my_orders(
    db: AsyncIOMotorClient = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Fetches all past and current orders for the logged-in user."""
    user_firebase_uid = current_user.get("firebase_uid")
    orders_cursor = db["orders"].find({"user_id": user_firebase_uid}).sort("created_at", -1)
    orders_list = await orders_cursor.to_list(length=100)
    return [format_order_for_frontend(order) for order in orders_list]


@router.post("/callback", include_in_schema=False, tags=["Payments"])
async def payment_callback(request: Request, db: AsyncIOMotorClient = Depends(get_database)):
    """Secure webhook endpoint for PhonePe to send server-to-server payment status updates."""
    # ... (This function's logic remains the same)
    try:
        encoded_response = (await request.body()).decode()
        x_verify_header = request.headers.get("X-VERIFY")
        expected_signature = hashlib.sha256((encoded_response + SALT_KEY).encode()).hexdigest() + f"###{SALT_INDEX}"
        if x_verify_header != expected_signature:
            raise HTTPException(status_code=400, detail="Webhook signature mismatch.")
        decoded_response = json.loads(base64.b64decode(encoded_response).decode())
        merchant_transaction_id = decoded_response['data']['merchantTransactionId']
        payment_status = decoded_response['code']
        new_status = "SUCCESS" if payment_status == 'PAYMENT_SUCCESS' else "FAILED"
        await db["orders"].update_one(
            {"merchant_transaction_id": merchant_transaction_id},
            {"$set": {"status": new_status, "phonepe_response": decoded_response}}
        )
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 4. Secure Endpoints for the Owner's Dashboard ---

@router.get("/orders", response_model=List[Dict], tags=["Owner Actions"])
async def get_all_orders(
    db: AsyncIOMotorClient = Depends(get_database),
    api_key: str = Depends(get_api_key) # Secured with Admin API Key
):
    """Fetches all orders from the database for the owner's dashboard."""
    orders_cursor = db["orders"].find({}).sort("created_at", -1)
    orders_list = await orders_cursor.to_list(length=200)
    return [format_order_for_frontend(order) for order in orders_list]

# --- THIS IS THE NEW, CRITICAL ENDPOINT ---
@router.put("/orders/{order_id}/status", tags=["Owner Actions"])
async def update_order_status(
    order_id: str,
    status: str = Body(..., embed=True, description="The new status for the order."),
    delivery_info: Dict = Body(None, embed=True, description="Optional delivery partner details."),
    db: AsyncIOMotorClient = Depends(get_database),
    api_key: str = Depends(get_api_key) # Secured with Admin API Key
):
    """
    Allows the owner to update the status of an order (e.g., CONFIRMED, PREPARING, SHIPPED).
    """
    valid_statuses = ["CONFIRMED", "PREPARING", "SHIPPED"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
    try:
        order_oid = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order_id format.")

    # Prepare the update document for MongoDB
    update_doc = {"$set": {"status": status}}
    if status == "SHIPPED" and delivery_info:
        # Only add delivery info if the order is being shipped
        update_doc["$set"]["delivery_info"] = delivery_info

    result = await db["orders"].update_one({"_id": order_oid}, update_doc)
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found.")
        
    return {"status": "success", "message": f"Order status successfully updated to {status}."}

