import logging

from .vector_query import query_data as query_vector_db
from .vector_db import add_data as add_to_vector_db
from fastapi import APIRouter, Body, HTTPException, File, UploadFile, BackgroundTasks
from typing import Any,Dict
from services.data_extraction.extract_data import process_document_extraction
import tempfile
import os

logger = logging.getLogger("RAG Router")
rag_router = APIRouter()

# ----------------- Background worker helpers -----------------
async def _run_add_data_background(workflow_id: str, data: Any):
    """Background task that adds data to the vector database."""
    try:
        await add_to_vector_db(workflow_id, data)
        logger.info("Background add_data completed for %s", workflow_id)
    except Exception as exc:
        logger.error("Background add_data failed for %s: %s", workflow_id, str(exc))


async def _run_extract_add_background(temp_file_path: str, workflow_id: str, collection_name: str):
    """Background task that extracts data then ingests it and cleans up temporary file."""
    try:
        result = await process_document_extraction(
            temp_file_path,
            collection_name=collection_name,
            workflow_id=workflow_id,
        )
        await add_to_vector_db(workflow_id, result)
        logger.info("Background extract+add completed for %s", workflow_id)
    except Exception as exc:
        logger.error("Background extract+add failed for %s: %s", workflow_id, str(exc))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_exc:
                logger.warning("Failed to clean temp file %s: %s", temp_file_path, str(cleanup_exc))

@rag_router.post("/add-data", status_code=202)  # background task
async def add_data_endpoint(
    background_tasks: BackgroundTasks,
    workflow_id: str = Body(...),
    data: Any = Body(...),
) -> Dict[str, Any]:
    """
    Append new data (string, markdown, dict, list, Document, etc.) to the collection without overwriting existing points.
    
    Args:
        workflow_id: The workflow id of the collection
        data: The data to add
    """
    try:
        # Schedule background task instead of awaiting directly
        background_tasks.add_task(_run_add_data_background, workflow_id, data)
        return {
            "status": "accepted",
            "workflow_id": workflow_id,
            "message": "Data ingest scheduled and running in background."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Failed to add data to vector DB", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to add data: {str(e)}")

@rag_router.post("/query-data")
async def query_data_endpoint(
    workflow_id: str = Body(...),
    query: str = Body(...),
    *,
    sparse_top_k: int = 3,
    similarity_top_k: int = 3,
    hybrid_top_k: int = 3,
) -> Any:
    """Run a hybrid similarity search over the workflow collection.

    Args:
        workflow_id: The workflow id of the collection
        query: The search query
        sparse_top_k: Number of sparse results to return
        similarity_top_k: Number of similarity results to return
        hybrid_top_k: Number of hybrid results to return
    
    Returns:
        Llama-index `Response` containing answer + source nodes.
    """
    try:
        return await query_vector_db(
            workflow_id=workflow_id,
            query=query,
            sparse_top_k=sparse_top_k,
            similarity_top_k=similarity_top_k,
            hybrid_top_k=hybrid_top_k
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Failed to query vector DB", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to query data: {str(e)}")

@rag_router.post("/extract-and-add-data", status_code=202)  # background task
async def extract_and_add_data(
    background_tasks: BackgroundTasks,
    workflow_id: str = Body(...),
    collection_name: str = Body(...),
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """
    Extract document data and save to both MongoDB and optionally JSON file.
    
    Args:
        workflow_id: The workflow id of the collection
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
        # Schedule background processing task
        background_tasks.add_task(
            _run_extract_add_background,
            temp_file_path,
            workflow_id,
            collection_name,
        )
        temp_file_path = None  # background function handles cleanup
        return {
            "status": "accepted",
            "workflow_id": workflow_id,
            "collection_name": collection_name,
            "message": "Extraction and vector ingest scheduled."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Failed to extract and add data", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to extract and add data: {str(e)}")
    finally:
        # Only clean up temp file here if background scheduling failed
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {str(e)}")

