from fastapi import APIRouter

from .metadata import metadata_router
from .conversation import conversation_router

user_data_router = APIRouter(tags=["Livekit Call Data"])
user_data_router.include_router(metadata_router)
user_data_router.include_router(conversation_router)
