import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "my_secure_verify_token")
    WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/outputs")

    @staticmethod
    def ensure_dirs():
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
