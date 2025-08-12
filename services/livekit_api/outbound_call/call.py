from fastapi import APIRouter, Depends
from .utils.outbound_caller import make_outbound_call
from .models import OutboundCallRequest, OutboundCallResponse

call_router = APIRouter()

@call_router.post(
    "/make-outbound-call",
    response_model=OutboundCallResponse,
    summary="Make an outbound call",
    description="Initiates an outbound call using LiveKit SIP and agent dispatch functionality.",
    responses={
        200: {"description": "Call initiated successfully"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "Internal server error"}
    }
)
async def make_outbound_call_endpoint(call_request: OutboundCallRequest) -> OutboundCallResponse:
    """
    Make an outbound call using LiveKit SIP and agent dispatch.
    
    This endpoint creates an agent dispatch and SIP participant to initiate an outbound call.
    """
    try:
        result = await make_outbound_call(**call_request.model_dump())
        
        return OutboundCallResponse(
            success=True,
            message="Call initiated successfully",
            dispatch_id=result.get('dispatch_id') if result else None,
            sip_participant_id=result.get('sip_participant_id') if result else None,
            sip_call_id=result.get('sip_call_id') if result else None
        )
    except Exception as e:
        return OutboundCallResponse(
            success=False,
            message=f"Failed to initiate call: {str(e)}"
        )