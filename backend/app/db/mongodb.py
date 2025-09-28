from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataBase:
    client: AsyncIOMotorClient = None

db = DataBase()

async def get_database() -> AsyncIOMotorClient:
    """Provides the database instance. Raises an error if the client is not connected."""
    if db.client is None:
        # This is a safeguard in case the app starts in a broken state.
        raise RuntimeError("Database client is not initialized. The application failed to connect to MongoDB on startup.")
    return db.client.get_database("restaurentDB")

async def connect_to_mongo():
    """
    Establishes a connection to the MongoDB database.
    If the connection fails, it will terminate the application process.
    """
    logger.info("Attempting to connect to MongoDB...")
    try:
        db.client = AsyncIOMotorClient(settings.MONGO_URI)
        # The 'ping' command is a lightweight way to verify a live connection.
        await db.client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB!")
    except Exception as e:
        # --- THIS IS THE CRITICAL FIX ---
        # If the connection fails, log a fatal error and exit the application.
        # This prevents the server from running in a broken, unusable state.
        logger.error(f"❌ FATAL: Could not connect to MongoDB. The application will not start.")
        logger.error(f"   Error details: {e}")
        sys.exit(1) # Exit the process with a non-zero status code to indicate failure.

async def close_mongo_connection():
    if db.client:
        logger.info("Closing MongoDB connection...")
        db.client.close()
        logger.info("MongoDB connection closed.")

