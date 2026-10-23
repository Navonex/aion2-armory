"""Testaufbau: SQLite in einem Temp-Ordner, AION-2-Website und Abyss Logs gefälscht."""
from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from armory_api.config import Settings
from armory_api.main import create_app

from .fake_abyss import HOST as ABYSS_HOST
from .fake_abyss import FakeAbyss
from .fake_nc import HOSTS as NC_HOSTS
from .fake_nc import FakeNC

BASE = "http://localhost:8000"
ORIGIN = {"origin": BASE}


class FakeNet:
    """Beantwortet alle Anfragen der Armory nach außen: AION-2-Website (fake_nc.py), Abyss Logs (fake_abyss.py)."""

    def __init__(self) -> None:
        self.nc = FakeNC()
        self.abyss = FakeAbyss()

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.host in NC_HOSTS:
            return self.nc(request)
        if request.url.host == ABYSS_HOST:
            return self.abyss(request)
        return httpx.Response(404)


@pytest.fixture
def database_url(tmp_path):
    return f"sqlite+aiosqlite:///{tmp_path}/armory.db"


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
