import asyncio
import httpx
import uuid

async def create_outbound_trunk_id():

    # API endpoint URL (adjust as needed for your setup)
    api_url = "http://0.0.0.0:8021/livekit/create-outbound-trunk-id"

    data = {
        "name": "My trunk",
        "address": "livekittest123.pstn.twilio.com",
        "numbers": ['*'],
        "auth_username": "elt",
        "auth_password": "Password@123"
    }
    
    try:
        # Make the API call
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=data)
            
        # Print the response
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Check if the call was successful
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success"):
                print("Outbound trunk ID created successfully!")
                print(f"Trunk ID: {response_data.get('trunk_id')}")
            else:
                print(f"Failed to create outbound trunk ID: {response_data.get('message')}")
        else:
            print(f"API request failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error making API request: {str(e)}")