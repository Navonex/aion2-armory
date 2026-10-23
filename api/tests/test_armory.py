"""Armory: Charaktere eintragen, abrufen, Verlauf, Rechte. NC ist nachgebaut (fake_nc.py), nur erfundene Daten."""
import asyncio
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from armory_api.aion2 import NC
from armory_api.armory import Armory
from armory_api.models import Character, CharacterDay

from .conftest import BASE, ORIGIN
from .fake_nc import info, search_row

ON = {"armory_aion2_enabled": True}
NEW = {"name": "Testheld", "server_id": 2302, "character_id": "abc="}


MEMBER = None  # es gibt nur das Konto „Gilde“; der Parameter bleibt, damit die Tests lesbar bleiben


def login(make_client, fake, who=None, **settings):
    """Neuer Browser (ohne Login gibt es nur das Konto „Gilde“)."""
    c = make_client(**{**ON, **settings})
    c.__enter__()
    return c


def db_run(database_url, work):
    async def go():
        engine = create_async_engine(database_url)
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            result = await work(db)
            await db.commit()
        await engine.dispose()
        return result
    return asyncio.run(go())


def age(database_url, character_id, hours):
    """Letzten Abruf zurückdatieren (Sperre des Knopfs, täglicher Lauf)."""
    when = datetime.now(UTC) - timedelta(hours=hours)
    db_run(database_url, lambda db: db.execute(update(Character).where(Character.id == character_id)
                                               .values(fetched_at=when)))


def test_suche(make_client, fake):
    fake.nc.rows = [search_row("Testheld"), search_row("Testheldin", cid="xyz%3D"),
                    search_row("Testheld", server=9999, cid="fremd%3D")]  # Server ohne Shard fällt weg
    c = login(make_client, fake, MEMBER)
    hits = c.get("/api/armory/search", params={"name": "testheld"}).json()
    assert [(h["name"], h["server_id"], h["character_id"], h["taken_by"]) for h in hits] == [
        ("Testheld", 2302, "abc=", None), ("Testheldin", 2302, "xyz=", None)]
    assert hits[0]["image"].startswith("https://profileimg.plaync.com/game_profile_images/")
    assert c.get("/api/armory/search", params={"name": "t"}).status_code == 422
    assert c.get("/api/armory/search", params={"name": "Testheld", "region": "kr"}).status_code == 422


def test_ausgeschaltet(make_client, fake):
    c = login(make_client, fake, MEMBER, armory_aion2_enabled=False)
    assert c.get("/api/armory/search", params={"name": "Testheld"}).status_code == 503
    assert c.post("/api/armory", json=NEW, headers=ORIGIN).status_code == 503
    assert c.get("/api/armory").json() == []


def test_eintragen_abrufen_verlauf(make_client, fake, database_url):
    c = login(make_client, fake, MEMBER)
    r = c.post("/api/armory", json=NEW, headers=ORIGIN)
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    # Der Abruf läuft im Hintergrund, im TestClient direkt nach der Antwort
    d = c.get(f"/api/armory/{cid}").json()
    assert (d["status"], d["combat_power"], d["item_level"], d["class_name"]) == ("ok", 123456, 2554, "Waldläufer")
    assert d["data"]["de"]["equipment"][0]["name"] == "Testbogen" and d["mine"] and d["can_delete"]
    assert [(x["combat_power"], x["item_level"]) for x in d["days"]] == [(123456, 2554)]
    # Mit bekannter Charakter-ID keine Suche; in der Armory immer mit Werten je Gegenstand, beide Sprachen
    assert "/aion2global/search/v2/character" not in fake.nc.calls
    assert d["data"]["en"]["equipment"][0]["detail"]["set"]["name"] == "Testset"
    assert d["data"]["de"]["equipment"][0]["detail"]["sub"][0]["value"] == "9.1%"

    listed = c.get("/api/armory").json()
    assert [(x["name"], x["owner"], x["mine"], x["class_name"], x["server"]) for x in listed] == [
        ("Testheld", "Gilde", True, "Waldläufer", "Zikel")]
    assert listed[0]["image"].startswith("https://profileimg.plaync.com/")
    assert "data" not in listed[0]


