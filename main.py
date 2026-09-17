"""
Northstar Injury Law — lead-capture API.

MVP scope on purpose: FastAPI + SQLite, no auth framework, no ORM, no
task queue. See README.md for what would need to change before this
handles real client data.
"""

import logging
import os
from typing import Optional
from pydantic import BaseModel

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from database import init_db, insert_lead, list_leads, update_lead_status, update_lead_notes
from models import LeadCreate
from notifications import send_lead_notification

load_dotenv()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("northstar.api")

app = FastAPI(title="Northstar Injury Law — Lead API", version="1.0.0")

_default_origins = "http://localhost:8000,http://127.0.0.1:8000"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("Database ready. Allowed CORS origins: %s", allowed_origins)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/leads")
def create_lead(payload: LeadCreate) -> dict:
    lead = payload.model_dump()

    try:
        lead_id = insert_lead(lead)
    except Exception:
        # Do not log the lead's personal details on failure — only that
        # a failure happened.
        logger.exception("Failed to store a new lead.")
        raise HTTPException(
            status_code=500,
            detail="We couldn't save your request. Please try again or call us directly.",
        )

    # A failed or unconfigured notification never fails the submission —
    # the lead is already safely stored above.
    send_lead_notification(lead, lead_id)

    logger.info("Stored new lead (id=%s).", lead_id)
    return {
        "success": True,
        "message": "Thank you. Your request has been received.",
        "lead_id": lead_id,
    }


@app.get("/api/leads")
def get_leads(x_api_key: Optional[str] = Security(api_key_header)) -> dict:
    """Minimal internal endpoint so the firm can actually see stored leads.

    Disabled unless ADMIN_API_KEY is set. This is a shared-secret header,
    not a real auth system — see README.md for what to use instead before
    handling real client data.
    """
    admin_key = os.getenv("ADMIN_API_KEY")
    if not admin_key:
        raise HTTPException(status_code=503, detail="Admin access is not configured.")
    if x_api_key != admin_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return {"leads": list_leads()}
class LeadStatusUpdate(BaseModel):
    status: str


@app.patch("/api/leads/{lead_id}/status")
def update_status(
    lead_id: int,
    payload: LeadStatusUpdate,
    x_api_key: Optional[str] = Security(api_key_header),
) -> dict:
    admin_key = os.getenv("ADMIN_API_KEY")

    if not admin_key:
        raise HTTPException(
            status_code=503,
            detail="Admin access is not configured.",
        )

    if x_api_key != admin_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )

    allowed_statuses = {
        "new",
        "contacted",
        "qualified",
        "retained",
        "closed",
        "lost",
    }

    if payload.status not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail="Invalid lead status.",
        )

    updated = update_lead_status(lead_id, payload.status)

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    current_leads = list_leads(limit=200)

    current_lead = next(
        (
            lead
            for lead in current_leads
            if int(lead["id"]) == int(lead_id)
        ),
        None,
    )

    return {
        "success": True,
        "lead_id": lead_id,
        "status": payload.status,
        "contacted_at": (current_lead or {}).get("contacted_at"),
    }
class LeadNotesUpdate(BaseModel):
    notes: str


@app.patch("/api/leads/{lead_id}/notes")
def update_notes(
    lead_id: int,
    payload: LeadNotesUpdate,
    x_api_key: Optional[str] = Security(api_key_header),
) -> dict:
    admin_key = os.getenv("ADMIN_API_KEY")

    if not admin_key:
        raise HTTPException(
            status_code=503,
            detail="Admin access is not configured.",
        )

    if x_api_key != admin_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )

    notes = payload.notes.strip()

    if len(notes) > 5000:
        raise HTTPException(
            status_code=422,
            detail="Notes must be 5000 characters or fewer.",
        )

    updated = update_lead_notes(lead_id, notes)

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Lead not found.",
        )

    return {
        "success": True,
        "lead_id": lead_id,
        "notes": notes,
    }