# garmin-coach-mcp

**Let Claude read your Garmin running data — and, if you want, put workouts on your watch.**

`garmin-coach-mcp` keeps a private archive of your Garmin Connect activities (summaries, laps and
second-by-second data from the original FIT files) and lets [Claude Desktop](https://claude.ai/download)
analyse it through the [Model Context Protocol](https://modelcontextprotocol.io).

It works with every sport recorded on Garmin (running, cycling, swimming, walking...); some features, such as
running dynamics, heart-rate recovery and treadmill handling, are running-specific.

Data is read through Garmin's **official [Connect Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api)**,
which is **read-only**. Writing workouts to Garmin is optional and available only in the Docker version
(see [Write access](#write-access-optional-docker-only)).

> *"Sync and analyse this morning's run: how did my heart rate drift in the last 5 km?"*
> *"Compare my long runs of the last 8 weeks: pace, heart rate, cadence."*
> *"Did I execute Wednesday's planned session as prescribed?"*

🇮🇹 **Italiano:** [guida semplice, passo per passo](README.it.md) · [guida avanzata Docker](docs/docker.it.md)

---

## Contents

- [Two ways to install](#two-ways-to-install)
- [Quick install: Claude Desktop extension](#quick-install-claude-desktop-extension) · [Extension settings](#extension-settings)
- [Advanced install: Docker server](#advanced-install-docker-server)
- [Connecting Claude Desktop to the Docker server](#connecting-claude-desktop-to-the-docker-server)
- [Write access (optional, Docker only)](#write-access-optional-docker-only)
- [Heart-rate zones](#heart-rate-zones)
- [Weight, body composition and daily totals](#weight-body-composition-and-daily-totals)
- [Notes about you](#notes-about-you)
- [Tools](#tools)
- [Structured workouts](#structured-workouts)
- [Configuration (Docker)](#configuration-docker)
- [Maintenance](#maintenance)
- [Usage limits (Free plan)](#usage-limits-free-plan)
- [Troubleshooting](#troubleshooting)
- [Building the extensions](#building-the-extensions)
- [Data, privacy and security](#data-privacy-and-security)
- [Limitations and disclaimer](#limitations-and-disclaimer)
- [Credits](#credits)

---

## Two ways to install

| | **Claude Desktop extension** (recommended) | **Docker server** (advanced) |
|---|---|---|
| For | Everyone | Homelab / NAS users |
| Install | Double-click a file, paste your Garmin key | Docker, `.env`, terminal |
| Runs | Inside Claude Desktop, while it is open | 24/7 on your server |
| Data stored | On your computer (folder of your choice) | On the server (`./data`) |
| Reads data via | Official Garmin Personal API (read-only) | Official Garmin Personal API (read-only) |
| Write workouts to Garmin | ❌ | ✅ optional community module |
| Per-lap grade-adjusted pace, shoes from Garmin | ❌ | ✅ optional community module |

Both work with Claude Desktop on macOS and Windows. Neither works from the Claude mobile app or claude.ai on the web.

---

## Quick install: Claude Desktop extension

No terminal, no Docker, no configuration files.

1. **Install [Claude Desktop](https://claude.ai/download)** (macOS or Windows) and sign in.
2. **Create a Garmin Personal API key:** sign in to Garmin Connect on the web, open
   **Settings → Personal API** ([direct link](https://connect.garmin.com/app/settings/personalApiToken)),
   accept the terms, choose an expiry (up to 1 year) and create the key. Copy it: Garmin shows it only once.
3. **Download `garmin-coach-<version>.mcpb`** from the [latest release](https://github.com/fabio983/garmin-coach-mcp/releases/latest).
4. **Double-click the file.** Claude Desktop opens an installation window.
5. **Fill in the settings** (see [Extension settings](#extension-settings)): paste the Garmin key; the other fields
   are optional. Click **Install** and make sure the extension is enabled.
6. **Open a new chat** and ask: *"Sync my Garmin runs and tell me about my latest one."*

The first import continues in the background while Claude Desktop is open. Claude Desktop manages Python and all
dependencies by itself.

### Extension settings

Shown in the installation window and later in **Claude Desktop → Settings → Extensions → Garmin Coach**.

| Setting | Required | What it does | What to enter |
|---|---|---|---|
| **Garmin Personal API key** | Yes | Lets Garmin Coach read your Garmin data (read-only: it can't change anything). | The key created in Garmin Connect → Settings → Personal API. |
| **Data folder** | No | Where the archive is saved: activities, notes, heart-rate zones. A `Garmin Coach` folder is created inside it. | Leave the default (`Documents`) or pick another folder. |
| **Import runs from (YYYY-MM-DD)** | No | Date from which activities are downloaded **at the first import only**. An older date means a longer first import (a few seconds per activity). Changing it later has no effect: to add older activities ask Claude (*"sync my activities since 2019"*). | Default `2024-01-01`. Pick a recent date if you want to start quickly. |
| **Starting heart-rate zones** | No | Zones used for the "time in zone" figures (single activity and weekly summary). They are the **starting** zones: after a new test just tell Claude the new ones in chat (see [Heart-rate zones](#heart-rate-zones)). | 4 numbers: the bpm where zones 2, 3, 4 and 5 begin, e.g. `135,150,160,170` → Z1 <135, Z2 135–149, Z3 150–159, Z4 160–169, Z5 ≥170. Copy them from your watch settings in the Garmin Connect app: select your device → User Profile → Heart Rate & Power Zones → Heart Rate → Zones (zones are set per device, not in the general profile or on the website). The default values are only an example. |

---

## Advanced install: Docker server

For an always-on machine (homelab VM, NAS, Raspberry Pi 4/5, PC) with Docker and Docker Compose.

### 1. Get the code

```bash
git clone https://github.com/fabio983/garmin-coach-mcp.git
cd garmin-coach-mcp
```

### 2. Configure

Create a Garmin Personal API key as described above, then:

```bash
cp .env.example .env
openssl rand -hex 32        # copy the output into MCP_TOKEN
nano .env                   # paste the key in GARMIN_PERSONAL_API_KEY, set TZ, BACKFILL_FROM, HR_BANDS...
```

See [Configuration](#configuration-docker) for all options. **After any later change to `.env` run
`docker compose up -d`**: a plain `restart` does not reload it.

### 3. Build and start

```bash
docker compose build
docker compose up -d
docker compose logs -f
```

The first start imports your history since `BACKFILL_FROM`: one `Details <id> (running) ok` line per run and a
final `Auto sync: ok`. Check it from the computer where Claude Desktop runs:

```bash
curl http://SERVER-IP:8765/healthz      # → ok   (127.0.0.1 if Docker runs on the same computer)
```

Optional: `tools/probe_personal_api.py` checks your key and what the API returns, see [tools/README.md](tools/README.md).

---

## Connecting Claude Desktop to the Docker server

### Recommended: the connector extension (no files to edit)

1. Download **`garmin-coach-docker-connector-<version>.mcpb`** from the [latest release](https://github.com/fabio983/garmin-coach-mcp/releases/latest).
2. Double-click it. In the installation window fill in:
   - **Server address:** `http://127.0.0.1:8765/mcp` if Docker runs on the same computer, otherwise
     `http://SERVER-IP:8765/mcp`;
   - **MCP token:** the value of `MCP_TOKEN` in your `.env`.
3. Click **Install**, then open a new chat and ask *"What's the status of my Garmin archive?"*

It bundles [mcp-remote](https://github.com/geelen/mcp-remote) and uses the Node.js runtime included in
Claude Desktop: nothing else to install.

### Alternative: manual configuration

Only if you prefer not to use the connector extension.

1. **Install Node.js LTS** (skip if `node -v` in a terminal already prints a version):
   - **Windows** (PowerShell): `winget install OpenJS.NodeJS.LTS`
   - **macOS** (Terminal), with [Homebrew](https://brew.sh): `brew install node` — or download the macOS installer from
     [nodejs.org](https://nodejs.org) and double-click it

   Then close and reopen the terminal and check `node -v`.
2. Find the full path of `npx`: `where npx` (Windows) or `which npx` (macOS, usually `/opt/homebrew/bin/npx` or
   `/usr/local/bin/npx`). Using the full path avoids "npx not found" errors.
3. In Claude Desktop open **Settings → Developer → Edit config** and add the block below inside `mcpServers`
   (see [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json)). If the file already has
   other keys (e.g. `preferences`), keep them: `mcpServers` goes at the top level, separated by a comma.

   ```json
   {
     "mcpServers": {
       "garmin-coach": {
         "command": "/opt/homebrew/bin/npx",
         "args": ["-y", "mcp-remote@latest", "http://SERVER-IP:8765/mcp",
                  "--allow-http", "--transport", "http-only",
                  "--header", "Authorization:${AUTH_HEADER}"],
         "env": { "AUTH_HEADER": "Bearer YOUR_MCP_TOKEN" }
       }
     }
   }
   ```

   On Windows use the path from `where npx` with double backslashes, e.g. `"C:\\Program Files\\nodejs\\npx.cmd"`.
4. **Quit Claude completely** (Windows: also from the tray icon) **before saving**, then reopen it.
   **Settings → Developer** should list `garmin-coach` as *running*.

---

## Write access (optional, Docker only)

The official Personal API is **read-only**. To let Claude create and schedule workouts on your Garmin, the Docker
version can enable a community module based on
[python-garminconnect](https://github.com/cyberjunky/python-garminconnect), which talks to Garmin Connect's private
API with the same login flow as the mobile app.

> **Before enabling it:** it is not an official Garmin interface, it can stop working whenever Garmin changes its
> private API, and it logs in with your account credentials. Use it only with your own account.

1. In `.env` set `ENABLE_GARMINCONNECT=true`
2. Recreate the container: `docker compose up -d`
3. Log in once: `docker compose run --rm garmin-coach login` (email, password, MFA code if enabled).
   Warnings like `mobile+cffi returned 429` are normal as long as it ends with `Login OK`.
4. `docker compose restart`, then restart Claude Desktop.
5. In a new chat ask *"What's the status of my Garmin archive?"* → `write access (community module): enabled`.

It also adds per-lap grade-adjusted pace and the shoes assigned in Garmin Connect. To disable it set
`ENABLE_GARMINCONNECT=false`, run `docker compose up -d` and optionally delete `data/tokens/garmin_tokens.json`.

---

## Heart-rate zones

Time-in-zone figures (in `get_activity` and `training_summary`) use **the zones valid on the date of each activity**:

- before you save any zones in chat, the *starting zones* from the settings (`HR_BANDS` with Docker) apply;
- when your zones change, for example after a test, tell Claude: *"After today's test my zones are 158, 166, 170,
  175: save them"*. It stores them with `set_hr_zones`, valid **from that date**: older activities keep the zones
  valid at their time, so comparisons over months stay fair;
- to apply new zones to the whole history too, say so (*"use them for all my past activities as well"*);
- ask *"which heart-rate zones are you using?"* to see the current zones and their history (`get_hr_zones`).

Claude can also recompute any activity or weekly summary with today's zones on request (`zones='current'`).

---

## Weight, body composition and daily totals

Read live from the official API (nothing to configure):

- `get_body_composition`: weight and, if your scale measures them (e.g. Garmin Index), BMI, body fat %, body water %,
  muscle mass, bone mass, visceral fat, metabolic age. Manual weight entries in Garmin Connect are included.
- `get_daily_summary`: day by day, total/active/resting calories, steps, distance, resting/min/max heart rate,
  stress, Body Battery, intensity minutes.

> *"How did my weight and body fat change in the last 2 months?"* · *"How many calories did I burn yesterday?"*

Fields depend on your devices; the tools state which ones your account doesn't provide.

---

## Notes about you

Claude works better when it knows your context: sensors, max heart rate, zones, target cadence, which shoes are for
what. Just tell it in a chat (*"My max heart rate is 190 and I've used a chest strap since June: save it"*): it
stores the notes with `update_athlete_notes` and reads them in future chats.

The notes are a plain text file, `athlete.md`, in the data folder (`data/athlete.md` with Docker; Docker users can
start from [`examples/athlete.example.md`](examples/athlete.example.md)).

---

## Tools

| Tool | What it does | Extension | Docker |
|---|---|---|---|
| `sync_garmin` | Fetch new activities now (`full=true` re-imports everything in background) | ✅ | ✅ |
| `sync_status` | Data sources, archive counts, period covered, latest syncs | ✅ | ✅ |
| `list_activities` | Activities in a date range, filterable by type | ✅ | ✅ |
| `get_activity` | Summary, laps, HRR60, time in HR zones, planned workout, annotations | ✅ | ✅ |
| `get_activity_series` | Second-by-second data averaged every N seconds | ✅ | ✅ |
| `training_summary` | Weekly runs, km, time, pace, longest run, load, HR distribution | ✅ | ✅ |
| `annotate_activity` | Real temperature, humidity, treadmill, shoes, session type, RPE, HRR, notes | ✅ | ✅ |
| `get_athlete_notes` / `update_athlete_notes` | Notes about you for future chats | ✅ | ✅ |
| `set_hr_zones` / `get_hr_zones` / `delete_hr_zones` | Heart-rate zones from the chat, each valid from a date | ✅ | ✅ |
| `get_body_composition` | Weight, BMI, body fat, water, muscle, bone (live, official API) | ✅ | ✅ |
| `get_daily_summary` | Daily calories, steps, resting HR, stress, Body Battery (live, official API) | ✅ | ✅ |
| `query_sql` | Read-only SQL on the archive | ✅ | ✅ |
| `create_workout` | Structured running workout: preview → confirm → upload and schedule | – | ✍️ community module |
| `get_workout` / `list_workouts` | Workouts in Garmin Connect, calendar | – | ✍️ community module |
| `delete_workout` | Unschedule / delete a workout (only when you ask) | – | ✍️ community module |

---

## Structured workouts

*Docker version with the [community module](#write-access-optional-docker-only).*

Describe the session in plain words and Claude builds it. Under the hood it is a step list:

```json
[
  {"kind": "warmup", "time": "15:00", "hr": "120-145", "note": "easy"},
  {"repeat": 3, "steps": [
    {"kind": "interval", "distance_km": 2, "pace": "5:40-5:45"},
    {"kind": "recovery", "time": "2:00", "note": "easy jog"}
  ]},
  {"kind": "cooldown", "time": "10:00"}
]
```

| Field | Values |
|---|---|
| `kind` | `warmup`, `interval`, `recovery`, `rest`, `cooldown`, `other` |
| duration (one) | `time` (`"mm:ss"`), `distance_km`, `distance_m`, `lap: true` (until lap button) |
| target (optional, one) | `pace` (`"m:ss-m:ss"` per km) or `hr` (`"min-max"` bpm) |
| `note` | Short text shown on the watch for that step |
| repeat | `{"repeat": N, "steps": [...]}`, can be nested |

Garmin targets always have two limits: for "slower than 7:00/km" use a wide range (`7:00-7:45`) or a heart-rate cap.
Claude always shows a **preview** first; `replace_workout_id` rewrites an existing workout keeping its calendar dates.

---

## Configuration (Docker)

All settings live in `.env` (see [`.env.example`](.env.example)). After changing it run `docker compose up -d`.

| Variable | Default | Description |
|---|---|---|
| `MCP_TOKEN` | – | Bearer token required by the MCP endpoint. **Set it.** |
| `GARMIN_PERSONAL_API_KEY` | – | Official Personal API key (read-only data source). **Set it.** |
| `ENABLE_GARMINCONNECT` | `false` | Optional community module (write access, GAP per lap, shoes) |
| `GARMIN_EMAIL` / `GARMIN_PASSWORD` | – | Community module only: automatic re-login (not usable with MFA) |
| `TZ` | – | Timezone, e.g. `Europe/Rome` |
| `BACKFILL_FROM` | `2024-01-01` | Start date of the first import |
| `SYNC_INTERVAL_MIN` | `30` | Background sync interval (0 = on demand only) |
| `REQUEST_DELAY_S` | `1.5` | Pause between Garmin requests |
| `HR_BANDS` | `135,150,160,170` | Starting HR zones: bpm where zones 2..N begin. Zones told to Claude in chat (`set_hr_zones`) take over from their date |
| `DETAIL_TYPE_MATCH` | `all` | Activity types (substring of Garmin `typeKey`, e.g. `run,cycling`) for which FIT/laps/records are downloaded; `all` = every activity |
| `ATHLETE_FILE` | `/data/athlete.md` | Notes about you |
| `MCP_PORT` | `8765` | Port inside the container |

The extension exposes the main options in its own settings: see [Extension settings](#extension-settings).

---

## Maintenance

| Task | Extension | Docker |
|---|---|---|
| Update | Download and open the new `.mcpb` | `git pull && docker compose up -d --build`, restart Claude Desktop |
| Garmin key expired (`auth_required` in `sync_status`) | New key → paste it in the extension settings | New key → `.env` → `docker compose up -d` |
| Import older history | Ask Claude: *"sync my runs since 2020-01-01"* | same, or `docker compose exec garmin-coach python -m app sync --since 2020-01-01` |
| Backup | Copy the `Garmin Coach` folder | Copy `data/` |
| Logs | Settings → Developer → Garmin Coach → logs | `docker compose logs -f` |

Garmin emails you about a week before the Personal API key expires.

---

## Usage limits (Free plan)

The extension also installs on the Free plan, but Free usage limits run out quickly: an analysis with laps, zones
and week-on-week comparisons produces a lot of text. Garmin Coach still uses far less than uploading files to the
chat, because Claude only requests the data it needs (activity summary, laps, weekly totals) already aggregated.
For regular use the Pro plan is the practical choice (Anthropic states at least five times the Free usage per
session). With any plan: start a new chat for each analysis, group questions in one message, and ask for summaries
and laps before per-second series.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Windows: install or start blocked by **Smart App Control** | The extension runs on Python: at install time Claude Desktop creates a Python environment under the user's AppData, and its `python.exe` and compiled libraries (`.pyd`) are unsigned, so Smart App Control blocks them. For now the extension needs Smart App Control off (Windows Security → App & browser control → Smart App Control settings); re-enabling it will most likely block the extension again at start-up. Since the April 2026 Windows 11 update it can be turned back on without reinstalling Windows. The Docker option is not affected on the server side. |
| `sync_status`: `auth_required`, *Personal API rejected the key* | Key expired, revoked or mistyped. Create a new one and update it (extension settings or `.env`). |
| `sync_status`: `network_error` | No internet connection, or a firewall blocks `personal.connectapi.garmin.com`. |
| Claude doesn't use the tools | Check the extension is enabled (Settings → Extensions) and start a new chat. |
| Claude says workouts need write access | Expected with the extension and with Docker without the community module (official API is read-only). |
| Connector / mcp-remote: *401 … missing or wrong MCP token* | The token in Claude Desktop differs from the one the server uses. `docker compose exec garmin-coach printenv MCP_TOKEN` shows the server's; after editing `.env` run `docker compose up -d`. |
| Manual config: `npx` not found / *No executable file* | Node.js missing, or Claude can't find it: use the full path of `npx` (see above). Or use the connector extension. |
| Claude: *"Unexpected non-whitespace character after JSON"* | Manual config only: the block is outside the main `{ }` of `claude_desktop_config.json`. |
| `429` warnings during `login` (community module) | Normal if it ends with `Login OK`. If it fails, wait an hour: Garmin rate-limits login attempts per IP. |
| `curl .../healthz` returns `unauthorized` | Wrong path: only `/healthz` is open without token. |
| A change in `.env` has no effect | Use `docker compose up -d`, not `restart`. |

---

## Building the extensions

```bash
./scripts/build-mcpb.sh      # needs uv and Node.js; outputs dist/*.mcpb
```

The GitHub workflow in `.github/workflows/release.yml` builds both files and attaches them to the release when a
`v*` tag is pushed.

---

## Data, privacy and security

- Your data stays on your computer (extension) or your server (Docker): SQLite database, original FIT files,
  tokens, your notes. Nothing is sent anywhere except the requests to Garmin.
- The extension stores the Garmin key in Claude Desktop's secure settings. With Docker the key is in `.env`
  (excluded by `.gitignore`) and tokens are in `data/tokens/`: protect them like passwords.
- The Docker MCP endpoint is plain HTTP protected by a token: **keep it on your LAN** (or behind a VPN).
- `query_sql` opens the database read-only. The only writes Claude can make are annotations and notes in the local
  archive and, with the Docker community module and after your confirmation, workouts in Garmin Connect.

---

## Limitations and disclaimer

- This project is **not affiliated with or endorsed by Garmin**.
- The official Personal API is **read-only** and meant for personal use with your own account.
  It does not expose per-lap grade-adjusted pace, shoes or per-activity VO2max.
- Write access relies on the unofficial API through the community module: Garmin may change it at any time.
  Your local archive stays available even if that happens.
- Workouts: running only for now (no strength, cycling or swimming).
- Works with Claude Desktop (macOS, Windows). Not from the Claude mobile app or claude.ai on the web.
- This is just a personal project that I wanted to share with the community. Enjoy!

---

## Credits

| Project | Role | License |
|---|---|---|
| [garmin-connect-personal-api-python](https://github.com/garmin/connect-personal-api-python) by Garmin | Official Personal API client (read-only data source) | Apache-2.0 |
| [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) by cyberjunky | Optional community module (write access, Docker) | MIT |
| [fitdecode](https://github.com/polyvertex/fitdecode) by polyvertex | FIT file parsing | MIT |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | MCP server | MIT |
| [Uvicorn](https://github.com/encode/uvicorn) | ASGI server (Docker) | BSD-3-Clause |
| [mcp-remote](https://github.com/geelen/mcp-remote) by geelen | Bridge to the Docker server, bundled in the connector extension | MIT |
| [MCPB](https://github.com/modelcontextprotocol/mcpb) | Claude Desktop extension format and packaging tool | MIT |

Full list, including transitive dependencies and trademark notices: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

[MIT](LICENSE)
