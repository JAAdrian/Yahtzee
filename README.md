# 🎲 Kniffel Tracker

Ein kleiner Django-Service, um mit Freunden im echten Leben Kniffel (Yahtzee) zu spielen – ohne Papier und Stift. Spieler anlegen, Spiel starten, Punkte in einem digitalen Kniffel-Block eintragen und am Ende die ewige Rangliste pflegen.

## Features

- **Spielerverwaltung**: Spieler anlegen, bearbeiten und löschen.
- **Spiele anlegen**: Neue Runden starten und direkt Teilnehmer auswählen.
- **Digitaler Kniffel-Block**: Alle 13 Kategorien inklusive Bonus (≥63 Oberer Teil → +35 Punkte).
- **Feste untere Kategorien**: Full House, Kleine Straße, Große Straße und Kniffel können als „Gewürfelt" oder „Gestrichen" markiert werden.
- **Reaktives Speichern**: Punkte werden bei jeder Eingabe automatisch gespeichert, die Summen aktualisieren sich sofort.
- **Spiel beenden**: Punkte werden gespeichert, Gewinner ermittelt.
- **Ewige Liste**: Rangliste der Spieler nach gewonnenen Spielen.

## Voraussetzungen

- Python 3.14.6
- asdf (optional, verwaltet über `.tool-versions`)
- Eine virtuelle Umgebung im Projektverzeichnis (`.venv/`)

## Installation

1. Repository klonen und ins Projektverzeichnis wechseln:

   ```bash
   git clone <repo-url>
   cd Yahtzee
   ```

2. Virtuelle Umgebung erstellen und aktivieren:

   ```bash
   python3.14 -m venv .venv
   source .venv/bin/activate
   ```

3. Abhängigkeiten installieren:

   ```bash
   pip install -r requirements.txt
   ```

4. Lokale Umgebungsvariablen anlegen:

   ```bash
   python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(50)}\nDEBUG=True')" > .env
   ```

   `.env` ist bereits in `.gitignore` eingetragen und wird vom Entwicklungsserver automatisch geladen.

5. Migrationen anwenden:

   ```bash
   python manage.py migrate
   ```

## Nutzung

### Entwicklungsserver starten

```bash
python manage.py runserver
```

Die App ist dann unter `http://127.0.0.1:8000/` erreichbar.

### Ablauf

1. **Spieler anlegen**: Über *Spieler → Neuer Spieler* Teilnehmer erfassen.
2. **Spiel starten**: Über *Spiele → Neues Spiel starten* eine neue Runde anlegen und direkt die Teilnehmer auswählen.
3. **Punkte eintragen**: Der digitale Kniffel-Block öffnet sich automatisch. Werte pro Spieler und Kategorie eingeben – Summen werden sofort aktualisiert.
4. **Spiel beenden**: Wenn alles eingetragen ist, auf *Spiel beenden* klicken. Die Ergebnisse werden festgeschrieben.
5. **Ewige Liste**: Unter *Ewige Liste* siehst du, wer die meisten Spiele gewonnen hat.

### Admin-Oberfläche

Optional kannst du einen Admin-Benutzer anlegen:

```bash
python manage.py createsuperuser
```

Die Admin-Oberfläche ist unter `/admin/` erreichbar.

## Tests ausführen

```bash
python manage.py test
```

Tests laufen ohne gesetzte `SECRET_KEY`-Umgebungsvariable, da sie intern einen Test-Key verwenden.

## Wichtige Hinweise

- Für die lokale Entwicklung werden `SECRET_KEY` und `DEBUG=True` aus der `.env`-Datei geladen.
- Vor einem Deployment müssen `SECRET_KEY` als Umgebungsvariable gesetzt und `DEBUG=False` sein. Die App verweigert den Start, wenn kein `SECRET_KEY` konfiguriert ist.
- Für ein Production-Deployment mit Docker sollte die SQLite-Datenbank (`db.sqlite3`) in ein persistentes Volume ausgelagert werden, damit die Daten bei Container-Neustarts erhalten bleiben.
- Für hohe Last oder mehrere Container-Instanzen empfiehlt sich ein Wechsel von SQLite zu PostgreSQL.

## Docker-Deployment

Die App lässt sich mit Docker Compose einfach deployen. Die SQLite-Datenbank wird dabei in ein benanntes Volume ausgelagert, damit sie bei Container-Neustarts erhalten bleibt.

### Voraussetzungen

- Docker
- Docker Compose

### Schnellstart

1. Einen sicheren `SECRET_KEY` generieren:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

2. Den generierten Wert in `docker-compose.yml` bei `SECRET_KEY=` eintragen.

3. Bei Bedarf `ALLOWED_HOSTS` in `docker-compose.yml` auf deine Domain anpassen.

4. Container bauen und starten:

   ```bash
   docker compose up -d --build
   ```

5. Die App ist unter `http://localhost:8000/` erreichbar.

### Wichtige Befehle

```bash
# Container neu bauen und starten
docker compose up -d --build

# Logs ansehen
docker compose logs -f

# Container stoppen
docker compose down

# Migrationen manuell ausführen (wird beim Start automatisch erledigt)
docker compose exec app python manage.py migrate

# Admin-Benutzer anlegen
docker compose exec app python manage.py createsuperuser
```

### Backup der SQLite-Datenbank

Da die Datenbank im Docker-Volume liegt, solltest du sie regelmäßig sichern:

```bash
docker compose cp app:/app/data/db.sqlite3 ./backup/kniffel-$(date +%F).sqlite3
```

## Deployment mit Fly.io

Die App kann auch direkt auf Fly.io deployt werden. Eine `fly.toml` liegt im Repository.

### Erstmaliges Setup

```bash
fly apps create yahtzee
fly volumes create kniffel_data --region ams --size 1
fly secrets set SECRET_KEY="<generate-with-secrets.token_urlsafe(50)>" ALLOWED_HOSTS="yahtzee.fly.dev"
fly scale count 1
fly deploy
```

> Wichtig: SQLite kann nicht mehrere gleichzeitige Schreiber sicher verarbeiten. Halte die App deshalb auf **genau einer Machine** (`fly scale count 1`).

### Update deployen

```bash
fly deploy --ha=false
```

## Projektstruktur

- `yahtzee_tracker/` – Django-Projekteinstellungen, URLs und WSGI/ASGI.
- `users/` – `Player`-Modell und Spieler-CRUD.
- `games/` – `Game`, `GamePlayer`, `ScoreEntry`-Modelle, Spiel-Logik und Templates.
- `templates/` – Gemeinsame Templates (Base-Layout).
- `AGENTS.md` – Interne Notizen für Entwicklungs-Assistenten.
