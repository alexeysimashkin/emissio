from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.procedure import ProcedureQueue, ProcedureStatus
from app.schemas.procedure import ProcedureCreate, ProcedureResponse
from app.services.procedure_service import ProcedureService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/procedures", tags=["procedures"])

@router.post("/queue", response_model=ProcedureResponse)
async def add_to_queue(
    procedure_data: ProcedureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "doctor", "nurse"))
):
    """Добавить пациента в очередь процедур"""
    procedure = await ProcedureService.add_to_queue(db, procedure_data, current_user.id)
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "CREATE", "procedure_queue", procedure.id, procedure_data.dict())
    return procedure

@router.get("/queue/nurse/{nurse_id}")
async def get_nurse_queue(
    nurse_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "procedure_nurse", "nurse"))
):
    """Получить очередь процедур для конкретной медсестры"""
    queue = await ProcedureService.get_nurse_queue(db, nurse_id)
    return queue

@router.put("/queue/{queue_id}/complete")
async def complete_procedure(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "procedure_nurse"))
):
    """Отметить процедуру как выполненную"""
    procedure = await db.get(ProcedureQueue, queue_id)
    if not procedure:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    
    if procedure.nurse_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    procedure.status = ProcedureStatus.DONE
    procedure.completed_at = datetime.now()
    await db.commit()
    
    await AuditService.log(db, current_user.id, current_user.email, current_user.role,
                          "UPDATE", "procedure_queue", queue_id, {"status": "completed"})
    return {"status": "completed", "queue_id": queue_id}
