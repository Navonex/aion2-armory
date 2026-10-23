"""Charakterprofile: Momentaufnahmen von der AION-2-Website.

`fill` füllt eine Momentaufnahme (models.Snapshot) für die Armory (armory.py), `load_details`
lädt die Werte je Gegenstand nach.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from .aion2 import LANGS, NC, NCError, NotFound, combat_power, item_level, localized
from .models import Snapshot

log = logging.getLogger(__name__)


async def fill(nc: NC, row: Snapshot, where: str, items: bool = False) -> None:
    """Holt die Momentaufnahme (beide Sprachen, mit `items` auch die Werte je Gegenstand) und setzt
    Status, Daten und Kennzahlen. Wirft nie: ein Fehler landet als Status `fehler`/`nicht_gefunden`
    in der Zeile, die bisherigen Daten bleiben. Mit bekannter Charakter-ID entfällt die Suche."""
    try:
        cid = row.nc_character_id or await nc.find(row.name, row.server_id)
        data = await nc.snapshots(row.server_id, cid, items)
    except NotFound as e:
        row.status, row.error = "nicht_gefunden", str(e)[:200]
    except NCError as e:
        row.status, row.error = "fehler", str(e)[:200]
        log.warning("Charakter %s (%s): %s", row.name, where, e)
    except Exception as e:  # unerwartete Antwort von NC: nie in „offen“ hängen bleiben
        row.status, row.error = "fehler", f"Format unbekannt: {type(e).__name__}"
        log.exception("Charakter %s (%s): unerwartete Antwort", row.name, where)
    else:
        row.status, row.error, row.nc_character_id, row.data = "ok", None, cid, data
        row.combat_power = combat_power(data)
        row.item_level = item_level(data)
    row.fetched_at = datetime.now(UTC)


def has_item_ids(data: dict | None) -> bool:
    """Ab FORMAT 2 merkt sich die Momentaufnahme die Gegenstands-IDs; nur dann lassen sich Werte nachladen."""
    if not data or not data.get("v"):
        return False
    return any(item.get("id") for item in localized(data).get("equipment", []))


async def load_details(nc: NC, row: Snapshot, where: str) -> None:
    """Werte je Gegenstand zu einer gespeicherten Momentaufnahme nachladen .
    Geholt wird für genau die gespeicherten Gegenstände; trägt der Charakter einen nicht mehr, bleibt
    er ohne Werte. Stand und Ergebnis stehen in data["details"]. Wirft nie."""
    data = dict(row.data or {})
    try:
        for lang in LANGS:
            snap = data.get(lang) or {}
            equipment = []
            for item in snap.get("equipment", []):
                detail = await nc.item(row.server_id, row.nc_character_id, lang, item)
                equipment.append({**item, "detail": detail})
            data[lang] = {**snap, "equipment": equipment}
        data["details"] = {"state": "ok"}
    except NCError as e:  # NC nicht erreichbar: der Knopf darf es noch einmal versuchen
        data["details"] = {"state": "fehler", "error": str(e)[:200]}
        log.warning("Item-Werte %s (%s): %s", row.name, where, e)
    except Exception:
        data["details"] = {"state": "fehler", "error": "Format unbekannt"}
        log.exception("Item-Werte %s (%s): unerwartete Antwort", row.name, where)
    data["details"]["at"] = datetime.now(UTC).isoformat()
    row.data = data  # neu zuweisen, sonst merkt SQLAlchemy die Änderung im JSON nicht
