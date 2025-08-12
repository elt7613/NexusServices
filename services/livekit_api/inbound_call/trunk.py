from fastapi import APIRouter

from .utils.create_inbound_trunk import create_inbound_trunk_id
from .utils.delete_inbound_trunk import delete_inbound_trunk
from .models import InboundTrunkRequest, InboundTrunkResponse, DeleteResponse

trunk_router = APIRouter()

@trunk_router.post(
    "/create-inbound-trunk-id",
    response_model=InboundTrunkResponse,
    summary="Create an inbound trunk ID",
    description="Creates an inbound trunk ID using LiveKit SIP functionality.",
    responses={
        200: {"description": "Trunk ID created successfully"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "Internal server error"},
    },
)
async def create_inbound_trunk_id_endpoint(
    trunk_request: InboundTrunkRequest,
) -> InboundTrunkResponse:
    try:
        result = await create_inbound_trunk_id(**trunk_request.model_dump())
        return InboundTrunkResponse(
            trunk_id=result,
            message="Trunk ID created successfully",
        )
    except Exception as e:
        return InboundTrunkResponse(
            trunk_id="",
            message=f"Failed to create trunk ID: {str(e)}",
        )


@trunk_router.delete(
    "/inbound-trunk/{trunk_id}",
    response_model=DeleteResponse,
    summary="Delete an inbound trunk",
    description="Deletes an inbound trunk by its ID",
)
async def delete_inbound_trunk_endpoint(trunk_id: str) -> DeleteResponse:
    try:
        ok = await delete_inbound_trunk(trunk_id)
        return DeleteResponse(
            success=ok,
            message=(
                "Trunk deleted successfully" if ok else "Failed to delete trunk"
            ),
        )
    except Exception as e:
        return DeleteResponse(success=False, message=str(e))
