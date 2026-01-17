from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import SessionLocal

router = APIRouter(prefix="/applications", tags=["applications"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=list[schemas.Application])
def list_applications(
    status: Optional[str] = None,
    company: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Application)

    if status:
        query = query.filter(models.Application.status == status)
    if company:
        query = query.filter(models.Application.company == company)

    return query.all()

@router.get("/{app_id}", response_model=schemas.Application)
def get_application(app_id: int, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_obj

@router.post("", response_model=schemas.Application, status_code=201)
def create_application(payload: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    new_app = models.Application(**payload.model_dump())
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app

@router.put("/{app_id}", response_model=schemas.Application)
def update_application(app_id: int, payload: schemas.ApplicationUpdate, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(app_obj, key, value)

    db.commit()
    db.refresh(app_obj)
    return app_obj

@router.delete("/{app_id}", status_code=204)
def delete_application(app_id: int, db: Session = Depends(get_db)):
    app_obj = db.query(models.Application).filter(models.Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(app_obj)
    db.commit()
    return
