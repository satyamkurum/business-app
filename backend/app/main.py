import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api.v1.api import api_router
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    # Startup logic
    await connect_to_mongo()
    # Ensure Firebase is initialized only once to prevent errors
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {e}")
    yield
    # Shutdown logic
    await close_mongo_connection()

app = FastAPI(
    title="Restaurant AI Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

# --- THIS IS THE DEFINITIVE FIX FOR DEPLOYMENT ---
# Instead of a hardcoded list, we read the allowed frontend URLs
# from your environment variables. This makes the application portable.
# On Render, you will set this to your Vercel and Streamlit URLs.
# Locally, it can be set to your localhost addresses.
origins = settings.FRONTEND_URLS.split(",") if hasattr(settings, 'FRONTEND_URLS') else []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# Include all your API endpoints from other files
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to the HFC Restaurant AI Assistant API!"}

