from sqlalchemy import Column, Integer, String, Date
from database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    location = Column(String, nullable=True)
    application_link = Column(String, nullable=True)
    date_applied = Column(Date, nullable=True)
    status = Column(String, default="Applied")
    notes = Column(String, nullable=True)
