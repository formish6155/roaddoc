from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, select, inspect, text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager
from src.config import settings

Base = declarative_base()


def _ensure_sqlite_columns(sync_conn):
    """Добавляет недостающие колонки в существующей SQLite БД."""
    if sync_conn.dialect.name != "sqlite":
        return

    inspector = inspect(sync_conn)
    table_names = set(inspector.get_table_names())

    if "reports" in table_names:
        report_columns = {column["name"] for column in inspector.get_columns("reports")}
        if "document_path" not in report_columns:
            sync_conn.execute(text("ALTER TABLE reports ADD COLUMN document_path VARCHAR(500)"))

    if "accident_reports" in table_names:
        accident_columns = {column["name"] for column in inspector.get_columns("accident_reports")}
        if "status" not in accident_columns:
            sync_conn.execute(text("ALTER TABLE accident_reports ADD COLUMN status VARCHAR(50) DEFAULT 'new'"))

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_admin = Column(Boolean, default=False)
    
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    accidents = relationship("AccidentReport", back_populates="user", cascade="all, delete-orphan")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    problem_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    photo_path = Column(String(500), nullable=True)
    document_path = Column(String(500), nullable=True)
    status = Column(String(50), default="new")  # new, in_progress, resolved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="reports")

class AccidentReport(Base):
    __tablename__ = "accident_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    participants = Column(Text, nullable=False)  # JSON string
    photo_paths = Column(Text, nullable=True)  # JSON array of paths
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    document_path = Column(String(500), nullable=True)
    status = Column(String(50), default="new")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="accidents")

# Асинхронный движок и сессия
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def create_db_and_tables():
    """Создание таблиц в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_sqlite_columns)
    
    # Безопасное добавление администраторов (только если не существует)
    async with get_db() as session:
        for admin_id in settings.ADMIN_IDS:
            # Проверяем по telegram_id, а не по первичному ключу
            result = await session.execute(
                select(User).where(User.telegram_id == admin_id)
            )
            existing_user = result.scalar_one_or_none()
        
            if not existing_user:
                new_admin = User(
                    telegram_id=admin_id,
                    username=f"admin_{admin_id}",
                    full_name="Администратор системы",
                    is_admin=True
                )
                session.add(new_admin)
                await session.commit()
                print(f"✅ Администратор {admin_id} добавлен в систему")
            else:
                # Обновляем флаг is_admin, если пользователь уже существует
                if not existing_user.is_admin:
                    existing_user.is_admin = True
                    await session.commit()
                    print(f"✅ Пользователь {admin_id} повышен до администратора")
    
    
    
