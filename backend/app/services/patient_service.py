from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate
from datetime import datetime

class PatientService:
    @staticmethod
    async def create_patient(db: AsyncSession, data: PatientCreate) -> Patient:
        patient = Patient(**data.dict())
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
        return patient
    
    @staticmethod
    async def get_patient(db: AsyncSession, patient_id: int) -> Patient | None:
        return await db.get(Patient, patient_id)
    
    @staticmethod
    async def get_by_chat_id(db: AsyncSession, chat_id: str) -> Patient | None:
        result = await db.execute(
            select(Patient).where(Patient.max_chat_id == chat_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_patient(db: AsyncSession, patient_id: int, data: PatientUpdate) -> Patient | None:
        patient = await db.get(Patient, patient_id)
        if not patient:
            return None
        
        for key, value in data.dict(exclude_unset=True).items():
            setattr(patient, key, value)
        
        await db.commit()
        await db.refresh(patient)
        return patient
    
    @staticmethod
    async def soft_delete_patient(db: AsyncSession, patient_id: int) -> Patient | None:
        patient = await db.get(Patient, patient_id)
        if not patient:
            return None
        
        patient.is_active = False
        await db.commit()
        return patient
