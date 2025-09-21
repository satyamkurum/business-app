# frontend_owner/firebase_config.py

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load the .env file
load_dotenv()

class FirebaseSettings(BaseSettings):
    """Loads Firebase configuration from environment variables."""
    FIREBASE_API_KEY: str
    FIREBASE_AUTH_DOMAIN: str
    FIREBASE_PROJECT_ID: str
    FIREBASE_STORAGE_BUCKET: str
    FIREBASE_MESSAGING_SENDER_ID: str
    FIREBASE_APP_ID: str

# Create an instance of the settings
settings = FirebaseSettings()

# Structure the config into the dictionary format the library expects
firebase_config = {
    "apiKey": settings.FIREBASE_API_KEY,
    "authDomain": settings.FIREBASE_AUTH_DOMAIN,
    "projectId": settings.FIREBASE_PROJECT_ID,
    "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
    "messagingSenderId": settings.FIREBASE_MESSAGING_SENDER_ID,
    "appId": settings.FIREBASE_APP_ID,
    "databaseURL": ""
}