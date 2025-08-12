from pymongo import MongoClient
from dotenv import load_dotenv
import os,logging,asyncio
from typing import Dict, Any, Optional, List

load_dotenv()

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
LOGGER = logging.getLogger("Get Data from MongoDB")


def _sync_get_extracted_data(
    workflow_id: str,
    collection_name: str
) -> Optional[Dict[str, Any]]:
    """
    Synchronous MongoDB operation to be run in thread pool.
    """
    try:
        LOGGER.info("Searching for extracted data with workflow id: %s", workflow_id)
        
        # Connect to MongoDB
        client = MongoClient(config.mongodb_uri)
        db = client[config.mongodb_database]
        collection = db[collection_name]
        
        # Query for documents with matching workflow id
        query = {"workflow_id": workflow_id}
        
        
        # Retrieve all extractions for this workflow_id 
        documents = list(collection.find(query).sort("extraction_timestamp"))
        
        if not documents:
            LOGGER.warning("No extracted data found for workflow id: %s", workflow_id)
            return None
        
        
        LOGGER.info("Found %d extractions for workflow_id %s", len(documents), workflow_id)

        # Transform each Mongo document into a cleaner payload
        extractions: List[Dict[str, Any]] = []
        for doc in documents:
            extractions.append({
                "record_id": doc.get("record_id"),
                "extraction_timestamp": doc.get("extraction_timestamp"),
                "processing_time": doc.get("processing_time", 0),
                "elements_count": doc.get("elements_count", 0),
                "elements": doc.get("elements", []),
            })

        return {
            "workflow_id": workflow_id,
            "total_extractions": len(extractions),
            "extractions": extractions
        }
        
    except Exception as e:
        LOGGER.error("Failed to retrieve data from MongoDB: %s", str(e))
        return None
    finally:
        try:
            client.close()
        except:
            pass


async def get_extracted_data(
    workflow_id: str,
    collection_name: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve extracted data from MongoDB using workflow id.
    
    Args:
        workflow_id: The workflow id to search for
        return_latest: If True, returns the most recent extraction for the file
        include_metadata: If True, includes processing metadata in the result
    
    Returns:
        Dictionary containing the extracted data, or None if not found
    """
    # Run the synchronous MongoDB operation in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_get_extracted_data, workflow_id, collection_name)


            