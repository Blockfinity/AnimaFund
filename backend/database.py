"""
PLATFORM: Shared database module — provides MongoDB access to all routers.
"""
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

_client = None
_db = None


def init_db():
    global _client, _db
    if not MONGO_URL or not DB_NAME:
        logging.error(f"MONGO_URL or DB_NAME not set. MONGO_URL={'set' if MONGO_URL else 'MISSING'}, DB_NAME={'set' if DB_NAME else 'MISSING'}")
        return
    _client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    _db = _client[DB_NAME]
    logging.info(f"MongoDB initialized: {DB_NAME}")


def close_db():
    global _client
    if _client:
        _client.close()


def get_db():
    return _db
