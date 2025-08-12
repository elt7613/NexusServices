from fastapi import APIRouter

from .dispatch_rule import dispatch_rule_router
from .trunk import trunk_router

inbound_call_router = APIRouter()

inbound_call_router.include_router(trunk_router)
inbound_call_router.include_router(dispatch_rule_router)

