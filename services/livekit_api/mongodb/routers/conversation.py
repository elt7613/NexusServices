import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from ..db import users, workflows, calls
from ..utils import now_ist_iso, parse_any_dt_to_ist, parse_bound_date_only, format_ist_ampm
from ..models import AddConversationRequest

logger = logging.getLogger(__name__)

conversation_router = APIRouter()


@conversation_router.post("/add-call-conversation", summary="Append messages to a call conversation")
def add_conversation(req: AddConversationRequest):
    try:
        now = now_ist_iso()

        def _normalize_messages(obj: Any):
            msgs: List[Dict[str, Any]] = []
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        m = dict(item)
                    else:
                        m = {"data": item}
                    msgs.append(m)
            else:
                if isinstance(obj, dict):
                    msgs.append(dict(obj))
                else:
                    msgs.append({"data": obj})
            return msgs

        msgs = _normalize_messages(req.messages)

        # Ensure user and workflow exist
        users().update_one(
            {"user_id": req.user_id},
            {"$setOnInsert": {"user_id": req.user_id, "created_at": now}, "$set": {"updated_at": now}},
            upsert=True,
        )
        workflows().update_one(
            {"user_id": req.user_id, "workflow_id": req.workflow_id},
            {"$setOnInsert": {"user_id": req.user_id, "workflow_id": req.workflow_id, "created_at": now}, "$set": {"updated_at": now}},
            upsert=True,
        )

        res = calls().update_one(
            {"user_id": req.user_id, "workflow_id": req.workflow_id, "call_id": req.call_id},
            {
                "$setOnInsert": {
                    "user_id": req.user_id,
                    "workflow_id": req.workflow_id,
                    "call_id": req.call_id,
                    "metadata": {},
                    "created_at": now,
                },
                "$push": {"messages": {"$each": msgs}},
                "$set": {"updated_at": now},
            },
            upsert=True,
        )
        created = res.upserted_id is not None
        return {"appended": len(msgs), "created": created}
    except Exception as e:
        logger.exception("Error adding conversation")
        raise HTTPException(status_code=500, detail=str(e))


@conversation_router.get("/get-call-conversation", summary="Fetch call conversation by user/workflow/call with optional date range")
def get_conversation(
    user_id: str = Query(..., min_length=1),
    workflow_id: Optional[str] = Query(None, min_length=1),
    call_id: Optional[str] = Query(None, min_length=1),
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD, IST) for filtering messages/calls"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD, IST) for filtering messages/calls"),
    limit: Optional[int] = Query(None, ge=1),
):
    try:
        q = {"user_id": user_id}
        if workflow_id:
            q["workflow_id"] = workflow_id
        if call_id:
            q["call_id"] = call_id

        projection = {"_id": 0, "user_id": 1, "workflow_id": 1, "call_id": 1, "messages": 1, "created_at": 1, "updated_at": 1}

        # bounds
        try:
            start_dt = parse_bound_date_only(start, as_end=False) if start else None
            end_dt = parse_bound_date_only(end, as_end=True) if end else None
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        def _call_in_range(doc: Dict[str, Any]) -> bool:
            base = doc.get("updated_at") or doc.get("created_at")
            dt = parse_any_dt_to_ist(base)
            if dt is None:
                return True
            if start_dt and dt < start_dt:
                return False
            if end_dt and dt > end_dt:
                return False
            return True

        def _filter_msgs(msgs_: List[Dict[str, Any]]):
            if start_dt is None and end_dt is None:
                return msgs_
            out = []
            for m in msgs_:
                dt = parse_any_dt_to_ist(m.get("timestamp"))
                if dt is None:
                    out.append(m)
                    continue
                if start_dt and dt < start_dt:
                    continue
                if end_dt and dt > end_dt:
                    continue
                out.append(m)
            return out

        def maybe_limit(msgs_: List[Dict[str, Any]]):
            if limit is not None:
                return msgs_[:limit]
            return msgs_

        if call_id:
            doc = calls().find_one(q, projection)
            if not doc:
                raise HTTPException(status_code=404, detail="Call not found")
            if not _call_in_range(doc):
                raise HTTPException(status_code=404, detail="No matching call in the given time range")
            msgs = doc.get("messages", []) or []
            msgs = maybe_limit(_filter_msgs(msgs))
            return {
                "user_id": doc["user_id"],
                "workflow_id": doc["workflow_id"],
                "call_id": doc["call_id"],
                "messages": msgs,
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
                "created_at_display": format_ist_ampm(doc.get("created_at")),
                "updated_at_display": format_ist_ampm(doc.get("updated_at")),
            }
        elif workflow_id:
            docs = [d for d in calls().find(q, projection) if _call_in_range(d)]
            workflows_calls = []
            for d in docs:
                msgs = maybe_limit(_filter_msgs(d.get("messages", []) or []))
                workflows_calls.append({
                    "call_id": d["call_id"],
                    "messages": msgs,
                    "created_at": d.get("created_at"),
                    "updated_at": d.get("updated_at"),
                    "created_at_display": format_ist_ampm(d.get("created_at")),
                    "updated_at_display": format_ist_ampm(d.get("updated_at")),
                })
            return {"user_id": user_id, "workflow_id": workflow_id, "calls": workflows_calls}
        else:
            docs = [d for d in calls().find(q, projection) if _call_in_range(d)]
            wf_map: Dict[str, List[Dict[str, Any]]] = {}
            for d in docs:
                wf = d["workflow_id"]
                msgs = maybe_limit(_filter_msgs(d.get("messages", []) or []))
                wf_map.setdefault(wf, []).append({
                    "call_id": d["call_id"],
                    "messages": msgs,
                    "created_at": d.get("created_at"),
                    "updated_at": d.get("updated_at"),
                    "created_at_display": format_ist_ampm(d.get("created_at")),
                    "updated_at_display": format_ist_ampm(d.get("updated_at")),
                })
            workflows_ = [{"workflow_id": wf, "calls": calls_} for wf, calls_ in wf_map.items()]
            return {"user_id": user_id, "workflows": workflows_}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching conversation")
        raise HTTPException(status_code=500, detail=str(e))


