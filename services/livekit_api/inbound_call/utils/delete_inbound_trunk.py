import asyncio
from livekit import api
from dotenv import load_dotenv
from livekit.protocol.sip import DeleteSIPTrunkRequest

load_dotenv()

async def delete_inbound_trunk(trunk_id: str):
    
    livekit_api = api.LiveKitAPI()
    
    try:
        await livekit_api.sip.delete_sip_trunk(
            DeleteSIPTrunkRequest(
                sip_trunk_id=trunk_id
            )
        )
        await livekit_api.aclose()
        return True
    except Exception as e:
        print(e)
        return False
