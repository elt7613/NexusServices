import os, json, logging, asyncio, pathlib, time
from typing import Union, Dict, Any, Optional, List
import unstructured_client
from unstructured_client.models import operations, shared
from unstructured.staging.base import elements_from_dicts
from dotenv import load_dotenv  

from .utils.save_to_mongodb import save_to_mongodb

load_dotenv()

class Config:
    def __init__(self):
        self.unstructured_api_url = os.environ.get("UNSTRUCTURED_API_URL")
        self.unstructured_api_key = os.environ.get("UNSTRUCTURED_API_KEY")
        self.timeout = int(os.environ.get("UNSTRUCTURED_TIMEOUT_SEC", "90"))
        self.max_retries = int(os.environ.get("MAX_RETRIES", "3"))

        self.validate()
    
    def validate(self):
        """Validate required environment variables"""
        missing_vars = []
        if not self.unstructured_api_url:
            missing_vars.append("UNSTRUCTURED_API_URL")
        if not self.unstructured_api_key:
            missing_vars.append("UNSTRUCTURED_API_KEY")
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate URLs
        if not self.unstructured_api_url.startswith(('http://', 'https://')):
            raise ValueError("UNSTRUCTURED_API_URL must be a valid URL")

# Initialize configuration
config = Config()

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger("unstructured_extractor")

# Initialize client 
CLIENT = unstructured_client.UnstructuredClient(
    api_key_auth=config.unstructured_api_key,
    server_url=config.unstructured_api_url
)

async def extract_file(
    path: Union[str, pathlib.Path],
    *,
    strategy: shared.Strategy = shared.Strategy.HI_RES,
    unique_ids: bool = True,
    return_elements: bool = False,
    custom_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Partition any supported document and return JSON. 
    Uses Gemini via OpenRouter only when VLM strategy is specified and supported.
    
    Args:
        path: Path to the document file
        strategy: Processing strategy (HI_RES default, VLM for multimodal if supported)
        unique_ids: Whether to generate unique element IDs
        return_elements: Whether to return parsed elements along with JSON
        custom_params: Additional partition parameters
    
    Returns:
        Dictionary containing processed document data
    """
    filename = pathlib.Path(path).expanduser().resolve()
    
    if not filename.exists():
        raise FileNotFoundError(f"File not found: {filename}")
    
    LOGGER.info("Processing document: %s (%.2f MB)", 
                filename.name, filename.stat().st_size / (1024 * 1024))
    
    start_time = time.time()
    
    try:
        with filename.open("rb") as f:
            files = shared.Files(content=f.read(), file_name=filename.name)
    
        # Base partition parameters
        partition_params = {
            'files': files,
            'strategy': strategy,
            'split_pdf_page': True,
            'split_pdf_concurrency_level': 15,
            'split_pdf_allow_failed': True,
            'unique_element_ids': unique_ids,
            'languages': ["auto"]
        }
        
        # Add VLM parameters only if VLM strategy is being used
        if strategy == shared.Strategy.VLM:
            partition_params.update({
                'vlm_model_provider': shared.VLMModelProvider.OPENAI,  # gateway trick
                'vlm_model': config.model_id,
            })
            LOGGER.info("Using VLM strategy with Gemini model: %s", config.model_id)
        else:
            LOGGER.info("Using %s strategy (VLM not available on this API)", strategy.value if hasattr(strategy, 'value') else str(strategy))
        
        # Merge custom parameters if provided
        if custom_params:
            partition_params.update(custom_params)
            LOGGER.info("Applied custom parameters: %s", list(custom_params.keys()))

        params = shared.PartitionParameters(**partition_params)
        req = operations.PartitionRequest(partition_parameters=params)
        
        LOGGER.info("Sending request to Unstructured API...")
        # Make the blocking call non-blocking by running it in a thread pool executor
        # This is more compatible with uvloop than asyncio.to_thread()
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, lambda: CLIENT.general.partition(request=req))

        if res.status_code != 200:
            error_msg = f"Partition failed: {res.status_code}"
            if hasattr(res, 'message') and res.message:
                error_msg += f" - {res.message}"
            if hasattr(res, 'raw_response'):
                try:
                    error_details = res.raw_response.text
                    error_msg += f" - Details: {error_details}"
                except:
                    pass
            raise RuntimeError(error_msg)

        processing_time = time.time() - start_time
        json_out = [e for e in res.elements] if res.elements else []
        
        LOGGER.info("Successfully processed %s: %d elements extracted in %.2f seconds", 
                   filename.name, len(json_out), processing_time)
        
        result = {"json": json_out, "processing_time": processing_time}
        
        if return_elements:
            result["elements"] = elements_from_dicts(json_out)
        
        return result

    except Exception as e:
        LOGGER.error("Failed to process %s: %s", workflow_id, str(e))
        raise

async def process_document_extraction(
    path: Union[str, pathlib.Path],
    *,
    workflow_id: str,
    collection_name: str,
) -> Dict[str, Any]:
    """
    Extract document data and save to both MongoDB and optionally JSON file.
    
    Args:
        path: Path to the document file
        strategy: Processing strategy
        collection_name: Name of the collection to save the data to
    
    Returns:
        Dictionary containing extraction results and save status
    """
    strategy = shared.Strategy.HI_RES

    try:
        # Extract document data
        LOGGER.info("Starting extraction and MongoDB save for: %s", workflow_id)
        result = await extract_file(
            path=path,
            strategy=strategy,
            unique_ids=True
        )
        
        # Save to MongoDB
        mongodb_success = await save_to_mongodb(
            workflow_id=workflow_id,
            collection_name=collection_name,
            data=result
        )

        return {
            "extraction_result": result,
            "mongodb_saved": mongodb_success
        }
        
    except Exception as e:
        LOGGER.error("Failed to extract and save %s: %s", workflow_id, str(e))
        raise
