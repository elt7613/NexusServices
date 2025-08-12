from fastapi import APIRouter

from .utils.create_inbound_dispatch_rule import create_inbound_dispatch_rule
from .utils.delete_inbound_dispatch_rule import delete_inbound_dispatch_rule
from .models import (
    InboundDispatchRuleRequest,
    InboundDispatchRuleResponse,
    DeleteResponse,
)

dispatch_rule_router = APIRouter()

@dispatch_rule_router.post(
    "/create-inbound-dispatch-rule",
    response_model=InboundDispatchRuleResponse,
    summary="Create an inbound dispatch rule",
    description="Creates an inbound SIP dispatch rule via LiveKit API",
    responses={
        200: {"description": "Dispatch rule created successfully"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "Internal server error"},
    },
)
async def create_inbound_dispatch_rule_endpoint(
    payload: InboundDispatchRuleRequest,
) -> InboundDispatchRuleResponse:
    try:
        dispatch = await create_inbound_dispatch_rule(**payload.model_dump())
        return InboundDispatchRuleResponse(
            dispatch_rule_id=dispatch,
            message="Dispatch rule created successfully",
        )
    except Exception as e:
        return InboundDispatchRuleResponse(
            dispatch_rule_id="",
            message=f"Failed to create dispatch rule: {str(e)}",
        )


@dispatch_rule_router.delete(
    "/inbound-dispatch-rule/{sip_dispatch_rule_id}",
    response_model=DeleteResponse,
    summary="Delete an inbound dispatch rule",
    description="Deletes an inbound SIP dispatch rule by its ID",
)
async def delete_inbound_dispatch_rule_endpoint(
    sip_dispatch_rule_id: str,
) -> DeleteResponse:
    try:
        ok = await delete_inbound_dispatch_rule(sip_dispatch_rule_id)
        return DeleteResponse(
            success=ok,
            message=(
                "Dispatch rule deleted successfully"
                if ok
                else "Failed to delete dispatch rule"
            ),
        )
    except Exception as e:
        return DeleteResponse(success=False, message=str(e))
