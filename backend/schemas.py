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
