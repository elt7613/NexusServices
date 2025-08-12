from pydantic import BaseModel
from typing import Optional, List, Any

# -------- Inbound Trunk Models --------
class InboundTrunkRequest(BaseModel):
    trunk_name: str
    trunk_numbers: List[str]

class InboundTrunkResponse(BaseModel):
    trunk_id: str
    message: Optional[str] = None

class DeleteResponse(BaseModel):
    success: bool
    message: Optional[str] = None

# -------- Inbound Dispatch Rule Models --------
class InboundDispatchRuleRequest(BaseModel):
    trunk_id: str
    dispatch_rule_name: str

    user_id: str
    workflow_id: str
    system_agent_name: str
    agent_name: str
    agent_gender: str
    agent_language: str
    agent_number: str
    inbound_trunk_id: str
    tts_model: str
    language_tts: str
    voice_id: str
    llm_model: str
    stt_model: str

    company_name: Optional[str] = None
    individual_name: Optional[str] = None
    knowledge_base: Optional[str] = None
    custom_instructions: Optional[str] = None
    campaign_objective: Optional[str] = None
    campaign_type: Optional[str] = None
    campaign_briefing: Optional[str] = None
    target_audience: Optional[str] = None
    key_talking_points: Optional[str] = None
    objection_responses: Optional[str] = None

class InboundDispatchRuleResponse(BaseModel):
    dispatch_rule_id: str
    message: Optional[str] = None
