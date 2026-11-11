# AION 2 Armory – Hinweise für Claude Code

Eigenständige Armory für eine AION-2-Gilde (Kopie aus dem Projekt NexHub). Charaktere werden von
der offiziellen AION-2-Website (NCSOFT) abgerufen: Profil, Verlauf, Vergleich, Bewertung gegen Top-Spieler, BiS-Listen.
Nutzer-Doku: `README.md`. Sprache im Code und in Kommentaren: Deutsch.

## Aufbau

- `api/` – Python 3.12, FastAPI, SQLAlchemy (async), uv. Paket `armory_api`.
  - `aion2.py`: Abruf der öffentlichen Charakterseiten (inoffizielle Endpunkte der Website, mit Pause
    zwischen Anfragen, `ARMORY_AION2_PAUSE`). Format der gespeicherten Daten steht dort.
  - `armory.py`: eingetragene Charaktere, täglicher Abruf (`Armory.daily`, läuft im Webserver-Prozess), Verlauf.
  - `bis_collector.py`: sammelt im Hintergrund alle 5 Minuten ein paar Top-Spieler (Abyss Logs → NC-Suche →
    Ausrüstung), höchstens 200 je Klasse, ohne Namen (SHA-256-Schlüssel); `bis_stats.py` rechnet die BiS-Listen
    daraus, `routes/bis.py` liefert sie (`/api/bis`).
  - `census.py` zählt aus demselben Bestand je Klasse die Zeilen der Seelenbindung, `metabot.py` holt
    Würfelbereiche von MetaBot.GG, `rating.py` bewertet daraus jeden Gegenstand, `ratgeber.py` gibt Hinweise.
  - `classes.py`: Klassentabelle, Gegenstück in `web/src/lib/nexproto.ts`.
  - `routes/armory.py`: API `/api/armory/…`; `routes/public.py`: `/api/public/…` (geteilte Links).
  - `deps.py`: **kein Login** – jede Anfrage läuft über ein festes Konto „Gilde“ (`db.prepare`).
  - `main.py`: App, optionales Passwort (`ARMORY_PASSWORT`, HTTP-Basic) und CSRF-Schutz (Origin-Prüfung),
    liefert außerdem die gebaute Oberfläche aus (`ARMORY_WEB_DIR`).
  - Tabellen legt der Start per `create_all` an (keine Migrationen). Bei Schemaänderungen an
    bestehenden Installationen braucht es dann eine Migration (z. B. Alembic nachrüsten).
- Der Code ist eine Kopie aus NexHub (Stand 11.11.2026); Abweichungen: kein Login, keine Runs, kein Alembic.
- `web/` – SvelteKit (Svelte 5, Runes), adapter-static, reine Browser-App (`ssr = false`).
  - Seiten: `src/routes/hub/armory/…`, geteilte Links `src/routes/(public)/v|c/[token]`.
  - Profil-Bausteine: `src/modules/logs/components/` (CharacterProfile, ItemCard, DaevanionBoard …).
  - Texte DE/EN: `src/lib/texts.ts`, `src/modules/*/texts.ts`, Funktion `t()` aus `src/lib/i18n.svelte.ts`.
  - Design: `src/app.css` (dunkles „Liquid Glass“, CSS-Variablen).

## Befehle

```bash
cd api && uv sync && uv run pytest            # Tests (AION-2-Website und Abyss Logs gefälscht: tests/fake_*.py)
cd web && npm ci && npm run check && npm run build
ARMORY_WEB_DIR=../web/build uv run python -m armory_api   # aus api/, Port 8000
docker compose up -d --build                   # alles zusammen, Daten im Volume armory-daten
```

`npm run dev` (Vite) leitet `/api` an `127.0.0.1:8000` weiter.

## In eine Gilden-Homepage einbauen

Der Code geht davon aus, dass er **an der Wurzel einer eigenen Adresse** läuft: absolute Pfade wie
`/hub/armory`, `/api/…`, `/klassen/…`, `/favicon.svg` stehen fest im Frontend (ca. 15 Links,
21 API-Aufrufe). Wege, vom einfachsten zum aufwendigsten:

1. **Eigene Subdomain** (z. B. `armory.gilde.de`) per Reverse Proxy auf den Container, auf der Homepage
   verlinken. Keine Codeänderung. `ARMORY_BASE_URL` auf die Subdomain setzen.
2. **Als iframe** auf einer Seite der Homepage, Quelle wie in 1. Keine Codeänderung. Mit Passwort fragt
   der Browser im iframe nach; besser dann Weg 4 für den Login.
3. **Unter einem Unterpfad** (z. B. `gilde.de/armory`): in `web/vite.config.ts` `paths: { base: '/armory' }`
   für SvelteKit setzen und alle absoluten Pfade im Frontend über `base` aus `$app/paths` bilden
   (Links, `goto`, `api()`-Aufrufe in `src/lib/api.ts` und `src/modules/*/api.ts`, `/klassen/`-Bilder in
   `src/modules/logs/classes.ts`, Favicon). Im Backend den Proxy das Präfix abschneiden lassen oder FastAPI
   mit `root_path` starten; die freien Pfade in `main.py` (`OFFEN`) und `ARMORY_BASE_URL` (Teilen-Links)
   anpassen.
4. **Login der Homepage übernehmen**: `deps.current_user` statt des festen Kontos den angemeldeten Nutzer
   der Homepage liefern lassen (z. B. Sitzung/JWT der Homepage prüfen, oder ein vom Reverse Proxy gesetzter
   Header). Das Passwort in `main.py` dann entfernen. Die Rechte-Logik ist schon da und wird mit echten
   Konten wieder sinnvoll: `Character.user_id`, `PER_USER` (Grenze je Konto, jetzt 500),
   `mine`/`can_delete`/`_may_manage` in `routes/armory.py`, Rolle `admin`/`member` in `models.User`.
5. **Nur die Daten nutzen**: die Homepage holt JSON von `/api/armory` usw. und zeigt es selbst an. Bei
   anderer Adresse als die Armory dafür CORS in `main.py` freigeben (`fastapi.middleware.cors`) und die
   Origin-Prüfung (`schutz`) entsprechend erweitern. Schnittstelle: `/api/docs` (OpenAPI).

Unabhängig vom Weg: Geteilte Links (`/v/<token>`, `/api/public/…`) müssen ohne Login
erreichbar bleiben. Steht die Armory im Internet, gehören HTTPS sowie Impressum/Datenschutz dazu
(`ARMORY_OPERATOR_*`, Seiten unter `src/routes/(public)/impressum|datenschutz`; die Datenschutzseite ist
eine Vorlage, beim Einbau an die Homepage anpassen).
