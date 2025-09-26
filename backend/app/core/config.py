# backend/app/core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    MONGO_URI: str
    FIREBASE_CREDENTIALS_PATH: str
    PINECONE_API_KEY: str
    GOOGLE_API_KEY: str
    ADMIN_API_KEY: str
    PHONEPE_MERCHANT_ID: str
    PHONEPE_SALT_KEY: str
    PHONEPE_SALT_INDEX: int
    PHONEPE_PAY_URL: str
    FRONTEND_URLS:str
    
settings = Settings()