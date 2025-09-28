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
    PHONEPE_PROD_MERCHANT_ID: str
    PHONEPE_PROD_SALT_KEY: str
    PHONEPE_PROD_SALT_INDEX: int
    PHONEPE_UAT_MERCHANT_ID: str
    PHONEPE_UAT_SALT_KEY: str
    PHONEPE_UAT_SALT_INDEX: int
    FRONTEND_URLS:str
    ENVIRONMENT: str = "DEV"
    
settings = Settings()