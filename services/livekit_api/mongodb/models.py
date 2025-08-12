from pydantic import BaseModel
from typing import Any


class AddMetadataRequest(BaseModel):
    user_id: str
    workflow_id: str
    call_id: str
    metadata: Any


class AddConversationRequest(BaseModel):
    user_id: str
    workflow_id: str
    call_id: str
    messages: Any
