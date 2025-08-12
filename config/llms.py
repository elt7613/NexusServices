from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
import os
from dotenv import load_dotenv

load_dotenv()

openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")

conversation_summarizer_llm = OpenAIModel(
    'meta-llama/llama-4-scout',
    provider=OpenRouterProvider(
        api_key=openrouter_api_key,
    ),
)