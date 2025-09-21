from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from motor.motor_asyncio import AsyncIOMotorClient
from app.db.mongodb import get_database
from fastapi.security import APIKeyHeader
from app.core.config import settings

# --- System 1: API Key for Hardcoded Owner/Admin Dashboard ---
# This tells FastAPI to look for a header named 'X-API-Key'.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    """
    Checks if the API key in the request header matches our secret key.
    This is a simple and secure way to protect internal/admin endpoints.
    """
    if api_key == settings.ADMIN_API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin API Key",
        )

# This is the scheme that tells FastAPI to look for a "Bearer" token
# in the Authorization header of incoming requests.
reusable_oauth2 = HTTPBearer()

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    db: AsyncIOMotorClient = Depends(get_database)
) -> dict:
    """
    A dependency that verifies a Firebase ID token and fetches the user from MongoDB.

    This function can be added to any endpoint to make it secure and to get
    the details of the currently authenticated user.
    """
    try:
        # The actual token string is in the 'credentials' attribute
        id_token = token.credentials
        
        # 1. Verify the token with Firebase's servers
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # 2. Find the user in our own MongoDB database using the Firebase UID
        user = await db["users"].find_one({"firebase_uid": uid})
        
        if not user:
            # This case handles if a user exists in Firebase but not in our DB.
            # It's a security measure to ensure the user is properly synced.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in our database. Please sync user first."
            )
        
        return user

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials: The ID token is invalid."
        )
    except Exception as e:
        # A general catch-all for other potential errors (e.g., token expired)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}"
        )
