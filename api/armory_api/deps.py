"""Bausteine für Routen: Einstellungen, Datenbank und das Konto.

Es gibt kein Login: alle Aufrufe laufen über das eine Konto „Gilde“ (db.prepare). Wer die Seite
öffnen darf, regelt höchstens das Passwort (ARMORY_PASSWORT, main.py).
    async def seite(user: CurrentUser, db: DB): ...
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings
from .db import get_db
from .models import User


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_settings)]
DB = Annotated[AsyncSession, Depends(get_db)]


async def current_user(request: Request, db: DB) -> User:
    user = await db.get(User, request.app.state.gilde_id)
    if user is None:
        raise HTTPException(500, "Konto Gilde fehlt")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
