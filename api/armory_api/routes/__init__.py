"""Alle Bereiche der API. Ein neuer Bereich = eine Datei hier mit `router` + Eintrag in ROUTERS.

    /api/public/…  immer ohne Passwort (geteilte Links, Impressum)
    /api/…         hinter dem Passwort, falls ARMORY_PASSWORT gesetzt ist
"""
from . import account, armory, bis, public

ROUTERS = [account.router, armory.router, bis.router, public.router]
