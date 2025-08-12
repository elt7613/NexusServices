import httpx
from typing import Any, Dict, List, Optional, Tuple

BASE_URL = "http://0.0.0.0:8021"


async def add_call_metadata(
    user_id: str = "test-user",
    workflow_id: str = "test-workflow",
    call_id: str = "test-call",
    metadata: Any = None,
    mode: str = "merge",
) -> Tuple[int, Dict[str, Any]]:
    """
    POST /livekit/add-call-metadata
    Returns (status_code, response_json)
    """
    if metadata is None:
        metadata = {"source": "test", "tags": ["demo"], "score": 0.9}

    url = f"{BASE_URL}/livekit/add-call-metadata"
    payload = {
        "user_id": user_id,
        "workflow_id": workflow_id,
        "call_id": call_id,
        "metadata": metadata,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params={"mode": mode}, json=payload)
        data: Dict[str, Any] = {}
        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text}
        return resp.status_code, data


async def add_call_conversation(
    user_id: str = "test-user",
    workflow_id: str = "test-workflow",
    call_id: str = "test-call",
    messages: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """
    POST /livekit/add-call-conversation
    Returns (status_code, response_json)
    """
    if messages is None:
        messages = [
            {"role": "user", "text": "Hello"},
            {"role": "assistant", "text": "Hi there!"},
        ]

    url = f"{BASE_URL}/livekit/add-call-conversation"
    payload = {
        "user_id": user_id,
        "workflow_id": workflow_id,
        "call_id": call_id,
        "messages": messages,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        data: Dict[str, Any] = {}
        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text}
        return resp.status_code, data
