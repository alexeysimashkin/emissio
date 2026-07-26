from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.services.patient_service import PatientService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/patients", tags=["patients"])

@router.get("/", response_model=list[PatientResponse])
async def get_patients(
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar", "doctor", "nurse"))
):
    """Получить список пациентов с поиском по ФИО или СНИЛС"""
    query = select(Patient).where(Patient.is_active == True)
    
    if search:
        query = query.where(
            or_(
                Patient.last_name.ilike(f"%{search}%"),
                Patient.first_name.ilike(f"%{search}%"),
                Patient.snils == search
            )
        )
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar", "doctor", "nurse"))
):
    patient = await PatientService.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")
    return patient

@router.post("/", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar"))
):
    """Создать пациента (регистратор или админ)"""
    # Проверка на дубликаты
    existing = await db.execute(
        select(Patient).where(
            or_(Patient.snils == patient_data.snils, Patient.policy_number == patient_data.policy_number)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Пациент с таким СНИЛС или полисом уже существует")
    
    patient = await PatientService.create_patient(db, patient_data)
    await AuditService.log(db, current_user.id, current_user.email, current_user.role, 
                          "CREATE", "patient", patient.id, {"data": patient_data.dict()})
    return patient

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar", "doctor"))
):
    patient = await PatientService.update_patient(db, patient_id, patient_data)
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")
    
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "UPDATE", "patient", patient_id, {"changes": patient_data.dict()})
    return patient

@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "registrar"))
):
    """Мягкое удаление пациента (только админ или регистратор)"""
    patient = await PatientService.soft_delete_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")
    
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "DELETE", "patient", patient_id, {"reason": "deleted"})
    return {"status": "deleted", "patient_id": patient_id}
