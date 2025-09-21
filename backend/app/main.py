import firebase_admin
from firebase_admin import credentials
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.api.v1.api import api_router
from app.core.config import settings

# --- 1. IMPORT THE MIDDLEWARE ---
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await connect_to_mongo()
    # Ensure Firebase is initialized only once
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

# --- 2. DEFINE ALLOWED ORIGINS ---
# This MUST match the address of your React development server
origins = [
    "http://localhost:3000",
]

# --- 3. ADD THE MIDDLEWARE TO YOUR APP ---
# This MUST be added before you include your routers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# --- 4. INCLUDE YOUR ROUTERS ---
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome!"}
