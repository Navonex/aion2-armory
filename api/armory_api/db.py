"""Datenbankverbindung. Die Tabellen legt der Start selbst an (keine Migrationen nötig)."""
from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from .models import Base, User

GILDE = "Gilde"


def aware(when: datetime) -> datetime:
    """SQLite gibt Zeitpunkte ohne Zeitzone zurück; gespeichert wird immer UTC."""
    return when if when.tzinfo else when.replace(tzinfo=UTC)


async def prepare(engine: AsyncEngine, sessionmaker: async_sessionmaker) -> int:
    """Tabellen anlegen und das eine Konto „Gilde“ sicherstellen; gibt dessen ID zurück."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with sessionmaker() as db:
        user = await db.scalar(select(User).where(User.username == GILDE))
        if user is None:
            user = User(username=GILDE, role="admin")
            db.add(user)
            await db.commit()
        return user.id


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessionmaker() as db:
        yield db
