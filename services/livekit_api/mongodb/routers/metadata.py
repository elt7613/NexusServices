import logging
from typing import Any, Dict, List, Optional, Literal
from fastapi import APIRouter, HTTPException, Query

from ..db import users, workflows, calls
from ..utils import IST, now_ist_iso, parse_any_dt_to_ist, parse_bound_date_only
from ..models import AddMetadataRequest

logger = logging.getLogger(__name__)

metadata_router = APIRouter()


@metadata_router.post("/add-call-metadata", summary="Add/merge call metadata")
def add_metadata(req: AddMetadataRequest, mode: Literal["merge", "replace"] = Query("merge")):
    try:
        now = now_ist_iso()
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

        # Upsert call metadata
        if mode == "merge" and isinstance(req.metadata, dict):
            set_fields = {f"metadata.{k}": v for k, v in req.metadata.items()}
            update = {
                "$set": {**set_fields, "updated_at": now},
                "$setOnInsert": {
                    "user_id": req.user_id,
                    "workflow_id": req.workflow_id,
                    "call_id": req.call_id,
                    "messages": [],
                    "created_at": now,
                },
            }
        else:
            update = {
                "$set": {"metadata": req.metadata, "updated_at": now},
                "$setOnInsert": {
                    "user_id": req.user_id,
                    "workflow_id": req.workflow_id,
                    "call_id": req.call_id,
                    "messages": [],
                    "created_at": now,
                },
            }

        res = calls().update_one(
            {"user_id": req.user_id, "workflow_id": req.workflow_id, "call_id": req.call_id},
            update,
            upsert=True,
        )
        created = res.upserted_id is not None
        return {"user_id": req.user_id, "workflow_id": req.workflow_id, "call_id": req.call_id, "created": created}
    except Exception as e:
        logger.exception("Error adding metadata")
        raise HTTPException(status_code=500, detail=str(e))


@metadata_router.get("/get-call-metadata", summary="Fetch call metadata by user/workflow/call")
def get_metadata(
    user_id: str = Query(..., min_length=1),
    workflow_id: Optional[str] = Query(None, min_length=1),
    call_id: Optional[str] = Query(None, min_length=1),
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD, IST)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD, IST)"),
):
    try:
        q = {"user_id": user_id}
        if workflow_id:
            q["workflow_id"] = workflow_id
        if call_id:
            q["call_id"] = call_id

        projection = {"_id": 0, "user_id": 1, "workflow_id": 1, "call_id": 1, "metadata": 1, "created_at": 1, "updated_at": 1}

        # bounds
        start_dt = None
        end_dt = None
        if start:
            try:
                start_dt = parse_bound_date_only(start, as_end=False)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        if end:
            try:
                end_dt = parse_bound_date_only(end, as_end=True)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        def _in_range(doc: Dict[str, Any]) -> bool:
            base = doc.get("updated_at") or doc.get("created_at")
            dt = parse_any_dt_to_ist(base)
            if dt is None:
                return True
            if start_dt and dt < start_dt:
                return False
            if end_dt and dt > end_dt:
                return False
            return True

        if call_id:
            doc = calls().find_one(q, projection)
            if not doc:
                raise HTTPException(status_code=404, detail="Call not found")
            if not _in_range(doc):
                raise HTTPException(status_code=404, detail="No matching call in the given time range")
            return {
                "user_id": doc["user_id"],
                "workflow_id": doc["workflow_id"],
                "call_id": doc["call_id"],
                "metadata": doc.get("metadata"),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
            }
        elif workflow_id:
            docs = [d for d in calls().find(q, projection) if _in_range(d)]
            calls_list = [
                {
                    "call_id": d["call_id"],
                    "metadata": d.get("metadata"),
                    "created_at": d.get("created_at"),
                    "updated_at": d.get("updated_at"),
                }
                for d in docs
            ]
            return {"user_id": user_id, "workflow_id": workflow_id, "calls": calls_list}
        else:
            docs = [d for d in calls().find(q, projection) if _in_range(d)]
            workflows_map: Dict[str, List[Dict[str, Any]]] = {}
            for d in docs:
                wf = d["workflow_id"]
                workflows_map.setdefault(wf, []).append(
                    {
                        "call_id": d["call_id"],
                        "metadata": d.get("metadata"),
                        "created_at": d.get("created_at"),
                        "updated_at": d.get("updated_at"),
                    }
                )
            workflows_list = [{"workflow_id": wf, "calls": calls_} for wf, calls_ in workflows_map.items()]
            return {"user_id": user_id, "workflows": workflows_list}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching metadata")
        raise HTTPException(status_code=500, detail=str(e))


@metadata_router.get("/get-latest-call-metadata", summary="Latest call metadata for a workflow")
def get_latest_call_metadata(
    user_id: str = Query(..., min_length=1),
    workflow_id: str = Query(..., min_length=1),
):
    try:
        projection = {"_id": 0, "user_id": 1, "workflow_id": 1, "call_id": 1, "metadata": 1, "created_at": 1, "updated_at": 1}
        cursor = (
            calls()
            .find({"user_id": user_id, "workflow_id": workflow_id}, projection)
            .sort([("updated_at", -1), ("created_at", -1)])
            .limit(1)
        )
        doc = next(cursor, None)
        if not doc:
            raise HTTPException(status_code=404, detail="No calls found for workflow")
        return {
            "user_id": doc["user_id"],
            "workflow_id": doc["workflow_id"],
            "call_id": doc["call_id"],
            "metadata": doc.get("metadata"),
            "created_at": doc.get("created_at"),
            "updated_at": doc.get("updated_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching latest call metadata")
        raise HTTPException(status_code=500, detail=str(e))


@metadata_router.delete("/delete-call-metadata", summary="Delete call metadata by user/workflow/call with optional date range (IST)")
def delete_call_metadata(
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

        projection = {"_id": 0, "user_id": 1, "workflow_id": 1, "call_id": 1, "created_at": 1, "updated_at": 1}

        try:
            start_dt = parse_bound_date_only(start, as_end=False) if start else None
            end_dt = parse_bound_date_only(end, as_end=True) if end else None
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        def _in_range(doc: Dict[str, Any]) -> bool:
            base = doc.get("updated_at") or doc.get("created_at")
            dt = parse_any_dt_to_ist(base)
            if dt is None:
                return True
            if start_dt and dt < start_dt:
                return False
            if end_dt and dt > end_dt:
                return False
            return True

        docs = [d for d in calls().find(base_q, projection) if _in_range(d)]
        if call_id and not docs:
            raise HTTPException(status_code=404, detail="No matching call in the given time range")
        if not docs:
            return {"matched_calls": 0, "modified_calls": 0}

        ids = [d["call_id"] for d in docs]
        now = now_ist_iso()
        upd_q = {"user_id": user_id, "call_id": {"$in": ids}}
        if workflow_id:
            upd_q["workflow_id"] = workflow_id
        res = calls().update_many(upd_q, {"$unset": {"metadata": ""}, "$set": {"updated_at": now}})
        return {"matched_calls": res.matched_count, "modified_calls": res.modified_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting call metadata")
        raise HTTPException(status_code=500, detail=str(e))
