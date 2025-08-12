import os
import logging
import pytz

from .config import MongodbClient

logger = logging.getLogger(__name__)

# Database and collection names
DB_NAME = "livekit_calling_system"
USERS_COL = "users"
WORKFLOWS_COL = "workflows"
CALLS_COL = "calls"
IST = pytz.timezone("Asia/Kolkata")

_client = MongodbClient().client


def users():
    return _client[DB_NAME][USERS_COL]


def workflows():
    return _client[DB_NAME][WORKFLOWS_COL]


def calls():
    return _client[DB_NAME][CALLS_COL]


# Ensure indexes on import
try:
    users().create_index("user_id", unique=True)
    workflows().create_index([("user_id", 1), ("workflow_id", 1)], unique=True)
    calls().create_index([("user_id", 1), ("workflow_id", 1), ("call_id", 1)], unique=True)
    logger.info("MongoDB indexes ensured for users/workflows/calls")
except Exception as e:
    logger.error(f"Failed to ensure indexes: {e}")
