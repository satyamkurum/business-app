from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataBase:
    client: AsyncIOMotorClient = None

db = DataBase()

async def get_database() -> AsyncIOMotorClient:
    # This should return the database object itself, not the collection
    return db.client.get_database("restaurentDB")

async def connect_to_mongo():
    logger.info("Attempting to connect to MongoDB...")
    try:
        db.client = AsyncIOMotorClient(settings.MONGO_URI)
        
        # --- THIS IS THE FIX ---
        # The 'ping' command must be run on the client's 'admin' database,
        # not on a specific collection.
        await db.client.admin.command('ping')
        
        logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB. Error: {e}")
        db.client = None

async def close_mongo_connection():
    if db.client:
        logger.info("Closing MongoDB connection...")
        db.client.close()
        logger.info("MongoDB connection closed.")
