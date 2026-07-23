from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(BigInteger, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    patronymic = Column(String(100))
    birth_date = Column(Date, nullable=False)
    snils = Column(String(14), unique=True, nullable=False, index=True)
    policy_number = Column(String(20), unique=True, nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    max_chat_id = Column(String(100), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
