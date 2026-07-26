from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, date, time
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.schedule import ScheduleSlot, ScheduleBlock, SlotStatus
from app.schemas.schedule import SlotCreate, SlotBlockCreate, SlotResponse
from app.services.schedule_service import ScheduleService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/schedule", tags=["schedule"])

@router.post("/slots")
async def create_slots(
    slots_data: list[SlotCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    """Создать слоты расписания (только админ)"""
    created_slots = []
    for slot_data in slots_data:
        # Проверка на конфликты
        existing = await db.execute(
            select(ScheduleSlot).where(
                ScheduleSlot.doctor_id == slot_data.doctor_id,
                ScheduleSlot.date == slot_data.date,
                ScheduleSlot.start_time == slot_data.start_time
            )
        )
        if existing.scalar_one_or_none():
            continue  # Пропускаем существующий слот
        
        new_slot = ScheduleSlot(
            doctor_id=slot_data.doctor_id,
            date=slot_data.date,
            start_time=slot_data.start_time,
            duration=slot_data.duration,
            status=SlotStatus.FREE,
            created_by=current_user.id
        )
        db.add(new_slot)
        created_slots.append(new_slot)
    
    await db.commit()
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "CREATE", "schedule_slots", 0, {"count": len(created_slots)})
    return {"created": len(created_slots), "slots": created_slots}

@router.post("/blocks")
async def block_schedule(
    block_data: SlotBlockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar"))
):
    """Заблокировать день для врача (админ или регистратор)"""
    if block_data.date < datetime.now().date():
        raise HTTPException(status_code=400, detail="Нельзя блокировать прошедшие дни")
    
    # Создаём блокировку
    new_block = ScheduleBlock(
        doctor_id=block_data.doctor_id,
        date=block_data.date,
        reason=block_data.reason,
        created_by=current_user.id
    )
    db.add(new_block)
    await db.commit()
    
    # Отменяем все занятые слоты на этот день
    await db.execute(
        update(ScheduleSlot)
        .where(
            ScheduleSlot.doctor_id == block_data.doctor_id,
            ScheduleSlot.date == block_data.date,
            ScheduleSlot.status == SlotStatus.BOOKED
        )
        .values(status=SlotStatus.CANCELED)
    )
    await db.commit()
    
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "CREATE", "schedule_block", new_block.id, {"date": str(block_data.date)})
    return {"status": "blocked", "date": str(block_data.date), "doctor_id": block_data.doctor_id}

@router.get("/doctors/{doctor_id}/slots")
async def get_doctor_slots(
    doctor_id: int,
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar", "doctor"))
):
    """Получить расписание врача за период"""
    slots = await ScheduleService.get_doctor_slots(db, doctor_id, date_from, date_to)
    return slots

@router.delete("/blocks/{block_id}")
async def remove_block(
    block_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar"))
):
    """Удалить блокировку (админ или регистратор)"""
    block = await db.get(ScheduleBlock, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Блокировка не найдена")
    
    await db.delete(block)
    await db.commit()
    
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "DELETE", "schedule_block", block_id, {})
    return {"status": "removed", "block_id": block_id}
