import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MongodbClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongodbClient, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance

    def _initialize_client(self):
        self.mongo_uri = os.getenv("MONGODB_URI")
        if not self.mongo_uri:
            raise ValueError("Missing MONGODB_URI in environment variables.")

        self.client = MongoClient(
            self.mongo_uri, 
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000
        )
        
        # Retry logic for connection
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.client.admin.command('ping')
                print("MongoDB client initialized successfully")
                break
            except ConnectionFailure as e:
                if attempt == max_retries - 1:
                    logger.error(f"Could not connect after {max_retries} attempts: {e}")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    async def get_collection(self, db_name: str, collection_name: str):
        return self.client[db_name][collection_name]
