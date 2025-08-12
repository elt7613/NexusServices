import asyncio
from livekit import api
from dotenv import load_dotenv
import uuid,json

load_dotenv()

async def create_inbound_dispatch_rule(
    trunk_id:str,
    dispatch_rule_name: str,
    user_id:str,
    workflow_id:str,
    system_agent_name:str,
    agent_name:str,
    agent_gender:str,
    agent_language:str,
    agent_number:str,
    inbound_trunk_id:str,
    tts_model:str,
    language_tts:str,
    voice_id:str,
    llm_model:str,
    stt_model:str,
    company_name:str,
    individual_name:str,
    knowledge_base:str,
    custom_instructions:str,
    campaign_objective:str,
    campaign_type:str,
    campaign_briefing:str,
    target_audience:str,
    key_talking_points:str,
    objection_responses:str
) -> str:
    lkapi = api.LiveKitAPI()

    data = {
        "user_id":user_id,
        "system_agent_name":system_agent_name,
        "workflow_id":workflow_id,
        "agent_name":agent_name,
        "agent_gender":agent_gender,
        "agent_language":agent_language,
        "agent_number": agent_number,
        "inbound_trunk_id": inbound_trunk_id,
        "tts_model":tts_model,
        "language_tts":language_tts,
        "voice_id":voice_id,
        "llm_model":llm_model,
        "stt_model":stt_model,
        "company_name":company_name,
        "individual_name":individual_name,
        "knowledge_base":knowledge_base,
        "custom_instructions":custom_instructions,
        "campaign_objective":campaign_objective,
        "campaign_type":campaign_type,
        "campaign_briefing":campaign_briefing,
        "target_audience":target_audience,
        "key_talking_points":key_talking_points,
        "objection_responses":objection_responses
    }

    # Create a dispatch rule to place each caller in a separate room
    rule = api.SIPDispatchRule(
        dispatch_rule_individual = api.SIPDispatchRuleIndividual(
            room_prefix = 'Inbound_Call-',
        )
    )

    request = api.CreateSIPDispatchRuleRequest(
        dispatch_rule = api.SIPDispatchRuleInfo(
            rule = rule,
            name = dispatch_rule_name,
            trunk_ids = [trunk_id],
            room_config=api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(
                    agent_name="Calling-Agent-System",
                    metadata=json.dumps(data),
                )]
            )
        )
    )

    dispatch = await lkapi.sip.create_sip_dispatch_rule(request)
    await lkapi.aclose()

    return str(dispatch.sip_dispatch_rule_id)
