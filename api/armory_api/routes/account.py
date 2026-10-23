"""Das Konto (immer „Gilde“, siehe deps.py)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..deps import CurrentUser

router = APIRouter(prefix="/api/me", tags=["konto"])


class Me(BaseModel):
    # Felder wie in der Oberfläche erwartet (Me in web/src/lib/api.ts)
    discord_id: str
    name: str
    avatar_url: str | None
    role: str


@router.get("")
async def me(user: CurrentUser) -> Me:
    return Me(discord_id="0", name=user.name, avatar_url=None, role=user.role)
