# Agent Notes: Kniffel Tracker

Compact reference for OpenCode sessions. User-facing UI, messages, and README are
German (`LANGUAGE_CODE=de-de`, `TIME_ZONE=Europe/Berlin`); keep new strings German.

## Project at a Glance

- Django 6 project (`yahtzee_tracker/`) with two apps: `users` (`Player` CRUD) and
  `games` (`Game`, `GamePlayer`, `ScoreEntry` + scoring logic).
- Root `/` redirects to `/games/`. Auth URLs are under `/accounts/`; admin path comes
  from `ADMIN_URL` (default `/admin/`, `fly.toml` sets `hansvonwurst`).
- SQLite only; no linter, formatter, typechecker, codegen, or CI config in the repo.

## Environment and Commands

- Use the existing `.venv/`: `.venv/bin/python manage.py <cmd>` (or activate first).
- `.tool-versions` is the real Python target (**3.14.8**); `Dockerfile` and `README`
  still say 3.14.6. Don't bump one without the other.
- Run all tests: `.venv/bin/python manage.py test` (33 tests in
  `games/tests.py` + `users/tests.py`, currently passing).
- Run one test:
  `.venv/bin/python manage.py test games.tests.GameViewTests.test_score_sheet_saves_numeric_values`
- Tests need no `SECRET_KEY`: `settings.py` injects a test key when `"test"` is in
  `sys.argv`. Any other command needs `SECRET_KEY`, normally from `.env` (gitignored,
  auto-loaded). `DEBUG` defaults to `False` when unset.
- `make test` calls bare `python`, so activate `.venv` first or it may use the wrong
  interpreter. `make deploy` SSHes to `REMOTE_HOST` and pulls the image; it does not
  copy files.

## Scoring Model

- The score sheet lazily creates missing rows via `_ensure_score_entries`, so each
  `GamePlayer` ends up with all 13 `ScoreEntry` rows. Scores use either a numeric
  `value` or a `state` (`empty`/`filled`/`stricken`).
- Fixed lower categories (`FULL_HOUSE` 25, `SMALL_STRAIGHT` 30, `LARGE_STRAIGHT` 40,
  `YAHTZEE` 50) award constant points when filled; `stricken` always contributes 0.
- `GamePlayer.upper_sum`, `bonus` (+35 at ≥63), `lower_sum`, and `total_score` are
  computed properties. There is no denormalized total field.
- POST field names are a hard contract used by views, JS, and tests:
  - numeric: `score_<gameplayer_id>_<category>`
  - fixed state: `state_<gameplayer_id>_<category>` (`empty`, `filled`, `stricken`)
- Upper-section inputs are validated **only client-side** in `static/js/score.js`:
  values must be multiples of the category base (e.g. twos must be even). The Django
  views accept any integer, so server-side tests don't enforce this.
- `game_score_partial` is **not** an HTMX endpoint despite the docstring. `score.js`
  uses `fetch` (300 ms debounce on `input`, immediate on `change`) and posts to
  `/games/<pk>/score-partial/`. It needs the `csrf-token` meta tag from `base.html`
  and the `data-game-player` / `data-category` attributes on inputs.
- The partial response contains `<tbody id="__upper__">` / `<tbody id="__lower__">`,
  which the JS regex-extracts into `#upper-totals` / `#lower-totals`. Changing the
  scoring UI means updating `game_score.html`, `game_score_partial.html`, the two
  `_score_totals_*.html` includes, and `score.js` together.
- Invalid partial requests (bad category/value, finished game) return HTTP 204 with a
  flash message; open pages won't display it and totals simply stay stale.

## Access and Behavior Gotchas

- Public: game list/detail/results, leaderboard, player list/detail.
- Login required: creating/editing/deleting players, creating/deleting/finishing
  games, adding players, and both score views. Mutating POSTs also use
  `django-ratelimit` (10–120/min).
- Rate limiting uses `LocMemCache`; it is per-process. Scaling beyond one process or
  machine needs a shared cache.
- `game_finish` GET renders a confirmation; only POST marks the game complete.
- Leaderboard wins come from `Game.ranked_players()`; on a tie only the first sorted
  player counts as winner (ties are not split).
- `Player.name` is DB-unique but case-sensitive. Creation checks `name__iexact`;
  `player_update` has no such duplicate guard.

## Deploy Notes

- Local DB is `db.sqlite3` (gitignored); `DATABASE_PATH` overrides the location.
- Docker entrypoint runs `collectstatic` + `migrate` on every start, then Gunicorn
  with 2 workers. SQLite lives in volume `kniffel_data` at `/app/data`.
- Docker Compose ships placeholder `SECRET_KEY`/`ALLOWED_HOSTS`; override before use.
- Fly builds from `Dockerfile` and keeps SQLite on one volume. Keep exactly one
  Machine and deploy with `fly deploy --ha=false`; multiple writers can corrupt SQLite.
- `README.md` has the full Docker/Fly setup and backup commands; prefer it over
  duplicating deployment steps here.
