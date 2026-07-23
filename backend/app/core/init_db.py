from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.core.config import settings

async def init_admin():
    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        if not existing.scalar_one_or_none():
            admin = User(
                email=settings.ADMIN_EMAIL,
                full_name=settings.ADMIN_FULL_NAME,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            await db.commit()
            print(f"✅ Админ создан: {settings.ADMIN_EMAIL}")
