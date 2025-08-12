import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import os,logging,time,asyncio,uuid
from typing import Dict, Any

load_dotenv()

PYMONGO_AVAILABLE = True


class Config:
    def __init__(self):
        # MongoDB configuration
        self.mongodb_uri = os.environ.get("MONGODB_URI")
        self.mongodb_database = os.environ.get("MONGODB_DATABASE", "document_processing")
        
        
# Initialize configuration
config = Config()

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger("Save to MongoDB")


def _sync_save_to_mongodb(
    workflow_id: str,
    collection_name: str,
    data: Dict[str, Any], 
) -> bool:
    """
    Synchronous MongoDB operation to be run in thread pool.
    """
    try:
        LOGGER.info("Connecting directly to MongoDB...")
        
        # Connect to MongoDB
        client = MongoClient(config.mongodb_uri)
        db = client[config.mongodb_database]
        collection = db[collection_name]
        
        # Prepare document data for MongoDB
        document_data = {
            "workflow_id": workflow_id,
            "extraction_timestamp": time.time(),
            "processing_time": data.get("processing_time", 0),
            "elements_count": len(data.get("json", [])),
            "elements": data.get("json", []),
            "record_id": f"{workflow_id}_{uuid.uuid4()}"  # Globally unique identifier
        }
        
        LOGGER.info("Saving %d elements to MongoDB collection: %s", 
                   len(document_data["elements"]), collection_name)
        
        # Insert new document – do not overwrite existing ones
        result = collection.insert_one(document_data)
        
        if result.inserted_id:
            LOGGER.info("Document inserted successfully to MongoDB:")
            LOGGER.info("  - Database: %s", config.mongodb_database)
            LOGGER.info("  - Collection: %s", collection_name)
            LOGGER.info("  - Record ID: %s", document_data["record_id"])
            LOGGER.info("  - Elements count: %d", document_data["elements_count"])
            return True
        else:
            LOGGER.warning("Failed to insert document to MongoDB")
            return False
        
    except Exception as e:
        LOGGER.error("Failed to save to MongoDB directly: %s", str(e))
        return False
    finally:
        try:
            client.close()
        except:
            pass


async def save_to_mongodb(
    workflow_id: str,
    collection_name: str,
    data: Dict[str, Any], 
) -> bool:
    """
    Save extraction result directly to MongoDB using pymongo.
    This is a fallback method when the Unstructured workflow API is not available.
    
    Args:
        workflow_id: The workflow id of the extraction
        collection_name: Name of the collection to save the data to
        data: The extraction result from extract_file
    
    Returns:
        True if successful, False otherwise
    """
    if not PYMONGO_AVAILABLE:
        LOGGER.error("pymongo is not installed. Install it with: pip install pymongo")
        return False
    
    # Run the synchronous MongoDB operation in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_save_to_mongodb, workflow_id, collection_name, data)