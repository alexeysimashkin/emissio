import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.schedule import ScheduleSlot, SlotStatus
from datetime import datetime

class MAXService:
    @staticmethod
    async def send_message(chat_id: str, text: str):
        """Отправить сообщение через MAX"""
        url = f"{settings.MAX_API_URL}/messages"
        headers = {
            "Authorization": f"Bearer {settings.MAX_BOT_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json=payload, headers=headers)
        except Exception as e:
            print(f"MAX error: {e}")
    
    @staticmethod
    async def send_notification(chat_id: str, text: str):
        """Отправить уведомление (с приоритетом)"""
        await MAXService.send_message(chat_id, f"🔔 {text}")
    
    @staticmethod
    async def get_doctors_list(db: AsyncSession) -> list[str]:
        """Получить список врачей для бота"""
        doctors = await db.execute(
            select(User).where(User.role == UserRole.DOCTOR, User.is_active == True)
        )
        return [f"👨‍⚕️ {d.full_name} ({d.id})" for d in doctors.scalars().all()]
    
    @staticmethod
    async def get_free_slots(db: AsyncSession, doctor_name: str, days_ahead: int = 7) -> list[str]:
        """Получить свободные слоты для врача на ближайшие N дней"""
        from datetime import timedelta
        today = datetime.now().date()
        date_to = today + timedelta(days=days_ahead)
        
        slots = await db.execute(
            select(ScheduleSlot)
            .join(User, ScheduleSlot.doctor_id == User.id)
            .where(
                User.full_name.ilike(f"%{doctor_name}%"),
                ScheduleSlot.date >= today,
                ScheduleSlot.date <= date_to,
                ScheduleSlot.status == SlotStatus.FREE
            )
            .order_by(ScheduleSlot.date, ScheduleSlot.start_time)
            .limit(10)
        )
        
        return [
            f"📅 {slot.date} {slot.start_time.strftime('%H:%M')} - {slot.duration} мин"
            for slot in slots.scalars().all()
        ]
