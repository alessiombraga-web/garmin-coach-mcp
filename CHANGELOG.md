# Changelog

## 0.3.1 — 2026-11-02

**All sports, not just running.**

- Laps and per-second data are now downloaded for every activity type (cycling, swimming, walking...),
  not only runs (`DETAIL_TYPE_MATCH` default changed from `run` to `all`). After updating, activities already in
  the archive without details are completed automatically at the next sync.
- Cadence keeps the right unit per sport: steps/min for running and walking, rpm for cycling (it was doubled).
- `get_activity`, `get_activity_series` and `training_summary` accept `type_filter` ('run', 'cycling', 'swim'...);
  `get_activity('latest')` now means the latest activity of any sport; laps also show speed in km/h.
- When an activity has no laps/per-second data, `get_activity` states the real reason, so Claude no longer
  blames the Garmin API (which provides the FIT file for every activity).

## 0.3.0 — 2026-11-01

**Install without Docker: Garmin Coach is now also a Claude Desktop extension.**

- New all-in-one Claude Desktop extension (`garmin-coach-<version>.mcpb`): double-click, paste the Garmin
  Personal API key, done. Runs inside Claude Desktop (Python managed by Claude Desktop via uv), stores the archive
  in `Documents/Garmin Coach` or a chosen folder, syncs while Claude Desktop is open. Read-only (official API).
- New Docker connector extension (`garmin-coach-docker-connector-<version>.mcpb`): connects Claude Desktop to the
  Docker server with a form (address + MCP token). No Node.js installation and no `claude_desktop_config.json` editing.
- New tools `get_athlete_notes` / `update_athlete_notes`: tell Claude about yourself in chat and it remembers.
- Cross-process sync lock (Claude Desktop can start more than one server process).
- Docker server: OAuth discovery probes answered with 404 and a clear 401 message for a wrong MCP token
  (mcp-remote used to report a misleading "Dynamic Client Registration rejected"); quotes around `MCP_TOKEN` ignored.
- Clearer `network_error` status when Garmin can't be reached.
- The community module is imported only when used (not installed in the extension).
- Docs: plain-language Italian guide (`README.it.md`), Italian Docker guide (`docs/docker.it.md`), English README
  reorganised; manual setup now lists Node.js install for Windows and macOS and recommends the full `npx` path.
- `scripts/build-mcpb.sh` and a GitHub workflow that attaches both `.mcpb` files to each release.

## 0.2.0 — 2026-10-25

**Data is now read through Garmin's official Connect Personal API, which is read-only.
Write access (structured workouts) is optional and requires enabling the community module.**

- New default data source: official [Garmin Connect Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api)
  via `garmin-connect-personal-api-python` (`GARMIN_PERSONAL_API_KEY`). Same original FIT files as before
  (verified byte-identical), no interactive login, no MFA.
- The unofficial python-garminconnect integration becomes an optional community module, off by default
  (`ENABLE_GARMINCONNECT=true`). It provides write access (create/schedule/delete workouts) and enriches data with
  per-lap grade-adjusted pace and shoes, which the official API does not expose.
- Workout tools explain how to enable write access when the module is off; `create_workout` still previews.
- `get_activity` shows the planned workout an activity was executed from (official API).
- `sync_status` reports read source and write access status.
- Upserts no longer erase fields the current source does not provide (e.g. VO2max).
- New `tools/probe_personal_api.py` to check the Personal API against the local archive.
- Migration from 0.1: add `GARMIN_PERSONAL_API_KEY` to `.env`; set `ENABLE_GARMINCONNECT=true` to keep
  workout tools (existing login tokens are reused); run `docker compose up -d --build`.

## 0.1.0 — 2026-09-27

First release.

- Garmin Connect → SQLite sync (history backfill + periodic incremental sync), original FIT files archived.
- MCP server (streamable HTTP, bearer token) with activity tools: `sync_garmin`, `sync_status`,
  `list_activities`, `get_activity`, `get_activity_series`, `training_summary`, `annotate_activity`, `query_sql`.
- Structured running workouts: `create_workout` (preview → confirm, calendar scheduling, in-place replace),
  `get_workout`, `list_workouts`, `delete_workout`.
- Optional personal notes for Claude in `data/athlete.md`.
- Documentation in English and Italian, third-party notices.
