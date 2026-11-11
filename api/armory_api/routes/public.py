"""Öffentlicher Bereich: alles hier geht immer ohne Passwort.

Nur herausgeben, was geteilt werden darf:
    GET /api/public/info                          wer betreibt die Armory (Impressum)?
    GET /api/public/vergleich/{token}?lang=de     ein geteilter Vergleich (Teilen-Link /v/<token>)

Geteilte Vergleiche zeigen beide Charaktere, aber nicht, wer geteilt hat. Suchmaschinen sollen
sie nicht aufnehmen.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select

from ..deps import DB, SettingsDep
from ..models import Comparison
from .armory import ComparisonOut, load_comparison

router = APIRouter(prefix="/api/public", tags=["öffentlich"])


class Operator(BaseModel):
    name: str
    address: list[str]
    email: str | None


class Info(BaseModel):
    login: bool  # Login gibt es hier nicht (immer False), Feld für die Oberfläche
    operator: Operator | None  # Impressum, aus ARMORY_OPERATOR_* in .env
    hoster: str | None


@router.get("/info")
async def info(settings: SettingsDep) -> Info:
    return Info(login=False, operator=settings.operator, hoster=settings.armory_hoster.strip() or None)


def _not_for_search_engines(response: Response) -> None:
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Cache-Control"] = "no-store"


@router.get("/vergleich/{token}")
async def shared_comparison(token: str, request: Request, db: DB, response: Response,
                            lang: str = "en") -> ComparisonOut:
    row = await db.scalar(select(Comparison).where(Comparison.token == token)) if len(token) <= 32 else None
    if row is None:
        raise HTTPException(404, "Link ungültig oder zurückgezogen")
    _not_for_search_engines(response)
    return await load_comparison(request, db, row, lang)
