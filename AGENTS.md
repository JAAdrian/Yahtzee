# Agent Notes: Kniffel Tracker

Compact reference for OpenCode sessions working on this Django project.

## Project at a Glance

- Single Django 6 app, SQLite by default, German-language UI (de-de / Europe/Berlin).
- Apps: `users` (Player CRUD), `games` (Game, GamePlayer, ScoreEntry models + scoring logic).
- Root URL redirects to `/games/`; admin lives at `/admin/`.
- No JS framework; plain Django templates under `templates/` and per-app template dirs.

## Environment

- Target Python: **3.14.6** (declared in `.tool-versions`).
- A local `.venv/` already exists and should be used.
- Activate: `source .venv/bin/activate` or use `.venv/bin/python` directly.
- Dependencies: `requirements.txt` pins `django==6.0.6`, `gunicorn`, and `whitenoise`.

## Common Commands

Use `.venv/bin/python manage.py <cmd>` or activate the venv first:

- Run dev server: `python manage.py runserver` → http://127.0.0.1:8000/
- Run tests: `python manage.py test` (23 tests across `users/tests.py`, `games/tests.py`)
- Run one app’s tests: `python manage.py test games` or `python manage.py test users`
- Apply migrations: `python manage.py migrate`
- Create admin user: `python manage.py createsuperuser`

Make shortcuts (verify `GITHUB_USER` / `GITHUB_TOKEN` / `REMOTE_HOST` / `REMOTE_DIR`):

- `make test` — run Django tests
- `make build` — build Docker image
- `make deploy REMOTE_HOST=... REMOTE_DIR=...` — SSH pull + recreate container

## Key Architecture Details

- `ScoreEntry` uses a single TextChoices category set. Fixed lower-section categories (Full House, Small/Large Straight, Yahtzee) award constant points when state is `filled`; `stricken` always contributes 0.
- `game_score` view POST handles both numeric categories and fixed-category state dropdowns. Field names in HTML must be:
  - Numeric: `score_<gameplayer_id>_<category>`
  - Fixed state: `state_<gameplayer_id>_<category>` (values: `empty`, `filled`, `stricken`)
- `GamePlayer.total_score` is computed on the fly from `ScoreEntry` rows; there is no denormalized total field.
- Creating/editing/deleting players and games is restricted to authenticated users via `@login_required`; lists and detail/result/leaderboard views remain public.
- Leaderboard counts wins by checking whether a player ranked first in each completed game.

## Docker / Production Notes

- `docker compose up -d --build` uses SQLite persisted in named volume `kniffel_data` mounted at `/app/data`.
- The container entrypoint (`docker-entrypoint.sh`) runs `collectstatic --noinput` and `migrate --noinput` on every start, then launches Gunicorn.
- Override in `docker-compose.yml` before real deployment: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`.
- `DATABASE_PATH` env var overrides the SQLite location; Docker sets it to `/app/data/db.sqlite3`.
- Production static files are served by WhiteNoise; `STATIC_ROOT` is `BASE_DIR / "staticfiles"`.
- `Makefile` defaults to `GITHUB_USER=jaadrian`; override via env or argument.

## Fly.io Deployment

The repo includes a `fly.toml` that builds the image from the repo's `Dockerfile` and deploys it with a persistent Fly Volume for the SQLite database.

### First-time setup

```bash
fly apps create yahtzee
fly volumes create kniffel_data --region ams --size 1
fly secrets set SECRET_KEY="<generate-with-secrets.token_urlsafe(50)>" ALLOWED_HOSTS="yahtzee.fly.dev"
fly deploy
```

### Required env vars

- `SECRET_KEY` — Django secret key (required, never use the dev default).
- `ALLOWED_HOSTS` — Fly app hostname(s), comma-separated; used by Django host validation.
- `DATABASE_PATH` — already set in `fly.toml` to `/app/data/db.sqlite3`.
- `DEBUG` — set to `"False"` in `fly.toml`.
- `SECURE_PROXY_SSL_HEADER` and `CSRF_TRUSTED_ORIGINS` are configured in `settings.py` so HTTPS/CSRF work behind Fly's proxy.

### fly.toml notes

- Build source: the repo's `Dockerfile` (managed by Fly on deploy).
- Volume `kniffel_data` is mounted at `/app/data` so SQLite survives redeploys.
- `auto_stop_machines = "stop"` and `min_machines_running = 0` allow the free-scale Machine to stop when idle. If you want it always on, set `min_machines_running = 1` and `auto_stop_machines = "off"`.
- Because SQLite cannot handle multiple writers safely, keep the app scaled to **a single Machine** (`fly scale count 1`).
- VM size defaults to `shared-cpu-1x` / 256 MB, which is enough for this app.

### Updating the app

Deploy from the local repo (no Git push required):

```bash
fly deploy --ha=false
```

`--ha=false` prevents Fly from launching a second Machine, which would break the single-volume SQLite setup.

### Creating an admin user on Fly

```bash
fly ssh console
python /app/manage.py createsuperuser
```

## Things That Are Easy to Miss

- `DEBUG` defaults to `True` and `SECRET_KEY` falls back to a hardcoded dev key when env vars are absent. Do not rely on these defaults for any deployment.
- `ALLOWED_HOSTS` is empty in debug mode and `localhost/127.0.0.1` in production mode if not explicitly set.
- Player names are unique case-insensitively (`Player.name` is unique at DB level; the view normalizes duplicates via lowercase comparison).
- The `.gitignore` explicitly ignores `AGENTS.md`; if you edit this file, stage it manually with `git add -f AGENTS.md`.
