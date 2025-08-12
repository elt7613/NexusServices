from fastapi import APIRouter

from .call import call_router
from .trunk import trunk_router

outbound_call_router = APIRouter()

outbound_call_router.include_router(trunk_router)
outbound_call_router.include_router(call_router)
