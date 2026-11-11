"""Einstellungen aus Umgebungsvariablen (z. B. in .env neben docker-compose.yml)."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    # SQLite reicht für eine Gilde. Postgres geht auch: postgresql+asyncpg://user:pw@host/db
    database_url: str = "sqlite+aiosqlite:///data/armory.db"
    # Adresse, unter der die Armory erreichbar ist (für Teilen-Links und den Schutz vor fremden Seiten)
    armory_base_url: str = "http://localhost:8000"
    # Leer: jeder mit der Adresse kommt rein. Gesetzt: der Browser fragt einmal nach dem Passwort
    # (Benutzername egal). Geteilte Links (/v/…) gehen immer ohne Passwort.
    armory_passwort: str = ""
    # Gebaute Web-Oberfläche (web/build); leer: nur die API
    armory_web_dir: Path | None = None
    armory_version: str = "dev"
    # Anbieterkennzeichnung für /impressum und /datenschutz, falls die Armory öffentlich erreichbar ist.
    # Anschrift: Zeilen mit „;“ getrennt. Leer: die Seiten sagen „noch nicht eingetragen“.
    armory_operator_name: str = ""
    armory_operator_address: str = ""
    armory_operator_email: str = ""
    armory_hoster: str = ""
    # Abrufe von der AION-2-Website: an/aus und Pause zwischen zwei Anfragen in Sekunden
    armory_aion2_enabled: bool = True
    armory_aion2_pause: float = 0.3

    @field_validator("armory_web_dir", mode="before")
    @classmethod
    def _empty_is_none(cls, v: object) -> object:
        return None if v == "" else v

    @field_validator("armory_base_url")
    @classmethod
    def _strip_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @property
    def origin(self) -> str:
        u = urlsplit(self.armory_base_url)
        return f"{u.scheme}://{u.netloc}"

    @property
    def operator(self) -> dict | None:
        if not self.armory_operator_name.strip():
            return None
        return {"name": self.armory_operator_name.strip(),
                "address": [line.strip() for line in self.armory_operator_address.split(";") if line.strip()],
                "email": self.armory_operator_email.strip() or None}
