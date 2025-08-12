import os
from dotenv import load_dotenv

import qdrant_client
from llama_index.core import Settings
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openrouter import OpenRouter

load_dotenv()

class RagConfig:
    def __init__(self):
        self.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        self.google_api_key = os.environ.get("GOOGLE_API_KEY")
        self.qdrant_url = os.environ.get("QDRANT_URL")
        self.qdrant_api_key = os.environ.get("QDRANT_API_KEY")
        
        # LLM
        Settings.llm = OpenRouter(
            api_key=self.openrouter_api_key, 
            model="google/gemini-2.0-flash-001",  
            max_tokens=10000,
            context_window=1000000,
            temperature=0.3     
        )

        # Embedding model
        Settings.embed_model = GeminiEmbedding(
            model_name="models/embedding-001",  
            api_key=self.google_api_key
        )

        # Chunking strategy for extracted json data
        Settings.node_parser = SentenceSplitter(
            chunk_size=2048,
            chunk_overlap=50,
            separator="\n\n",
        )
        
        # Qdrant client
        self.client = qdrant_client.QdrantClient(
            url=f"{self.qdrant_url}:80",
            api_key=self.qdrant_api_key,
            timeout=30
        )

        # Async Qdrant client
        self.aclient = qdrant_client.AsyncQdrantClient(
            url=f"{self.qdrant_url}:80",
            api_key=self.qdrant_api_key,
            timeout=30
        )