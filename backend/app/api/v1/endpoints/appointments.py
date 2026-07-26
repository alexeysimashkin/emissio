from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.schedule import ScheduleSlot, SlotStatus
from app.models.appointment import Appointment, AppointmentSource
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.services.max_service import MAXService

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar", "doctor"))
):
    """Создать запись на приём (врач может записать любого пациента)"""
    # Проверяем слот
    slot = await db.get(ScheduleSlot, appointment_data.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Слот не найден")
    
    # Врач может записать только к себе
    if current_user.role == "doctor" and slot.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы можете записывать только к себе")
    
    # Проверяем статус слота
    if slot.status != SlotStatus.FREE:
        raise HTTPException(status_code=409, detail="Слот уже занят")
    
    # Проверяем блокировку дня
    from app.models.schedule import ScheduleBlock
    block = await db.execute(
        select(ScheduleBlock).where(
            ScheduleBlock.doctor_id == slot.doctor_id,
            ScheduleBlock.date == slot.date
        )
    )
    if block.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Этот день заблокирован для записи")
    
    # Создаём запись
    appointment = await AppointmentService.create_appointment(
        db, appointment_data, current_user.id, slot
    )
    
    # Отправляем уведомление в MAX
    patient = await db.get(Patient, appointment_data.patient_id)
    if patient and patient.max_chat_id:
        await MAXService.send_notification(
            patient.max_chat_id,
            f"✅ Вы записаны к врачу {slot.doctor.full_name} на {slot.date} в {slot.start_time}"
        )
    
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "CREATE", "appointment", appointment.id, appointment_data.dict())
    return appointment

@router.delete("/{appointment_id}")
async def cancel_appointment(
    appointment_id: int,
    reason: str = "Отмена по инициативе пациента",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar", "doctor"))
):
    """Отменить запись"""
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    # Проверка прав
    if current_user.role == "doctor" and appointment.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы можете отменять только свои записи")
    
    # Освобождаем слот
    await db.execute(
        update(ScheduleSlot)
        .where(ScheduleSlot.id == appointment.slot_id)
        .values(status=SlotStatus.FREE, patient_id=None)
    )
    
    appointment.canceled_at = datetime.now()
    appointment.cancel_reason = reason
    await db.commit()
    
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "DELETE", "appointment", appointment_id, {"reason": reason})
    return {"status": "canceled", "appointment_id": appointment_id}
