import asyncio
import httpx
import uuid,os

company_context = """
    **WuShoes – Summary**

WuShoes is an innovative footwear company focused on delivering high-quality, stylish, and comfortable shoes across diverse categories. Its core values include innovation, quality, sustainability, customer satisfaction, and continuous improvement.

**Key Highlights:**

* **Product Lines:** Lifestyle, Performance, Professional, and Specialized segments (including eco-friendly and orthopedic shoes).
* **Manufacturing:** High-tech, sustainable production with advanced materials and strict quality control.
* **Technology:** Emphasis on R\&D, biomechanical design, 3D prototyping, and digital tools like virtual try-ons.
* **Market Focus:** Urban professionals, athletes, fashion-forward individuals aged 16–55.
* **Sustainability:** Recyclable components, reduced carbon footprint, and ethical sourcing.
* **Customer Experience:** Strong online presence, personalized services, loyalty programs, and responsive support.
* **Future Goals:** Global expansion, new product innovation, enhanced digital platforms, and increased sustainability investments.

WuShoes positions itself not just as a footwear brand, but as a complete lifestyle solution.

    """

instructions = "you'll be reciving calls from delivery person and you'll have to guid them to leave the parcle neare the door and the adddress is itpl house 49 and leave the parcle near by the door where the dog is.the dog wont bite"

# Configuration
user_id = "user-test123"
system_agent_name = "bulk_calling_agent" #"appointment_agent" #"bulk_calling_agent" #"personal_agent" #"customer_support_agent"
custom_instructions = None #"inform the user regarding the appointment for web 6th july 2025 is at 4pm and the take confirmation if he/she will be available. user's name ELT,email: elt@gmail,com,phone number: 1234567897"
workflow_id = str(uuid.uuid4()) #"a673504a-0733-4276-ae0b-24fb547c6faf" #str(uuid.uuid4())
room_name = f"Outbound_call-{workflow_id}_{str(uuid.uuid4())}"
agent_name = "Alita"
agent_gender = "Female"
agent_language = "multilingual"
agent_number = "+15075123753"
outbound_trunk_id = "ST_4iXEXw7jboku" #"ST_KspaAwCjKvQV" #os.getenv("SIP_OUTBOUND_TRUNK_ID")
number_to_call = "+917795341235" #"+918770975421"
number_from = "+15075123753" #"+19387585572" 
company_name = "Wu shoes"
individual_name = None
knowledge_base = company_context
voice_id = "95d51f79-c397-46f9-b49a-23763d3eaa2d"
language_tts = "en"
llm_model = "openai/gpt-4.1-mini"
stt_model = "nova-3"
tts_model = "sonic-2"

campaign_objective = "geting feedback"
campaign_type = "feedback"
campaign_briefing = "want to get the feedback from the customers regarding the shoes taht hey bought from wushoes "
target_audience = "the perosns who bought the wushoes's shoes"
key_talking_points = "geeting the feed of wushoes from peoples"
objection_responses = "we'll note taht and improve it"

def create_test_call_request():
    """Create a test request for the outbound call API."""
    return {
        "user_id":user_id,
        "workflow_id":workflow_id,
        "system_agent_name":system_agent_name,
        "room_name":room_name,
        "agent_name":agent_name,
        "agent_gender":agent_gender,
        "agent_language":agent_language,
        "agent_number":agent_number,
        "number_from":number_from,
        "number_to_call":number_to_call,
        "outbound_trunk_id":outbound_trunk_id,
        "tts_model":tts_model,
        "language_tts":language_tts,
        "voice_id":voice_id,
        "llm_model":llm_model,
        "stt_model":stt_model,
        "company_name":company_name,
        "individual_name":individual_name,
        "knowledge_base":knowledge_base,
        "custom_instructions":custom_instructions,
        "campaign_objective":campaign_objective,
        "campaign_type":campaign_type,
        "campaign_briefing":campaign_briefing,
        "target_audience":target_audience,
        "key_talking_points":key_talking_points,
        "objection_responses":objection_responses
    }


async def test_outbound_call_api():
    """Test the outbound call API endpoint."""
    # Create a test request
    test_request = create_test_call_request()
    
    # Convert to dict for JSON serialization
    request_data = test_request
    
    # API endpoint URL (adjust as needed for your setup)
    api_url = "http://tkscw8048ssw0ss4kokkss0c.106.51.142.222.sslip.io/livekit/make-outbound-call"
    
    try:
        # Make the API call
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=request_data)
            
        # Print the response
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

    except Exception as e:
        print(f"Error making API request: {str(e)}")


def run_test():
    """Run the test synchronously."""
    asyncio.run(test_outbound_call_api())


if __name__ == "__main__":
    run_test()
