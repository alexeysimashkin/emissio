from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class AppointmentSource(str, enum.Enum):
    WEB = "web"
    REGISTRY = "registry"
    MAX = "max"

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(BigInteger, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("schedule_slots.id"), nullable=False)
    source = Column(Enum(AppointmentSource), default=AppointmentSource.WEB)
    notes = Column(String(500))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    canceled_at = Column(DateTime(timezone=True), nullable=True)
