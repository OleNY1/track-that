from fastapi import FastAPI
from database import engine
import models

from routers.applications import router as applications_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(applications_router)