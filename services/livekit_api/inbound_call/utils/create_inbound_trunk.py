import asyncio

from livekit import api
from dotenv import load_dotenv

load_dotenv()

async def create_inbound_trunk_id(
  trunk_name: str,
  trunk_numbers: list,
) -> str:
    livekit_api = api.LiveKitAPI()

    trunk = api.SIPInboundTrunkInfo(
        name = trunk_name,
        numbers = trunk_numbers,
        krisp_enabled = True,
    )

    request = api.CreateSIPInboundTrunkRequest(
        trunk = trunk
    )

    trunk = await livekit_api.sip.create_sip_inbound_trunk(request)
    await livekit_api.aclose()

    return str(trunk.sip_trunk_id)
