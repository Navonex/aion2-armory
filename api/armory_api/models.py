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


class ClassCensus(Base):
    """Zählung der Top-Spieler einer Klasse (census.py): je Platz, wie viele welche Zeile der
    Seelenbindung tragen, und der größte Wert je Zeile (rating.count_players/add_tops). Keine Namen."""

    __tablename__ = "class_census"

    cls: Mapped[str] = mapped_column(String(32), primary_key=True)
    group_label: Mapped[str] = mapped_column(String(300))  # woher die Spieler stammen („Raid · Hard“)
    data: Mapped[dict] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ItemRolls(Base):
    """Würfeltabelle eines Gegenstands von MetaBot.GG (metabot.py), je englischem Namen; `data` leer,
    wenn MetaBot den Gegenstand nicht kennt (dann erst nach einer Woche neu fragen)."""

    __tablename__ = "item_rolls"

    name: Mapped[str] = mapped_column(String(128), primary_key=True)
    data: Mapped[dict | None] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BisQueue(Base):
    """Warteschlange der BiS-Listen (bis_collector.py): Namen aus den Ranglisten von Abyss Logs, die noch
    abgerufen werden. Der Name steht nur hier und nur bis zum Abruf."""

    __tablename__ = "bis_queue"

    id: Mapped[int] = mapped_column(BigID, primary_key=True)
    cls: Mapped[str] = mapped_column(String(32))
    player_name: Mapped[str] = mapped_column(String(64))
    raid: Mapped[str] = mapped_column(String(128))
    tier: Mapped[str] = mapped_column(String(16))  # „Hard“ oder „Normal“
    rank: Mapped[int] = mapped_column(Integer, index=True)  # Platz in der Klasse, mischt die Klassen beim Abruf
    combat_power: Mapped[int | None] = mapped_column(BigInteger)
    tries: Mapped[int] = mapped_column(Integer, default=0)


class BisSample(Base):
    """Ein Top-Spieler im Bestand der BiS-Listen: Ausrüstung und Skills in beiden Sprachen (FORMAT von
    aion2.py). Ohne Namen; `character_key` ist ein SHA-256 aus Server und Charakter-ID, damit niemand doppelt
    zählt. Die Zählung für die Bewertung der Armory (census.py) rechnet aus demselben Bestand."""

    __tablename__ = "bis_samples"

    id: Mapped[int] = mapped_column(BigID, primary_key=True)
    cls: Mapped[str] = mapped_column(String(32), index=True)
    character_key: Mapped[str] = mapped_column(String(64), unique=True)
    raid: Mapped[str] = mapped_column(String(128))
    tier: Mapped[str] = mapped_column(String(16))
    combat_power: Mapped[int | None] = mapped_column(BigInteger)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    data: Mapped[dict] = mapped_column(JSON)
