from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.appointment import Appointment, AppointmentSource
from app.models.schedule import ScheduleSlot, SlotStatus
from app.schemas.appointment import AppointmentCreate
from datetime import datetime

class AppointmentService:
    @staticmethod
    async def create_appointment(
        db: AsyncSession, 
        data: AppointmentCreate, 
        created_by: int,
        slot: ScheduleSlot
    ) -> Appointment:
        # Резервируем слот
        slot.status = SlotStatus.BOOKED
        slot.patient_id = data.patient_id
        
        # Создаём запись
        appointment = Appointment(
            patient_id=data.patient_id,
            doctor_id=slot.doctor_id,
            slot_id=slot.id,
            source=data.source or AppointmentSource.WEB,
            notes=data.notes,
            created_by=created_by
        )
        
        db.add(appointment)
        await db.commit()
        await db.refresh(appointment)
        return appointment
    
    @staticmethod
    async def get_patient_appointments(db: AsyncSession, patient_id: int) -> list[Appointment]:
        result = await db.execute(
            select(Appointment)
            .where(Appointment.patient_id == patient_id, Appointment.canceled_at.is_(None))
            .order_by(Appointment.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def cancel_appointment(db: AsyncSession, appointment_id: int, reason: str):
        appointment = await db.get(Appointment, appointment_id)
        if not appointment:
            return None
        
        # Освобождаем слот
        await db.execute(
            update(ScheduleSlot)
            .where(ScheduleSlot.id == appointment.slot_id)
            .values(status=SlotStatus.FREE, patient_id=None)
        )
        
        appointment.canceled_at = datetime.now()
        appointment.cancel_reason = reason
        await db.commit()
        return appointment
