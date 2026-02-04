import os
from dotenv import load_dotenv

load_dotenv()

HDFC_BASE_URL = os.getenv("HDFC_BASE_URL")
MERCHANT_ID = os.getenv("HDFC_MERCHANT_ID")
API_KEY = os.getenv("HDFC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
RETURN_URL = os.getenv("RETURN_URL")
