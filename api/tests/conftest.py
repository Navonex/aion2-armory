"""Testaufbau: SQLite in einem Temp-Ordner, AION-2-Website, Abyss Logs und MetaBot.GG gefälscht."""
from __future__ import annotations

import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine

from armory_api.bis_collector import BisCollector
from armory_api.config import Settings
from armory_api.main import create_app
from armory_api.models import Base

from .fake_abyss import HOST as ABYSS_HOST
from .fake_abyss import FakeAbyss
from .fake_metabot import HOST as METABOT_HOST
from .fake_metabot import FakeMetaBot
from .fake_nc import HOSTS as NC_HOSTS
from .fake_nc import FakeNC

BASE = "http://localhost:8000"
ORIGIN = {"origin": BASE}


class FakeNet:
    """Beantwortet alle Anfragen der Armory nach außen: AION-2-Website (fake_nc.py), Abyss Logs (fake_abyss.py),
    MetaBot.GG (fake_metabot.py)."""

    def __init__(self) -> None:
        self.nc = FakeNC()
        # Ranglisten und Würfeltabellen für die Zählung (census.py), siehe fake_abyss.py, fake_metabot.py
        self.abyss = FakeAbyss()
        self.metabot = FakeMetaBot()

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.host in NC_HOSTS:
            return self.nc(request)
        if request.url.host == ABYSS_HOST:
            return self.abyss(request)
        if request.url.host == METABOT_HOST:
            return self.metabot(request)
        return httpx.Response(404)


@pytest.fixture(autouse=True)
def no_background_collector(monkeypatch):
    """Der Sammler der BiS-Listen läuft im Test nicht neben der Armory her; test_bis.py ruft seine Takte selbst
    auf. Sonst sammeln zwei Sammler gleichzeitig in dieselbe Datenbank."""
    async def idle(self: BisCollector) -> None:
        return None
    monkeypatch.setattr(BisCollector, "run", idle)


@pytest.fixture
def database_url(tmp_path):
    """Tabellen gleich anlegen: manche Tests schreiben in die Datenbank, bevor die App läuft."""
    url = f"sqlite+aiosqlite:///{tmp_path}/armory.db"

    async def create() -> None:
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
    asyncio.run(create())
    return url


@pytest.fixture
def fake() -> FakeNet:
    return FakeNet()


@pytest.fixture
def make_client(database_url, fake):
    def _make(**overrides) -> TestClient:
        values = dict(database_url=database_url, armory_base_url=BASE, armory_passwort="",
                      # explizit, sonst greift ARMORY_WEB_DIR aus der Umgebung (im Image gesetzt)
                      armory_web_dir=None,
                      # Abrufe von der Website nur in den Tests, die sie einschalten
                      armory_aion2_enabled=False, armory_aion2_pause=0)
        settings = Settings(**{**values, **overrides})
        app = create_app(settings, http=httpx.AsyncClient(transport=httpx.MockTransport(fake)))
        return TestClient(app, base_url=BASE, follow_redirects=False)
    return _make


@pytest.fixture
def client(make_client):
    with make_client() as c:
        yield c
