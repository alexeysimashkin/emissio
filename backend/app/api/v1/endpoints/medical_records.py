from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.medical_record import MedicalRecord
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordResponse
from app.services.medical_record_service import MedicalRecordService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/medical-records", tags=["medical-records"])

@router.post("/", response_model=MedicalRecordResponse)
async def create_medical_record(
    record_data: MedicalRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "registrar"))
):
    """Создать запись в медкарте (врач, регистратор или админ)"""
    record = await MedicalRecordService.create_record(db, record_data, current_user.id)
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "CREATE", "medical_record", record.id, {"diagnosis": record_data.diagnosis})
    return record

@router.get("/patient/{patient_id}", response_model=list[MedicalRecordResponse])
async def get_patient_records(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "registrar"))
):
    """Получить все записи медкарты пациента"""
    records = await MedicalRecordService.get_patient_records(db, patient_id)
    return records

@router.put("/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record(
    record_id: int,
    record_data: MedicalRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "registrar"))
):
    """Обновить запись в медкарте"""
    record = await MedicalRecordService.update_record(db, record_id, record_data)
    if not record:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "UPDATE", "medical_record", record_id, {"changes": record_data.dict()})
    return record
