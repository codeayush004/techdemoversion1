import secrets
import string
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/agent", tags=["agent"])

# Simple in-memory storage for agent sessions
# In production, use Redis!
AGENT_SESSIONS: Dict[str, Dict[str, Any]] = {}

class AgentSyncPayload(BaseModel):
    user_id: Optional[str] = None
    containers: Any
    system_info: Optional[Dict[str, Any]] = None

@router.get("/session")
async def create_session():
    """Generates a unique 6-character sync code for the agent."""
    sync_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    AGENT_SESSIONS[sync_code] = {
        "status": "waiting",
        "data": None
    }
    return {"sync_code": sync_code}

@router.post("/sync/{sync_code}")
async def sync_agent_data(sync_code: str, payload: AgentSyncPayload):
    """Endpoint for the local agent to push container metadata."""
    if sync_code not in AGENT_SESSIONS:
        raise HTTPException(status_code=404, detail="Invalid sync code or session expired")
    
    AGENT_SESSIONS[sync_code] = {
        "status": "completed",
        "data": payload.dict()
    }
    return {"status": "success", "message": "Data synchronized successfully"}

@router.get("/status/{sync_code}")
async def check_session_status(sync_code: str):
    """Endpoint for the React frontend to poll for incoming data."""
    if sync_code not in AGENT_SESSIONS:
        raise HTTPException(status_code=404, detail="Invalid sync code")
    
    session = AGENT_SESSIONS[sync_code]
    return session
