from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.services.max_service import MAXService
from app.services.appointment_service import AppointmentService
from app.services.patient_service import PatientService
from app.core.database import AsyncSessionLocal
import json

router = APIRouter(prefix="/webhook", tags=["max"])

@router.post("/max")
async def max_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook для MAX мессенджера"""
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Обработка события
    event_type = data.get("event")
    chat_id = data.get("chat_id")
    text = data.get("text", "").lower()
    
    if not chat_id:
        return {"status": "ok"}
    
    if event_type == "message":
        # Обработка в фоновом режиме
        background_tasks.add_task(handle_max_message, chat_id, text)
    
    return {"status": "ok"}

async def handle_max_message(chat_id: str, text: str):
    """Обработка сообщения от пациента в MAX"""
    async with AsyncSessionLocal() as db:
        # Ищем пациента по chat_id
        patient = await PatientService.get_by_chat_id(db, chat_id)
        
        if text == "/start":
            await MAXService.send_message(
                chat_id,
                "👋 Добро пожаловать в ЕМИССиО!\n"
                "Отправьте:\n"
                "- 'врачи' - список врачей\n"
                "- 'запись к [имя врача]' - записаться\n"
                "- 'мои записи' - посмотреть записи"
            )
            return
        
        if text == "врачи":
            doctors = await MAXService.get_doctors_list(db)
            await MAXService.send_message(chat_id, "👨‍⚕️ Доступные врачи:\n" + "\n".join(doctors))
            return
        
        if text.startswith("запись к"):
            doctor_name = text.replace("запись к", "").strip()
            slots = await MAXService.get_free_slots(db, doctor_name)
            if slots:
                await MAXService.send_message(
                    chat_id,
                    f"📅 Свободные слоты у {doctor_name}:\n" + "\n".join(slots)
                )
            else:
                await MAXService.send_message(chat_id, "❌ Нет свободных слотов")
            return
        
        if text == "мои записи":
            if not patient:
                await MAXService.send_message(chat_id, "❌ Пациент не найден. Свяжитесь с регистратурой.")
                return
            
            appointments = await AppointmentService.get_patient_appointments(db, patient.id)
            if appointments:
                msg = "📋 Ваши записи:\n" + "\n".join([
                    f"🏥 {app.doctor.full_name} - {app.slot.date} {app.slot.start_time}"
                    for app in appointments
                ])
                await MAXService.send_message(chat_id, msg)
            else:
                await MAXService.send_message(chat_id, "📭 У вас нет активных записей")
            return
        
        await MAXService.send_message(
            chat_id,
            "❌ Неизвестная команда. Отправьте /start для справки."
        )
