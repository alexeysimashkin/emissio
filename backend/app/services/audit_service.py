from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from datetime import datetime

class AuditService:
    @staticmethod
    async def log(
        db: AsyncSession,
        user_id: int,
        user_email: str,
        user_role: str,
        action: str,
        resource: str,
        resource_id: int,
        changes: dict
    ):
        log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            action=action,
            resource=resource,
            resource_id=resource_id,
            changes=changes,
            created_at=datetime.now()
        )
        db.add(log)
        await db.commit()
