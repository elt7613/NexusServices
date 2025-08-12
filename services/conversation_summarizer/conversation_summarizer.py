from pydantic_ai import Agent
from config.llms import conversation_summarizer_llm
from prompts.conversation_summarizer import conversation_summarizer_prompt
from models.schema import ConversationSummaryModel
from fastapi import APIRouter
from utils.agent_execution import execute_agent_safely

# FastAPI router setup
conversation_summarizer_router = APIRouter()

conversation_summarizer = Agent(
    model=conversation_summarizer_llm,
    system_prompt=conversation_summarizer_prompt,
    output_type=ConversationSummaryModel,
    retries=5
)

@conversation_summarizer_router.post("/summarize-conversation", response_model=ConversationSummaryModel)
async def summarize_conversation(conversation_history: str) -> ConversationSummaryModel:
    prompt = f"""
    # Conversation history: {conversation_history}

    *** Summarize the conversation in a concise and detailed manner. ***
    """

    response = await execute_agent_safely(conversation_summarizer, prompt)
    return response.output
