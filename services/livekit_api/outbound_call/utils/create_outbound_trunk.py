import asyncio
from dotenv import load_dotenv

from livekit import api
from livekit.protocol.sip import CreateSIPOutboundTrunkRequest, SIPOutboundTrunkInfo

load_dotenv()

async def create_outbound_trunk_id(
  trunk_name: str,
  trunk_address: str,
  trunk_numbers: list,
  trunk_auth_username: str,
  trunk_auth_password: str
) -> str:
  lkapi = api.LiveKitAPI()

  trunk = SIPOutboundTrunkInfo(
    name = trunk_name,
    address = trunk_address,
    numbers = trunk_numbers,
    auth_username = trunk_auth_username,
    auth_password = trunk_auth_password
  )

  request = CreateSIPOutboundTrunkRequest(
    trunk = trunk
  )
  trunk = await lkapi.sip.create_sip_outbound_trunk(request)
  await lkapi.aclose()

  return f"{trunk.sip_trunk_id}"
