from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import boto3
from botocore.client import Config
from dotenv import load_dotenv
import os
import tempfile
import shutil
from typing import Optional

load_dotenv()

# Environment-based configuration (do NOT hardcode secrets)
AWS_S3_ENDPOINT = os.getenv("AWS_S3_ENDPOINT")
AWS_S3_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY_ID")
AWS_S3_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_ACCESS_KEY")
AWS_S3_REGION = os.getenv("AWS_S3_REGION", "us-east-1")
AWS_S3_FORCE_PATH_STYLE = os.getenv("AWS_S3_FORCE_PATH_STYLE", "true").lower() in ("1", "true", "yes")

call_recording_router = APIRouter()

class DownloadRequest(BaseModel):
    bucket: Optional[str] = "recording"
    object_key: str
    filename: Optional[str] = None


def _get_s3_client():
    if not (AWS_S3_ENDPOINT and AWS_S3_ACCESS_KEY_ID and AWS_S3_SECRET_ACCESS_KEY):
        raise RuntimeError("S3 configuration missing. Ensure AWS_S3_* env vars are set.")

    s3_config = {}
    if AWS_S3_FORCE_PATH_STYLE:
        s3_config = {"s3": {"addressing_style": "path"}}

    return boto3.client(
        "s3",
        endpoint_url=AWS_S3_ENDPOINT,
        aws_access_key_id=AWS_S3_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION,
        config=Config(**s3_config) if s3_config else Config(),
    )


def _cleanup_tmp(file_path: str, dir_path: str):
    """Safely remove the downloaded file and its temporary directory."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        # Ignore cleanup errors
        pass
    finally:
        try:
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path, ignore_errors=True)
        except Exception:
            pass


@call_recording_router.post(
    "/download-call-recording",
    response_class=FileResponse,
    summary="Download a call recording from S3/MinIO",
    description="Downloads a call recording object by bucket and key, returning the file.",
)
def download_recording(payload: DownloadRequest, background_tasks: BackgroundTasks):
    tmp_dir = None
    try:
        s3 = _get_s3_client()

        # Use provided filename or derive from object key
        filename = payload.filename or os.path.basename(payload.object_key) or "recording.bin"

        # Save to a secure temp directory
        tmp_dir = tempfile.mkdtemp(prefix="recording-")
        local_path = os.path.join(tmp_dir, filename)

        s3.download_file(payload.bucket, payload.object_key, local_path)

        # Schedule cleanup after response is sent
        background_tasks.add_task(_cleanup_tmp, local_path, tmp_dir)

        # Return the file as a response for client download and attach cleanup
        return FileResponse(
            local_path,
            filename=filename,
            media_type="application/octet-stream",
            background=background_tasks,
        )
    except Exception as e:
        # Best-effort cleanup on error
        if tmp_dir and os.path.isdir(tmp_dir):
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to download: {str(e)}")
