from fastapi import APIRouter
from .utils.create_outbound_trunk import create_outbound_trunk_id
from .models import OutboundTrunkRequest, OutboundTrunkResponse

trunk_router = APIRouter()

@trunk_router.post(
    "/create-outbound-trunk-id",
    response_model=OutboundTrunkResponse,
    summary="Create an outbound trunk ID",
    description="Creates an outbound trunk ID using LiveKit SIP functionality.",
    responses={
        200: {"description": "Trunk ID created successfully"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "Internal server error"}
    }
)
async def create_outbound_trunk_id_endpoint(trunk_request: OutboundTrunkRequest) -> OutboundTrunkResponse:
    """
    Create an outbound trunk ID using LiveKit SIP functionality.
    
    This endpoint creates an outbound trunk ID to initiate an outbound call.
    """
    try:
        result = await create_outbound_trunk_id(**trunk_request.model_dump())
        
        return OutboundTrunkResponse(
            trunk_id=result,
            message="Trunk ID created successfully"
        )
    except Exception as e:
        return OutboundTrunkResponse(
            trunk_id="",
            message=f"Failed to create trunk ID: {str(e)}"
        )