@conversation_router.get("/get-latest-call-conversation", summary="Latest call conversation for a workflow")
def get_latest_call_conversation(
    user_id: str = Query(..., min_length=1),
    workflow_id: str = Query(..., min_length=1),
    limit: Optional[int] = Query(None, ge=1),
):
    try:
        projection = {"_id": 0, "user_id": 1, "workflow_id": 1, "call_id": 1, "messages": 1, "created_at": 1, "updated_at": 1}
        cursor = (
            calls()
            .find({"user_id": user_id, "workflow_id": workflow_id}, projection)
            .sort([("updated_at", -1), ("created_at", -1)])
            .limit(1)
        )
        doc = next(cursor, None)
        if not doc:
            raise HTTPException(status_code=404, detail="No calls found for workflow")
        msgs = doc.get("messages", []) or []
        if limit is not None:
            msgs = msgs[:limit]
        return {
            "user_id": doc["user_id"],
            "workflow_id": doc["workflow_id"],
            "call_id": doc["call_id"],
            "messages": msgs,
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
            "created_at_display": format_ist_ampm(doc.get("created_at")),
            "updated_at_display": format_ist_ampm(doc.get("updated_at")),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching latest call conversation")
        raise HTTPException(status_code=500, detail=str(e))


@conversation_router.delete("/delete-call-conversation", summary="Delete call messages by user/workflow/call with optional date range (IST)")
def delete_call_conversation(
    user_id: str = Query(..., min_length=1),
    workflow_id: Optional[str] = Query(None, min_length=1),
    call_id: Optional[str] = Query(None, min_length=1),
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD, IST)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD, IST)"),
):
    try:
        base_q = {"user_id": user_id}
        if workflow_id:
            base_q["workflow_id"] = workflow_id
        if call_id:
            base_q["call_id"] = call_id

        projection = {"_id": 0, "user_id": 1, "workflow_id": 1, "call_id": 1, "messages": 1, "created_at": 1, "updated_at": 1}

        try:
            start_dt = parse_bound_date_only(start, as_end=False) if start else None
            end_dt = parse_bound_date_only(end, as_end=True) if end else None
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        def _call_in_range(doc: Dict[str, Any]) -> bool:
            base = doc.get("updated_at") or doc.get("created_at")
            dt = parse_any_dt_to_ist(base)
            if dt is None:
                return True
            if start_dt and dt < start_dt:
                return False
            if end_dt and dt > end_dt:
                return False
            return True

        def _msg_in_range(ts: Any) -> bool:
            dt = parse_any_dt_to_ist(ts)
            if dt is None:
                return True
            if start_dt and dt < start_dt:
                return False
            if end_dt and dt > end_dt:
                return False
            return True

        now = now_ist_iso()

        if call_id:
            doc = calls().find_one(base_q, projection)
            if not doc:
                raise HTTPException(status_code=404, detail="Call not found")
            if not _call_in_range(doc):
                raise HTTPException(status_code=404, detail="No matching call in the given time range")
            msgs = doc.get("messages", []) or []
            if start_dt is None and end_dt is None:
                new_msgs: List[Dict[str, Any]] = []
            else:
                new_msgs = [m for m in msgs if not _msg_in_range(m.get("timestamp"))]
            removed = len(msgs) - len(new_msgs)
            calls().update_one(base_q, {"$set": {"messages": new_msgs, "updated_at": now}})
            return {"matched_calls": 1, "modified_calls": 1 if removed > 0 else 0, "removed_messages": removed}

        # Multiple calls case
        total_matched = 0
        total_modified = 0
        total_removed = 0
        for d in calls().find(base_q, projection):
            if not _call_in_range(d):
                continue
            total_matched += 1
            msgs = d.get("messages", []) or []
            if start_dt is None and end_dt is None:
                new_msgs: List[Dict[str, Any]] = []
            else:
                new_msgs = [m for m in msgs if not _msg_in_range(m.get("timestamp"))]
            removed = len(msgs) - len(new_msgs)
            if removed > 0 or (start_dt is None and end_dt is None and len(msgs) > 0):
                calls().update_one({"user_id": d["user_id"], "workflow_id": d["workflow_id"], "call_id": d["call_id"]}, {"$set": {"messages": new_msgs, "updated_at": now}})
                total_modified += 1
                total_removed += removed
        return {"matched_calls": total_matched, "modified_calls": total_modified, "removed_messages": total_removed}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting call conversation")
        raise HTTPException(status_code=500, detail=str(e))
