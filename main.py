"""
Face Liveness & Deepfake Detection — FastAPI Backend
Uses AWS Rekognition FaceLiveness to verify a real human face.
"""

import os
import uuid
import logging
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── AWS client ────────────────────────────────────────────────────────────────
def get_rekognition_client():
    return boto3.client(
        "rekognition",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Face Liveness & Deepfake Detection API",
    description="Detect face liveness using AWS Rekognition FaceLiveness",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Pydantic models ───────────────────────────────────────────────────────────
class SessionResponse(BaseModel):
    session_id: str


class LivenessResult(BaseModel):
    session_id: str
    status: str                  # SUCCEEDED | FAILED | EXPIRED | IN_PROGRESS
    confidence: float            # 0.0 – 100.0
    is_live: bool                # True if confidence >= threshold
    is_deepfake: bool            # True if detected as deepfake / not live
    audit_images_count: int = 0


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


@app.post("/api/create-session", response_model=SessionResponse)
async def create_liveness_session():
    """
    Create a new FaceLiveness session with AWS Rekognition.
    Returns a session_id that the frontend uses to start the liveness check.
    """
    client = get_rekognition_client()
    client_request_token = str(uuid.uuid4())

    try:
        response = client.create_face_liveness_session(
            ClientRequestToken=client_request_token,
        )
        session_id = response["SessionId"]
        logger.info("Created liveness session: %s", session_id)
        return SessionResponse(session_id=session_id)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error("AWS error creating session: %s", error_code)
        raise HTTPException(status_code=500, detail=f"AWS error: {error_code}")
  

@app.get("/api/get-result/{session_id}", response_model=LivenessResult)
async def get_liveness_result(session_id: str):
    """
    Fetch the FaceLiveness result for a given session.
    Interprets confidence score and flags deepfake/spoof attempts.
    """
    client = get_rekognition_client()
    LIVENESS_THRESHOLD = float(os.getenv("LIVENESS_THRESHOLD", "90.0"))

    try:
        response = client.get_face_liveness_session_results(SessionId=session_id)
        logger.info("Got result for session %s: %s", session_id, response)

        status     = response.get("Status", "UNKNOWN")
        confidence = response.get("Confidence", 0.0)
        is_live    = status == "SUCCEEDED" and confidence >= LIVENESS_THRESHOLD
        is_deepfake = not is_live

        audit_images = response.get("AuditImages", [])

        return LivenessResult(
            session_id=session_id,
            status=status,
            confidence=round(confidence, 2),
            is_live=is_live,
            is_deepfake=is_deepfake,
            audit_images_count=len(audit_images),
        )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "SessionNotFoundException":
            raise HTTPException(status_code=404, detail="Session not found or expired")
        logger.error("AWS error fetching result: %s", error_code)
        raise HTTPException(status_code=500, detail=f"AWS error: {error_code}")


@app.get("/api/health")
async def health_check():
    """Quick health probe."""
    return {
        "status": "ok",
        "region": os.getenv("AWS_REGION", "us-east-1"),
        "threshold": float(os.getenv("LIVENESS_THRESHOLD", "90.0")),
    }
