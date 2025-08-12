import logging
import json
from typing import Dict, Any, Optional
from livekit import api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("caller")

async def make_outbound_call(
    user_id: str,
    workflow_id: str,
    system_agent_name: str,
    room_name: str,
    agent_name: str,
    agent_gender: str,
    agent_language: str,
    agent_number: str,
    number_from: str,
    number_to_call: str,
    outbound_trunk_id: str,
    tts_model: str,
    language_tts: str,
    voice_id: str,
    llm_model: str,
    stt_model: str,
    company_name: str,
    individual_name: str,
    knowledge_base: str,
    custom_instructions: str = None,
    campaign_objective: str = None,
    campaign_type: str = None,
    campaign_briefing: str = None,
    target_audience: str = None,
    key_talking_points: str = None,
    objection_responses: str = None
) -> Dict[str, Any]:
    """
    Make an outbound call using LiveKit SIP and agent dispatch functionality.
    
    Returns:
        Dict containing dispatch_id and sip_participant_id if successful, None otherwise.
    """
    # Dynamic agent config
    agent_config = {
        "user_id": user_id,
        "workflow_id": workflow_id,
        "system_agent_name": system_agent_name,
        "custom_instructions": custom_instructions,
        "agent_name": agent_name,
        "agent_gender": agent_gender,
        "agent_language": agent_language,
        "agent_number": agent_number,
        "room_name": room_name,
        "number_to_call": number_to_call,
        "number_from": number_from,
        "outbound_trunk_id": outbound_trunk_id,
        "language_tts": language_tts,
        "company_name": company_name,
        "individual_name": individual_name,
        "knowledge_base": knowledge_base,
        "llm_model": llm_model,
        "stt_model": stt_model,
        "tts_model": tts_model,
        "voice_id": voice_id,
        "campaign_objective": campaign_objective,
        "campaign_type": campaign_type,
        "campaign_briefing": campaign_briefing,
        "target_audience": target_audience,
        "key_talking_points": key_talking_points,
        "objection_responses": objection_responses
    }
    metadata = {
        "phone_number": number_to_call,
        "agent_config": agent_config,
        "standalone_call": True,
    }

    lkapi = api.LiveKitAPI()
    result = {
        "dispatch_id": None,
        "sip_participant_id": None,
        "sip_call_id": None
    }

    try:
        #logger.info(f"Creating agent dispatch for room: {room_name}")
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="Calling-Agent-System",
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )
        #logger.info(f"Dispatch created: {dispatch}")
        result["dispatch_id"] = dispatch.id
    except Exception as e:
        logger.error(f"Failed to create dispatch: {e}")
        await lkapi.aclose()
        return result

    try:
        #logger.info(f"Creating SIP participant for room: {room_name}")
        sip_participant = await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_trunk_id=outbound_trunk_id,
                sip_number=number_from,
                sip_call_to=number_to_call,
                participant_identity=f"sip-{workflow_id}",
                krisp_enabled = True,
                #wait_until_answered=True,
            )
        )
        #logger.info(f"SIP participant created: {sip_participant}")
        result["sip_participant_id"] = sip_participant.participant_id
        result["sip_call_id"] = sip_participant.sip_call_id
    except api.TwirpError as e:
        logger.error(f"SIP Error: {e.message}")
        if e.metadata:
            sip_status = e.metadata.get('sip_status_code')
            sip_message = e.metadata.get('sip_status')
            logger.error(f"SIP Status: {sip_status} - {sip_message}")
    except Exception as e:
        logger.error(f"Error creating SIP participant: {e}")
    finally:
        await lkapi.aclose()
    
    return result
