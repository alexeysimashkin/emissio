from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Enum, DateTime, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class SlotStatus(str, enum.Enum):
    FREE = "свободно"
    BOOKED = "занято"
    CANCELED = "отменено"

class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    duration = Column(Integer, nullable=False)  # 10,15,20,30
    status = Column(Enum(SlotStatus), default=SlotStatus.FREE)
    patient_id = Column(BigInteger, ForeignKey("patients.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ScheduleBlock(Base):
    __tablename__ = "schedule_blocks"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    reason = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
