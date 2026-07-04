# 🎲 Kniffel Tracker

Ein kleiner Django-Service, um mit Freunden im echten Leben Kniffel (Yahtzee) zu spielen – ohne Papier und Stift. Spieler anlegen, Spiel starten, Punkte in einem digitalen Kniffel-Block eintragen und am Ende die ewige Rangliste pflegen.

## Features

- **Spielerverwaltung**: Spieler anlegen, bearbeiten und löschen.
- **Spiele anlegen**: Neue Runden starten und Spieler hinzufügen.
- **Digitaler Kniffel-Block**: Alle 13 Kategorien inklusive Bonus (≥63 Oberer Teil → +35 Punkte).
- **Feste untere Kategorien**: Full House, Kleine Straße, Große Straße und Kniffel können als „Gewürfelt" oder „Gestrichen" markiert werden.
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
   pip install django==6.0.6
   ```

4. Migrationen anwenden:

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
2. **Spiel starten**: Über *Spiele → Neues Spiel starten* eine neue Runde anlegen.
3. **Spieler hinzufügen**: Im Spiel auf *Spieler hinzufügen* klicken und Teilnehmer auswählen.
4. **Punkte eintragen**: *Punkte eintragen* öffnet den digitalen Kniffel-Block. Einfach die Werte pro Spieler und Kategorie eingeben und speichern.
5. **Spiel beenden**: Wenn alles eingetragen ist, auf *Spiel beenden* klicken. Die Ergebnisse werden festgeschrieben.
6. **Ewige Liste**: Unter *Ewige Liste* siehst du, wer die meisten Spiele gewonnen hat.

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

## Wichtige Hinweise

- `SECRET_KEY` und `DEBUG=True` in `yahtzee_tracker/settings.py` sind für die lokale Entwicklung gedacht. Vor einem Deployment müssen beide angepasst werden.
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

## Deployment mit GitHub Container Registry (GHCR)

Ein `Makefile` vereinfacht das Bauen, Pushen und Deployen des Images.

### Voraussetzungen

- Ein GitHub Account mit einem Personal Access Token (PAT), das mindestens die Berechtigung `write:packages` hat.
- Das Token in der Umgebungsvariable `GITHUB_TOKEN` verfügbar machen.
- Deinen GitHub-Username in der Umgebungsvariable `GITHUB_USER` setzen.
- SSH-Zugriff auf den Zielserver, auf dem Docker Compose bereits eingerichtet ist.

### Umgebungsvariablen setzen

```bash
export GITHUB_USER=your-github-username
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

### Makefile-Targets

```bash
make help          # Zeigt alle verfügbaren Targets
make test          # Django-Tests lokal ausführen
make build         # Docker-Image bauen
make login         # Lokal bei GHCR.io anmelden
make push          # Image nach GHCR.io pushen
make push-latest   # Zusätzlich als 'latest' taggen und pushen
make deploy        # Image auf dem Server pullen und Container neustarten
make clean         # Lokales Image entfernen
```

### Beispiel: vollständiges Build & Deploy

```bash
# 1. Tests laufen lassen
make test

# 2. Image bauen
make build

# 3. Bei GHCR.io anmelden und Image pushen
make login
make push
make push-latest

# 4. Auf Server deployen (Remote-Daten in Makefile anpassen oder übergeben)
make deploy REMOTE_HOST=user@server.example.com REMOTE_DIR=/opt/kniffel-tracker
```

### Server-Vorbereitung für `make deploy`

Auf dem Zielserver musst du mindestens einmalig bei GHCR.io eingeloggt sein, damit `docker pull` funktioniert:

```bash
ssh user@server.example.com
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin
```

Außerdem sollte `docker-compose.yml` und ggf. eine `.env`-Datei bereits unter `REMOTE_DIR` liegen.

### Hinweise zum Docker-Setup

- Das Entrypoint-Skript `docker-entrypoint.sh` führt beim Start automatisch `python manage.py migrate` aus.
- Für Produktion wird `Gunicorn` als WSGI-Server verwendet, nicht der Django-Entwicklungsserver.
- Passe vor dem Deployment unbedingt `SECRET_KEY`, `DEBUG=False` und `ALLOWED_HOSTS` an.

## Projektstruktur

- `yahtzee_tracker/` – Django-Projekteinstellungen, URLs und WSGI/ASGI.
- `users/` – `Player`-Modell und Spieler-CRUD.
- `games/` – `Game`, `GamePlayer`, `ScoreEntry`-Modelle, Spiel-Logik und Templates.
- `templates/` – Gemeinsame Templates (Base-Layout).
