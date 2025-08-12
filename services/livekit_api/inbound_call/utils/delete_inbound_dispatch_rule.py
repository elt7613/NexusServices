from livekit import api
from dotenv import load_dotenv

load_dotenv()

async def delete_inbound_dispatch_rule(sip_dispatch_rule_id: str) -> bool:
    
    livekit_api = api.LiveKitAPI()
    
    try:
        await livekit_api.sip.delete_sip_dispatch_rule(
            api.DeleteSIPDispatchRuleRequest(
                sip_dispatch_rule_id=sip_dispatch_rule_id
            )
        )
        await livekit_api.aclose()
        return True
    except Exception:
        return False

