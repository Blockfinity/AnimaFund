"""
Shared database module — provides MongoDB access to all routers.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

_client = None
_db = None


def init_db():
    global _client, _db
    _client = AsyncIOMotorClient(MONGO_URL)
    _db = _client[DB_NAME]


def close_db():
    global _client
    if _client:
        _client.close()


def get_db():
    return _db
