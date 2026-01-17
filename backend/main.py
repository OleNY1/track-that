from fastapi import FastAPI, Depends, HTTPException
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

@app.put("/applications/{app_id}", response_model=schemas.Application)
def update_application(
    app_id: int,
    payload: schemas.ApplicationUpdate,
    db: Session = Depends(get_db)
):
    app_obj = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(app_obj, key, value)

    db.commit()
    db.refresh(app_obj)
    return app_obj

@app.delete("/applications/{app_id}", status_code=204)
def delete_application(app_id: int, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(app_obj)
    db.commit()
    return

