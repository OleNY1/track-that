
# This file defines the API input and output schemas, 
# validating client data and safely converting database objects into JSON responses.
from pydantic import BaseModel
from typing import Optional
from datetime import date

class ApplicationCreate(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    application_link: Optional[str] = None
    date_applied: Optional[date] = None
    status: str = "Applied"
    notes: Optional[str] = None

class Application(ApplicationCreate):
    id: int

    class Config:
        from_attributes = True

class ApplicationUpdate(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    application_link: Optional[str] = None
    date_applied: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None

