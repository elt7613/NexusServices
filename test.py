from livekit import api
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def is_call_picked_up(livekit_client, room_name, participant_identity):
    try:
        participants_response = await livekit_client.room.list_participants(
            api.ListParticipantsRequest(room=room_name)
        )
        participants = participants_response.participants

        for p in participants:
            if hasattr(p, 'identity') and p.identity == participant_identity:
                if hasattr(p, 'attributes') and p.attributes:
                    call_status = p.attributes.get("sip.callStatus")
                    return call_status == "active"
                else:
                    return False
        
        return False
        
    except Exception as e:
        return False

async def main():
    livekit_client = api.LiveKitAPI()
    call_id = "a673504a-0733-4276-ae0b-24fb547c6faf"
    room_name = f"standalone-call-{call_id}"
    sip_participant_identity = f"sip-{call_id}"
    
    c = 0
    while True:
        picked_up = await is_call_picked_up(livekit_client, room_name, sip_participant_identity)
        if picked_up:
            print("Call picked up!")
            break
        else:
            print("Call not picked up yet...")
            
        c += 1
        print(f"Attempt {c}")
        await asyncio.sleep(1)
        
        # Add a reasonable limit to avoid infinite loops
        if c > 60:  # Stop after 60 attempts (1 minute)
            print("Timeout reached, stopping...")
            break

if __name__ == "__main__":
    asyncio.run(main())

