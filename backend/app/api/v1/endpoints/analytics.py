from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.schedule import ScheduleSlot, SlotStatus
from app.models.appointment import Appointment
from app.models.patient import Patient
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard/admin")
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    """Дашборд для администратора"""
    today = datetime.now().date()
    
    # Количество записей на сегодня
    appointments_today = await db.execute(
        select(func.count()).select_from(Appointment)
        .join(ScheduleSlot)
        .where(ScheduleSlot.date == today)
    )
    
    # Свободные слоты на сегодня
    free_slots = await db.execute(
        select(func.count()).select_from(ScheduleSlot)
        .where(
            ScheduleSlot.date == today,
            ScheduleSlot.status == SlotStatus.FREE
        )
    )
    
    # Всего пациентов
    total_patients = await db.execute(select(func.count()).select_from(Patient))
    
    # Загруженность врачей
    doctors_load = await db.execute(
        select(
            User.full_name,
            func.count(ScheduleSlot.id).label('total'),
            func.sum(case((ScheduleSlot.status == SlotStatus.BOOKED, 1), else_=0)).label('booked')
        )
        .join(ScheduleSlot, User.id == ScheduleSlot.doctor_id)
        .where(ScheduleSlot.date == today)
        .group_by(User.id)
    )
    
    return {
        "today": {
            "appointments": appointments_today.scalar() or 0,
            "free_slots": free_slots.scalar() or 0,
            "total_patients": total_patients.scalar() or 0
        },
        "doctors_load": [
            {
                "doctor": row[0],
                "total": row[1],
                "booked": row[2],
                "load_percent": round(row[2] / row[1] * 100) if row[1] > 0 else 0
            }
            for row in doctors_load
        ]
    }
