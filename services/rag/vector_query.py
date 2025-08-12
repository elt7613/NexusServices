from __future__ import annotations

import asyncio
from typing import Any, Optional

import nest_asyncio
from llama_index.core import StorageContext, VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore

from .config import RagConfig

nest_asyncio.apply()

# Shared Qdrant clients (sync + async)
client = RagConfig().client
aclient = RagConfig().aclient


def _build_query_engine(
    workflow_id: str,
    *,
    sparse_top_k: int = 3,
    similarity_top_k: int = 3,
    hybrid_top_k: int = 3,
) -> Any:
    """
    Create and return a llama-index QueryEngine for a given collection.
    
    Args:
        workflow_id: The workflow id of the collection
        sparse_top_k: Number of sparse results to return
        similarity_top_k: Number of similarity results to return
        hybrid_top_k: Number of hybrid results to return
    
    Returns:
        llama-index QueryEngine object
    """
    vector_store = QdrantVectorStore(
        client=client,
        aclient=aclient,
        collection_name=workflow_id,
        enable_hybrid=True,
        fastembed_sparse_model="Qdrant/bm25",
    )

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=StorageContext.from_defaults(vector_store=vector_store),
    )

    return index.as_query_engine(
        use_async=True,
        vector_store_query_mode="hybrid",
        sparse_top_k=sparse_top_k,
        similarity_top_k=similarity_top_k,
        hybrid_top_k=hybrid_top_k,
        llm=Settings.llm,
    )


async def query_data(
    workflow_id: str,
    query: str,
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
    query_engine = _build_query_engine(
        workflow_id,
        sparse_top_k=sparse_top_k,
        similarity_top_k=similarity_top_k,
        hybrid_top_k=hybrid_top_k,
    )

    return await query_engine.aquery(query)

