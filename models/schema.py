from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ConversationSummaryModel(BaseModel):
    """Request model for conversation summarization."""
    conversation_summary: str
