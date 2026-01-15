from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

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

applications_db: List[Application] = []
next_id = 1

@app.get("/applications", response_model=List[Application])
def list_applications():
    return applications_db

@app.post("/applications", response_model=Application, status_code=201)
def create_application(payload: ApplicationCreate):
    global next_id
    new_app = Application(id=next_id, **payload.model_dump())
    next_id += 1
    applications_db.append(new_app)
    return new_app


