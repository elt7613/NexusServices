from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import os
from dotenv import load_dotenv

load_dotenv()

openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
base_url = os.environ.get("OPENROUTER_BASE_URL")

conversation_summarizer_llm = OpenAIModel(
    'meta-llama/llama-4-scout',
    provider=OpenAIProvider(
        base_url=base_url,
        api_key=openrouter_api_key,
    ),
)