from fastapi import APIRouter, Body
from services.data_extraction.get_extracted_data import get_extracted_data
from services.data_extraction.extract_data import process_document_extraction
from typing import Union, Dict, Any, Optional, List
from fastapi import HTTPException, File, UploadFile, BackgroundTasks, Depends, Body, Query, Form
import os
import sys
import logging
import tempfile
from contextlib import asynccontextmanager

# Configure logger for this module
logger = logging.getLogger("data_extraction")

data_extraction_router = APIRouter()

# Extract data from file (synchronous)
# -------------------------------
@data_extraction_router.post("/extract-data")
async def extract_data(
    workflow_id: str = Form(...),
    collection_name: str = Form(...),
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """
    Extract document data and save to both MongoDB and optionally JSON file.
    
    Args:
        workflow_id: The workflow id of the extraction
        collection_name: Name of the collection to save the data to
        file: The file to extract data from
    
    Returns:
        Dictionary containing extraction results and save status
    """
    temp_file_path = None
    try:
        # Create a temporary file to save the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{workflow_id}") as temp_file:
            temp_file_path = temp_file.name
            
            # Read and write the uploaded file content to the temporary file
            content = await file.read()
            temp_file.write(content)
        
        # Call the extraction function with correct parameters
        result = await process_document_extraction(
            temp_file_path,
            collection_name=collection_name,
            workflow_id=workflow_id
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing document extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document extraction failed: {str(e)}")
    
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {str(e)}")

# Async background extraction endpoint
# -------------------------------
@data_extraction_router.post("/extract-data-async", status_code=202)
async def extract_data_async(
    background_tasks: BackgroundTasks,
    workflow_id: str = Form(...),
    collection_name: str = Form(...),
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """
    Trigger document extraction in the background and return immediately.

    This endpoint is suitable when you want the extraction to happen
    asynchronously so the request doesn\'t block the client. Each call
    creates an isolated background task, ensuring multiple concurrent
    requests are processed independently.
    """
    temp_file_path: Optional[str] = None
    try:
        # Persist the uploaded file to a temporary location so the background
        # task can access it after the response is sent.
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{workflow_id}") as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)

        # Schedule the extraction task.
        background_tasks.add_task(_run_extraction_background, temp_file_path, workflow_id, collection_name)

        # Respond immediately. Client can later poll `/get-extracted-data` to
        # retrieve results from MongoDB.
        return {
            "status": "accepted",
            "workflow_id": workflow_id,
            "collection_name": collection_name,
            "message": "Extraction has started and is running in the background."
        }
    except Exception as exc:
        logger.error("Failed to schedule background extraction for %s: %s", workflow_id, str(exc))
        raise HTTPException(status_code=500, detail=f"Failed to schedule extraction: {str(exc)}")
    # NOTE: Do NOT delete the temp file here; it is cleaned up in the background task.


async def _run_extraction_background(temp_file_path: str, workflow_id: str, collection_name: str):
    """Wrapper that performs extraction and cleans up resources."""
    try:
        await process_document_extraction(
            temp_file_path,
            collection_name=collection_name,
            workflow_id=workflow_id,
        )
    except Exception as exc:
        logger.error("Background extraction failed for %s: %s", workflow_id, str(exc))
    finally:
        # Ensure temporary file is removed regardless of outcome.
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_exc:
                logger.warning("Failed to clean temp file %s: %s", temp_file_path, str(cleanup_exc))


# Get extracted data
@data_extraction_router.get("/get-extracted-data")
async def get_data(
    workflow_id: str = Query(...),
    collection_name: str = Query(...),
):
    """
    Get extracted data from MongoDB.
    
    Args:
        workflow_id: The workflow id of the extraction
        collection_name: Name of the collection to save the data to
    
    Returns:
        Dictionary containing extraction results and save status
    """
    return await get_extracted_data(workflow_id, collection_name)


