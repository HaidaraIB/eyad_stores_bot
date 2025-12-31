import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OWNER_ID = int(os.getenv("OWNER_ID"))
    ERRORS_CHANNEL = int(os.getenv("ERRORS_CHANNEL"))
    API_PURCHASES_ARCHIVE_CHANNEL = int(os.getenv("API_PURCHASES_ARCHIVE_CHANNEL"))
    CHARGING_BALANCE_ORDERS_ARCHIVE_CHANNEL = int(os.getenv("CHARGING_BALANCE_ORDERS_ARCHIVE_CHANNEL"))
    MANUAL_PURCHASES_ARCHIVE_CHANNEL = int(os.getenv("MANUAL_PURCHASES_ARCHIVE_CHANNEL"))

    G2BULK_API_KEY = os.getenv("G2BULK_API_KEY")

    DB_PATH = os.getenv("DB_PATH")
    DB_POOL_SIZE = 20
    DB_MAX_OVERFLOW = 10
