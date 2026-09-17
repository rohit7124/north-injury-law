"""
Request/response models for the lead-capture API.

Validation here is the server-side backstop behind the client-side checks
in script.js. Never trust the client: this is what actually protects the
database and keeps bad data out.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

ALLOWED_ACCIDENT_TYPES = {
    "car",
    "truck",
    "motorcycle",
    "pedestrian",
    "slip-fall",
    "wrongful-death",
    "other",
}

ALLOWED_CONTACT_METHODS = {"phone", "email", "text"}

MAX_NAME_LEN = 100
MAX_PHONE_LEN = 30
MAX_DESCRIPTION_LEN = 2000
MAX_DATE_LEN = 20


class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    contact_method: Optional[str] = None
    accident_type: str
    accident_date: Optional[str] = None
    description: str
    consent: bool

    @field_validator("first_name", "last_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("This field cannot be blank.")
        if len(v) > MAX_NAME_LEN:
            raise ValueError(f"This field must be {MAX_NAME_LEN} characters or fewer.")
        return v

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v: str) -> str:
        v = (v or "").strip()
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) < 10:
            raise ValueError("Enter a valid phone number.")
        if len(v) > MAX_PHONE_LEN:
            raise ValueError("Phone number is too long.")
        return v

    @field_validator("contact_method")
    @classmethod
    def contact_method_valid(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        v = v.strip().lower()
        if v not in ALLOWED_CONTACT_METHODS:
            raise ValueError("Select a valid contact method.")
        return v

    @field_validator("accident_type")
    @classmethod
    def accident_type_valid(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in ALLOWED_ACCIDENT_TYPES:
            raise ValueError("Select a valid accident type.")
        return v

    @field_validator("accident_date")
    @classmethod
    def accident_date_valid(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        v = v.strip()
        if len(v) > MAX_DATE_LEN:
            raise ValueError("Invalid date.")
        # Basic ISO (YYYY-MM-DD) shape check; the <input type="date"> element
        # already constrains this on the client, this is just a backstop.
        parts = v.split("-")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("Date must be in YYYY-MM-DD format.")
        return v

    @field_validator("description")
    @classmethod
    def description_valid(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("Please tell us briefly what happened.")
        if len(v) > MAX_DESCRIPTION_LEN:
            raise ValueError(f"Description must be {MAX_DESCRIPTION_LEN} characters or fewer.")
        return v

    @field_validator("consent")
    @classmethod
    def consent_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Consent is required to submit this form.")
        return v
