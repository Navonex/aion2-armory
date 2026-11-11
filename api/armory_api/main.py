"""FastAPI-Anwendung: API unter /api, alles andere ist die statische Web-Oberfläche."""
from __future__ import annotations

import asyncio
import base64
import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .aion2 import NC
from .armory import Armory
from .bis_collector import BisCollector
from .census import Census
from .config import Settings
from .db import prepare
from .deps import DB
from .routes import ROUTERS

log = logging.getLogger(__name__)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
# Ohne Passwort erreichbar: geteilte Links samt den Dateien, die ihre Seiten brauchen
OFFEN = ("/api/public/", "/api/health", "/v/", "/_app/", "/impressum", "/datenschutz",
         "/favicon", "/robots.txt", "/klassen/")


def create_app(settings: Settings | None = None, http: httpx.AsyncClient | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.database_url.startswith("sqlite"):
            Path(settings.database_url.split("///", 1)[-1]).parent.mkdir(parents=True, exist_ok=True)
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        app.state.gilde_id = await prepare(engine, app.state.sessionmaker)
        app.state.http = http or httpx.AsyncClient(timeout=10)
        app.state.armory, tasks = None, []
        if settings.armory_aion2_enabled:
            nc = NC(app.state.http, settings.armory_aion2_pause)
            app.state.armory = Armory(app.state.sessionmaker, nc)
            census = Census(app.state.sessionmaker, app.state.http)
            collector = BisCollector(app.state.sessionmaker, nc, app.state.http)
            # der tägliche Armory-Abruf, der Sammler der BiS-Listen und die Zählung daraus; laufen neben dem Webserver
            tasks = [asyncio.create_task(app.state.armory.daily()),
                     asyncio.create_task(collector.run()),
                     asyncio.create_task(census.daily())]
        if not settings.armory_passwort:
            log.warning("ARMORY_PASSWORT ist leer – jeder mit der Adresse kann die Armory öffnen")
        yield
        for task in tasks:
            task.cancel()
        if http is None:
            await app.state.http.aclose()
        await engine.dispose()

    app = FastAPI(title="AION 2 Armory", version=settings.armory_version, lifespan=lifespan,
                  docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
    app.state.settings = settings
    for router in ROUTERS:
        app.include_router(router)

    @app.middleware("http")
    async def schutz(request: Request, call_next):
        """Passwort (HTTP-Basic, Benutzername egal) und Schutz vor fremden Seiten (CSRF)."""
        path = request.url.path
        if settings.armory_passwort and not path.startswith(OFFEN) and not _passwort_ok(request, settings):
            return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="AION 2 Armory"'})
        origin = request.headers.get("origin")
        if request.method not in SAFE_METHODS and origin and origin != settings.origin:
            return JSONResponse({"detail": "Fremde Herkunft"}, status_code=403)
        return await call_next(request)

    @app.get("/api/health", tags=["system"])
    async def health(db: DB) -> dict:
        await db.execute(text("SELECT 1"))
        return {"ok": True}

    if settings.armory_web_dir:
        _serve_web(app, settings.armory_web_dir.resolve())
    return app


def _passwort_ok(request: Request, settings: Settings) -> bool:
    kopf = request.headers.get("authorization", "")
    if not kopf.startswith("Basic "):
        return False
    try:
        _, _, passwort = base64.b64decode(kopf[6:]).decode().partition(":")
    except ValueError:
        return False
    return secrets.compare_digest(passwort.encode(), settings.armory_passwort.encode())


def _serve_web(app: FastAPI, web) -> None:
    """Gebaute Web-Oberfläche ausliefern; unbekannte Pfade bekommen die App-Hülle 200.html."""

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404)
        if path == "":
            return FileResponse(web / "200.html", headers={"Cache-Control": "no-cache"})
        file = (web / path).resolve()
        if file.is_file() and file.is_relative_to(web):
            # Dateien unter _app/immutable tragen einen Hash im Namen und ändern sich nie
            cache = "public, max-age=31536000, immutable" if path.startswith("_app/immutable/") else "no-cache"
            return FileResponse(file, headers={"Cache-Control": cache})
        return FileResponse(web / "200.html", headers={"Cache-Control": "no-cache"})
