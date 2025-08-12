import os, asyncio, json
import qdrant_client
from llama_index.core import VectorStoreIndex
from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import QueryBundle
from llama_index.core import VectorStoreIndex, Document
from .config import RagConfig
import nest_asyncio
from typing import Any, List

from dotenv import load_dotenv

load_dotenv()

nest_asyncio.apply()

# Qdrant clients (sync / async)
client = RagConfig().client
aclient = RagConfig().aclient

def _get_vector_store(workflow_id: str) -> QdrantVectorStore:
    """
    Return a QdrantVectorStore bound to a specific collection.

    Args:
        workflow_id: The workflow id of the collection
    
    Returns:
        QdrantVectorStore object
    """
    return QdrantVectorStore(
        client=client,
        aclient=aclient,
        collection_name=workflow_id,
        enable_hybrid=True,
        fastembed_sparse_model="Qdrant/bm25",
    )


def _normalize_to_documents(input_data: Any) -> List[Document]:
    """
    Convert various input types into a list of Document objects.

    Args:
        input_data: The input data to convert
    
    Returns:
        List of Document objects
    """
    docs: List[Document] = []

    if input_data is None:
        return docs

    # Already a Document
    if isinstance(input_data, Document):
        return [input_data]

    # Iterable -> flatten
    if isinstance(input_data, (list, tuple, set)):
        for item in input_data:
            docs.extend(_normalize_to_documents(item))
        return docs

    # Dict -> JSON string
    if isinstance(input_data, dict):
        try:
            text = json.dumps(input_data, ensure_ascii=False, indent=2)
        except Exception:
            text = str(input_data)
        docs.append(Document(text=text, metadata={"source_type": "dict"}))
        return docs

    # Fallback to string representation
    docs.append(Document(text=str(input_data)))
    return docs

async def add_data(workflow_id: str, data: Any) -> None:
    """
    Append new data (string, markdown, dict, list, Document, etc.) to the collection without overwriting existing points.
    
    Args:
        workflow_id: The workflow id of the collection
        data: The data to add
    """
    vector_store = _get_vector_store(workflow_id)

    documents = _normalize_to_documents(data)
    if not documents:
        return

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: VectorStoreIndex.from_documents(
            documents,
            storage_context=StorageContext.from_defaults(vector_store=vector_store),
        ),
    )