def test_knopf_sperre_und_ein_eintrag_je_tag(make_client, fake, database_url):
    c = login(make_client, fake, MEMBER)
    cid = c.post("/api/armory", json=NEW, headers=ORIGIN).json()["id"]
    assert c.post(f"/api/armory/{cid}/refresh", headers=ORIGIN).status_code == 429
    age(database_url, cid, hours=1)
    stronger = info()
    stronger["profile"]["combatPower"] = 130000
    fake.nc.routes["/api/character/info"] = stronger
    assert c.post(f"/api/armory/{cid}/refresh", headers=ORIGIN).status_code == 202
    d = c.get(f"/api/armory/{cid}").json()
    assert d["combat_power"] == 130000
    assert [x["combat_power"] for x in d["days"]] == [130000]  # derselbe Tag wird überschrieben


def test_fehler_behaelt_die_letzten_daten(make_client, fake, database_url):
    c = login(make_client, fake, MEMBER)
    cid = c.post("/api/armory", json=NEW, headers=ORIGIN).json()["id"]
    age(database_url, cid, hours=1)
    fake.nc.routes["/api/character/info"] = 500
    assert c.post(f"/api/armory/{cid}/refresh", headers=ORIGIN).status_code == 202
    d = c.get(f"/api/armory/{cid}").json()
    assert d["status"] == "fehler" and d["error"]
    assert d["data"]["en"]["profile"]["combat_power"] == 123456 and len(d["days"]) == 1


def test_einmal_je_charakter(make_client, fake, database_url):
    c = login(make_client, fake, MEMBER)
    cid = c.post("/api/armory", json=NEW, headers=ORIGIN).json()["id"]
    r = c.post("/api/armory", json=NEW, headers=ORIGIN)
    assert r.status_code == 409 and "Gilde" in r.json()["detail"]
    hits = c.get("/api/armory/search", params={"name": "Testheld"}).json()
    assert hits[0]["taken_by"] == "Gilde"
    assert c.post("/api/armory", json={**NEW, "server_id": 9999}, headers=ORIGIN).status_code == 422
    d = c.get(f"/api/armory/{cid}").json()
    assert d["mine"] and d["can_delete"]
    assert c.delete(f"/api/armory/{cid}", headers=ORIGIN).status_code == 204
    assert c.get(f"/api/armory/{cid}").status_code == 404
    assert db_run(database_url, lambda db: db.scalars(select(CharacterDay))).all() == []

def test_taeglich_faellig(make_client, fake, database_url):
    c = login(make_client, fake, MEMBER)
    fresh = c.post("/api/armory", json=NEW, headers=ORIGIN).json()["id"]
    old = c.post("/api/armory", json={**NEW, "character_id": "alt="}, headers=ORIGIN).json()["id"]
    stuck = c.post("/api/armory", json={**NEW, "character_id": "offen="}, headers=ORIGIN).json()["id"]
    age(database_url, old, hours=25)
    db_run(database_url, lambda db: db.execute(update(Character).where(Character.id == stuck).values(status="offen")))

    async def due():
        engine = create_async_engine(database_url)
        armory = Armory(async_sessionmaker(engine, expire_on_commit=False),
                        NC(httpx.AsyncClient(transport=httpx.MockTransport(fake.nc)), pause=0))
        ids = await armory.due()
        await engine.dispose()
        return ids
    assert sorted(asyncio.run(due())) == sorted([old, stuck]) and fresh not in asyncio.run(due())


def test_suche_nach_klasse(make_client, fake):
    fake.nc.rows = [search_row("Testheld"), search_row("Testheiler", cid="heil%3D", pc=30)]
    c = login(make_client, fake, MEMBER)
    alle = c.get("/api/armory/search", params={"name": "test"}).json()
    assert [(h["name"], h["cls"]) for h in alle] == [("Testheld", "ranger"), ("Testheiler", "cleric")]
    nur = c.get("/api/armory/search", params={"name": "test", "cls": "cleric"}).json()
    assert [h["name"] for h in nur] == ["Testheiler"]
    # die Klassentabelle holt der Hub nur einmal
    assert fake.nc.calls.count("/en-us/api/gameinfo/pcdata") == 1
    assert c.get("/api/armory/search", params={"name": "test", "cls": "koch"}).status_code == 422


