"""Datenbanktabellen. Die Armory legt sie beim Start selbst an (db.prepare)."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# SQLite vergibt automatische IDs nur für INTEGER PRIMARY KEY
BigID = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    pass


class User(Base):
    """Konto. Ohne Login gibt es genau eins: „Gilde“ (db.prepare); alle Einträge gehören ihm."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigID, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def name(self) -> str:
        return self.username


class Snapshot:
    """Momentaufnahme eines Charakters von der AION-2-Website, gefüllt von characters.fill().

    status: offen, ok, nicht_gefunden, name_maskiert, fehler. `data` ist das Format aus aion2.py."""

    name: Mapped[str] = mapped_column(String(64))
    cls: Mapped[str | None] = mapped_column(String(32))
    server_id: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), index=True)
    nc_character_id: Mapped[str | None] = mapped_column(String(128))
    combat_power: Mapped[int | None] = mapped_column(BigInteger)
    item_level: Mapped[int | None] = mapped_column(Integer)
    data: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(String(200))
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))



class Character(Snapshot, Base):
    """Ein Charakter in der Armory, täglich neu abgerufen (armory.py)."""

    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("server_id", "nc_character_id"),)

    id: Mapped[int] = mapped_column(BigID, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CharacterDay(Base):
    """Verlauf in der Armory: je Charakter und Tag Kampfkraft und Item-Level des letzten Abrufs."""

    __tablename__ = "character_days"
    __table_args__ = (UniqueConstraint("character_id", "day"),)

    id: Mapped[int] = mapped_column(BigID, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    day: Mapped[date] = mapped_column(Date)
    combat_power: Mapped[int | None] = mapped_column(BigInteger)
    item_level: Mapped[int | None] = mapped_column(Integer)


class Comparison(Base):
    """Geteilter Vergleich: wer den Link /v/<token> kennt, sieht ihn ohne Passwort. Gespeichert ist nur, wer
    mit wem verglichen wird; die Werte holt die Armory beim Öffnen (der rechte live von der Website)."""

    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(BigID, primary_key=True)
    token: Mapped[str] = mapped_column(String(32), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    left_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    right_server_id: Mapped[int] = mapped_column(Integer)
    right_name: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BuildCheck(Base):
    """Letzter Build-Check eines Armory-Charakters (buildcheck.py). `result` ist die Auswertung aus
    evaluation.py, ohne Namen der Top-Spieler. Geteilt: wer /c/<share_token> kennt, sieht ihn ohne Passwort."""

    __tablename__ = "build_checks"

    id: Mapped[int] = mapped_column(BigID, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), unique=True)
    status: Mapped[str] = mapped_column(String(16))  # läuft, fertig, fehler
    progress: Mapped[int] = mapped_column(Integer, default=0)  # Profile der Gruppe schon geholt
    error: Mapped[str | None] = mapped_column(String(200))
    result: Mapped[dict | None] = mapped_column(JSON)
    share_token: Mapped[str | None] = mapped_column(String(32), unique=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
