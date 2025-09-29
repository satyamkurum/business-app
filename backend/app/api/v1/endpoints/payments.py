import base64
import hashlib
import json
import uuid
import requests
from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict
from datetime import datetime, timezone
from bson import ObjectId

from app.core.config import settings
from app.core.security import get_current_user, get_api_key
from app.db.mongodb import get_database

router = APIRouter()

# --- 1. Environment-Specific Configuration ---
# This block intelligently selects the right keys and URL based on your .env file.
# To go live, you only need to change ENVIRONMENT="PROD" in your Render environment variables.
if settings.ENVIRONMENT == "PROD":
    MERCHANT_ID = settings.PHONEPE_PROD_MERCHANT_ID
    SALT_KEY = settings.PHONEPE_PROD_SALT_KEY
    SALT_INDEX = settings.PHONEPE_PROD_SALT_INDEX
    PHONEPE_HOST_URL = "https://api.phonepe.com/apis/hermes"
else: # SANDBOX / UAT
    MERCHANT_ID = settings.PHONEPE_UAT_MERCHANT_ID
    SALT_KEY = settings.PHONEPE_UAT_SALT_KEY
    SALT_INDEX = settings.PHONEPE_UAT_SALT_INDEX
    PHONEPE_HOST_URL = "https://api-preprod.phonepe.com/apis/pgsandbox"

PAY_API_ENDPOINT = "/pg/v1/pay"
STATUS_API_ENDPOINT = f"/pg/v1/status/{MERCHANT_ID}"

# --- 2. Helper Function for Data Formatting ---
def format_order_for_frontend(order: dict) -> dict:
    """Converts MongoDB data types into clean, JSON-friendly strings for the frontend."""
    if "_id" in order: order["_id"] = str(order["_id"])
    if "created_at" in order and hasattr(order["created_at"], 'isoformat'):
        order["created_at"] = order["created_at"].isoformat()
    return order

# --- 3. Core Payment Endpoints (Manual Implementation) ---

@router.post("/initiate-payment", tags=["Payments"])
async def initiate_payment(
    items: List[Dict] = Body(...),
    db: AsyncIOMotorClient = Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """
    Initiates a payment using the secure X-VERIFY signature method for both Sandbox and Production.
    """
    merchant_transaction_id = str(uuid.uuid4())
    user_id = current_user.get("firebase_uid")
    amount_in_paisa = int(sum(item['pricing'][0]['price'] * item['quantity'] for item in items) * 100)

    await db["orders"].insert_one({
        "merchant_transaction_id": merchant_transaction_id, "user_id": user_id,
        "items": [{"name": item['name'], "quantity": item['quantity'], "price": item['pricing'][0]['price']} for item in items],
        "total_amount": amount_in_paisa, "status": "PENDING", "created_at": datetime.now(timezone.utc)
    })

    redirect_url_base = settings.FRONTEND_URLS.split(",")[0]
    
    payload = {
        "merchantId": MERCHANT_ID,
        "merchantTransactionId": merchant_transaction_id,
        "merchantUserId": user_id,
        "amount": amount_in_paisa,
        "redirectUrl": f"{redirect_url_base}/payment-status",
        "redirectMode": "POST",
        "callbackUrl": f"{settings.BACKEND_URL}/api/v1/payments/callback",
        "paymentInstrument": {"type": "PAY_PAGE"}
    }
    
    # Create the secure X-VERIFY signature
    base64_payload = base64.b64encode(json.dumps(payload).encode()).decode()
    main_str = base64_payload + PAY_API_ENDPOINT + SALT_KEY
    sha256_hash = hashlib.sha256(main_str.encode()).hexdigest()
    verify_header = sha256_hash + "###" + str(SALT_INDEX)
    
    headers = {"Content-Type": "application/json", "X-VERIFY": verify_header, "accept": "application/json"}
    
    try:
        response = requests.post(f"{PHONEPE_HOST_URL}{PAY_API_ENDPOINT}", json={"request": base64_payload}, headers=headers)
        response_data = response.json()
    
        if not response_data.get('success'):
            raise HTTPException(status_code=500, detail=f"PhonePe API Error: {response_data.get('message')}")

        return {"redirectUrl": response_data['data']['instrumentResponse']['redirectInfo']['url']}
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"An unexpected error occurred during payment initiation: {e}")


@router.post("/callback", include_in_schema=False, tags=["Payments"])
async def payment_callback(request: Request, db: AsyncIOMotorClient = Depends(get_database)):
    """Secure webhook endpoint for PhonePe, with mandatory signature validation."""
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

@router.get("/status/{merchant_transaction_id}", tags=["Payments"])
async def check_payment_status(merchant_transaction_id: str, db: AsyncIOMotorClient = Depends(get_database)):
    """Checks the status of a transaction, as required by the checklist."""
    api_path_part = f"{STATUS_API_ENDPOINT}/{merchant_transaction_id}"
    main_str = api_path_part + SALT_KEY
    sha256_hash = hashlib.sha256(main_str.encode()).hexdigest()
    verify_header = sha256_hash + "###" + str(SALT_INDEX)
    
    headers = {"Content-Type": "application/json", "X-VERIFY": verify_header, "X-MERCHANT-ID": MERCHANT_ID}
    
    response = requests.get(f"{PHONEPE_HOST_URL}{api_path_part}", headers=headers)
    response_data = response.json()
    
    if response_data.get("success"):
        payment_status = response_data.get('code')
        new_status = "SUCCESS" if payment_status == 'PAYMENT_SUCCESS' else "FAILED" if payment_status in ['PAYMENT_ERROR', 'TRANSACTION_NOT_FOUND'] else "PENDING"
        await db["orders"].update_one(
            {"merchant_transaction_id": merchant_transaction_id},
            {"$set": {"status": new_status}}
        )
    return response_data

# --- 4. Secure Endpoints for Owner & Customer ---
@router.get("/orders", response_model=List[Dict], tags=["Owner Actions"])
async def get_all_orders(db: AsyncIOMotorClient = Depends(get_database), api_key: str = Depends(get_api_key)):
    orders_cursor = db["orders"].find({}).sort("created_at", -1)
    orders_list = await orders_cursor.to_list(length=200)
    return [format_order_for_frontend(order) for order in orders_list]

@router.get("/my-orders", response_model=List[Dict], tags=["Customer Actions"])
async def get_my_orders(db: AsyncIOMotorClient = Depends(get_database), current_user: dict = Depends(get_current_user)):
    orders_cursor = db["orders"].find({"user_id": current_user.get("firebase_uid")}).sort("created_at", -1)
    orders_list = await orders_cursor.to_list(length=100)
    return [format_order_for_frontend(order) for order in orders_list]

@router.put("/orders/{order_id}/status", tags=["Owner Actions"])
async def update_order_status(
    order_id: str,
    status: str = Body(..., embed=True),
    delivery_info: Dict = Body(None, embed=True),
    db: AsyncIOMotorClient = Depends(get_database),
    api_key: str = Depends(get_api_key)
):
    valid_statuses = ["CONFIRMED", "PREPARING", "SHIPPED"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status.")
    
    order_oid = ObjectId(order_id)
    update_doc = {"$set": {"status": status}}
    if status == "SHIPPED" and delivery_info:
        update_doc["$set"]["delivery_info"] = delivery_info

    result = await db["orders"].update_one({"_id": order_oid}, update_doc)
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found.")
        
    return {"status": "success", "message": f"Order status updated to {status}."}