def test_live_ohne_speichern(make_client, fake, database_url):
    c = login(make_client, fake, MEMBER)
    r = c.get("/api/armory/live", params={"server_id": 2302, "name": "Testheld", "lang": "de"})
    assert r.status_code == 200
    assert r.json()["name"] == "Testheld" and r.json()["data"]["profile"]["class"] == "Waldläufer"
    # nichts gespeichert: weder Charakter noch Verlauf
    assert db_run(database_url, lambda db: db.scalar(select(func.count()).select_from(Character))) == 0
    assert c.get("/api/armory/live", params={"server_id": 2302, "name": "Niemand"}).status_code == 404


def test_passwort(make_client):
    """Mit ARMORY_PASSWORT fragt der Browser nach; geteilte Links gehen ohne."""
    with make_client(armory_passwort="geheim") as c:
        r = c.get("/api/armory")
        assert r.status_code == 401 and r.headers["www-authenticate"].startswith("Basic")
        assert c.get("/api/armory", auth=("egal", "falsch")).status_code == 401
        assert c.get("/api/armory", auth=("egal", "geheim")).status_code == 200
        assert c.get("/api/public/vergleich/gibtsnicht").status_code == 404
        assert c.get("/api/health").status_code == 200


def test_fremde_herkunft(client):
    assert client.post("/api/armory", json=NEW, headers={"origin": "https://boese.example"}).status_code == 403



def share(c, left, name="Testheld"):
    return c.post("/api/armory/compare/share", json={"left": left, "server_id": 2302, "name": name}, headers=ORIGIN)


def test_vergleich_teilen(make_client, fake, database_url):
    member = login(make_client, fake, MEMBER)
    cid = member.post("/api/armory", json=NEW, headers=ORIGIN).json()["id"]
    url = share(member, cid).json()["share_url"]
    assert url.startswith(f"{BASE}/v/")
    assert share(member, cid).json()["share_url"] == url  # derselbe Vergleich, derselbe Link
    token = url.rsplit("/", 1)[1]

    anyone = make_client(**ON)  # ohne Login
    anyone.__enter__()
    r = anyone.get(f"/api/public/vergleich/{token}", params={"lang": "de"})
    assert r.status_code == 200 and "noindex" in r.headers["x-robots-tag"]
    body = r.json()
    assert (body["left"]["name"], body["left"]["class_name"]) == ("Testheld", "Waldläufer")
    assert body["left"]["data"]["de"]["equipment"][0]["name"] == "Testbogen" and "owner" not in body["left"]
    # rechts live, nichts dazu gespeichert
    assert body["right"]["data"]["profile"]["class"] == "Waldläufer" and body["right_error"] is None
    assert db_run(database_url, lambda db: db.scalar(select(func.count()).select_from(Character))) == 1

    # rechts nicht (mehr) zu finden: links steht trotzdem da
    gone = share(member, cid, name="Niemand").json()["share_url"].rsplit("/", 1)[1]
    body = anyone.get(f"/api/public/vergleich/{gone}").json()
    assert body["right"] is None and body["right_error"] and body["left"]["name"] == "Testheld"

    assert member.delete(f"/api/armory/compare/share/{token}", headers=ORIGIN).json() == {"share_url": None}
    assert anyone.get(f"/api/public/vergleich/{token}").status_code == 404
    assert share(member, cid).json()["share_url"] != url  # neu geteilt, neuer Link


def test_vergleich_teilen_fehler(make_client, fake, database_url):
    member = login(make_client, fake, MEMBER)
    cid = member.post("/api/armory", json=NEW, headers=ORIGIN).json()["id"]
    token = share(member, cid).json()["share_url"].rsplit("/", 1)[1]
    assert share(member, 999).status_code == 404
    assert member.post("/api/armory/compare/share", json={"left": cid, "server_id": 9999, "name": "X"},
                       headers=ORIGIN).status_code == 422

    # Charakter ausgetragen: der Link ist weg
    assert member.delete(f"/api/armory/{cid}", headers=ORIGIN).status_code == 204
    assert member.get(f"/api/public/vergleich/{token}").status_code == 404


def test_vergleich_unbekannt(client):
    assert client.get("/api/public/vergleich/gibtsnicht").status_code == 404



def test_suche_ohne_klassentabelle(make_client, fake):
    """Fällt die Klassentabelle der Website aus, sucht die Armory trotzdem, nur ohne Klasse."""
    fake.nc.routes["/en-us/api/gameinfo/pcdata"] = 503
    c = login(make_client, fake, MEMBER)
    hits = c.get("/api/armory/search", params={"name": "Testheld"}).json()
    assert [(h["name"], h["cls"]) for h in hits] == [("Testheld", None)]
