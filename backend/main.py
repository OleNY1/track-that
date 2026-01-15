from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import SessionLocal, engine
import models
import schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/applications", response_model=list[schemas.Application])
def list_applications(db: Session = Depends(get_db)):
    return db.query(models.Application).all()

@app.post("/applications", response_model=schemas.Application, status_code=201)
def create_application(
    payload: schemas.ApplicationCreate,
    db: Session = Depends(get_db)
):
    new_app = models.Application(**payload.model_dump())
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app
