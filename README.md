# AION 2 Armory

Eine Armory für eure Gilde in AION 2: Charaktere eintragen, täglich von der offiziellen
AION-2-Website abrufen und ansehen.

- **Charakterprofil**: Kampfkraft, Ausrüstung mit Werten, Titel, Skills, Daevanion
- **Verlauf**: Kampfkraft und Gegenstandsstufe pro Tag
- **Vergleich**: zwei Charaktere nebeneinander, auch mit jemandem, der nicht eingetragen ist; als Link teilbar
- **Build-Check**: ein Charakter gegen die 15 besten Spieler seiner Klasse (EU, ähnliche Kampfkraft,
  Rangliste von [Abyss Logs](https://abysslogs.com)); als Link teilbar
- Deutsch und Englisch

Es gibt kein Konto und keinen Login. Alle, die die Seite öffnen dürfen, sehen und pflegen dieselbe
Liste. Wer sie öffnen darf, regelt ein einfaches Passwort (optional). Geteilte Links funktionieren
immer ohne Passwort.

Entstanden als Teil von NexHub (Navonex und gamunex), hier als eigenständige Kopie nur mit der Armory.

## Starten mit Docker

Voraussetzung: Docker mit Compose.

```bash
git clone https://github.com/Navonex/aion2-armory.git
cd aion2-armory
cp .env.example .env      # Passwort und Adresse eintragen
docker compose up -d --build
```

Dann im Browser `http://<server>:8000` öffnen. Die Daten liegen im Docker-Volume `armory-daten`
(SQLite-Datei `armory.db`). Sichern: das Volume oder die Datei kopieren.

Aktualisieren:

```bash
git pull
docker compose up -d --build
```

## Einstellungen (`.env`)

| Variable | Bedeutung |
|---|---|
| `ARMORY_BASE_URL` | Adresse der Armory, z. B. `https://armory.meine-gilde.de`. Daraus entstehen die Teilen-Links. |
| `ARMORY_PASSWORT` | Passwort für die Gilde. Leer = jeder mit der Adresse kommt rein. Der Browser fragt einmal (Benutzername egal). |
| `ARMORY_OPERATOR_NAME`, `…_ADDRESS`, `…_EMAIL`, `ARMORY_HOSTER` | Impressum und Datenschutz, nur nötig, wenn die Armory öffentlich im Internet steht. Anschrift mit `;` trennen. |
| `DATABASE_URL` | Standard SQLite. Postgres geht auch: `postgresql+asyncpg://user:passwort@host/db` |

Steht die Armory im Internet, gehört HTTPS davor (z. B. Caddy oder ein anderer Reverse Proxy). Das
Passwort wird sonst unverschlüsselt übertragen.

## Entwicklung

```bash
# API (Python 3.12, uv)
cd api
uv sync
uv run pytest
ARMORY_WEB_DIR=../web/build uv run python -m armory_api   # Port 8000

# Web-Oberfläche (Node 24, SvelteKit)
cd web
npm ci
npm run dev       # Entwicklung (braucht die API daneben)
npm run build     # nach web/build, wird von der API ausgeliefert
npm run check
```

| Ordner | Inhalt |
|---|---|
| `api/armory_api/aion2.py` | Abruf von der offiziellen AION-2-Website |
| `api/armory_api/armory.py` | eingetragene Charaktere, täglicher Abruf, Verlauf |
| `api/armory_api/buildcheck.py`, `evaluation.py`, `abysslogs.py` | Build-Check |
| `api/armory_api/routes/` | API (`/api/armory/…`, öffentlich `/api/public/…`) |
| `web/src/routes/hub/armory/` | Seiten der Armory |
| `web/src/routes/(public)/` | geteilte Links (`/v/…`, `/c/…`), Impressum, Datenschutz |

## Hinweise

- Die Daten kommen von den öffentlichen Charakterseiten der offiziellen AION-2-Website (NCSOFT) und von
  Abyss Logs. Ändern die ihr Format, kann der Abruf ausfallen, bis der Code angepasst ist.
- Kein offizielles Projekt von NCSOFT. AION ist eine Marke von NCSOFT.
- Lizenz: GPL-3.0-or-later (siehe `LICENSE`).
