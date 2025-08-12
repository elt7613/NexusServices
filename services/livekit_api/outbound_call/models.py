from pydantic import BaseModel
from typing import Optional

#----------- Outbound Trunk ID Request and Response Models -----------
class OutboundTrunkRequest(BaseModel):
    trunk_name: str
    trunk_address: str
    trunk_numbers: list
    trunk_auth_username: str
    trunk_auth_password: str

class OutboundTrunkResponse(BaseModel):
    trunk_id: str
    message: Optional[str] = None
    
#----------- Outbound Call Request and Response Models -----------
class OutboundCallRequest(BaseModel):
    user_id: str
    system_agent_name: str
    workflow_id: str
    room_name: str
    agent_name: str
    agent_gender: str
    agent_language: str
    agent_number: str
    number_from: str
    number_to_call: str
    outbound_trunk_id: str
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

class OutboundCallResponse(BaseModel):
    success: bool
    message: str
    dispatch_id: Optional[str] = None
    sip_participant_id: Optional[str] = None
    sip_call_id: Optional[str] = None

    
    
