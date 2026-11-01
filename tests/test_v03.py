"""0.3: extension mode, athlete notes, auth middleware, cross-process lock."""
import asyncio
import importlib


def _reload(tmp_path, monkeypatch, **env):
    for k in ("GC_RUNTIME", "GC_DATA_PARENT", "DATA_DIR", "ENABLE_GARMINCONNECT", "GARMIN_PERSONAL_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from app import config, db, garmin, official, sync, server
    for m in (config, db, garmin, official, sync, server):
        importlib.reload(m)
    return config, server, sync


def _call(server, name, args):
    res = asyncio.run(server.mcp.call_tool(name, args))
    return (res[0] if isinstance(res, tuple) else res)[0].text


def test_extension_data_folder_and_write_message(tmp_path, monkeypatch):
    config, server, _ = _reload(tmp_path, monkeypatch, GC_RUNTIME="extension", GC_DATA_PARENT=str(tmp_path))
    assert config.DATA_DIR == tmp_path / "Garmin Coach"
    out = _call(server, "list_workouts", {})
    assert "not available in the Claude Desktop extension" in out
    assert "not available in the desktop extension" in _call(server, "sync_status", {})


def test_athlete_notes(tmp_path, monkeypatch):
    _, server, _ = _reload(tmp_path, monkeypatch)
    assert "No athlete notes" in _call(server, "get_athlete_notes", {})
    _call(server, "update_athlete_notes", {"notes": "Max HR 190"})
    _call(server, "update_athlete_notes", {"notes": "Cadence 172-176"})
    assert _call(server, "get_athlete_notes", {}) == "Max HR 190\nCadence 172-176"
    _call(server, "update_athlete_notes", {"notes": "Only this", "mode": "replace"})
    assert _call(server, "get_athlete_notes", {}) == "Only this"


def test_auth_middleware(tmp_path, monkeypatch):
    _, server, _ = _reload(tmp_path, monkeypatch, MCP_TOKEN='"secret"')
    sent = []

    async def app(scope, receive, send):
        sent.append("app")

    mw = server.BearerAuth(app, server.config.MCP_TOKEN)

    async def run(path, headers=()):
        msgs = []

        async def send(m):
            msgs.append(m)
        await mw({"type": "http", "path": path, "headers": list(headers)}, None, send)
        return msgs

    assert asyncio.run(run("/.well-known/oauth-authorization-server"))[0]["status"] == 404
    r = asyncio.run(run("/mcp"))
    assert r[0]["status"] == 401 and b"MCP_TOKEN" in r[1]["body"]
    asyncio.run(run("/mcp", [(b"authorization", b"Bearer secret")]))  # quotes stripped from .env value
    assert sent == ["app"]


def test_cross_process_lock(tmp_path, monkeypatch):
    _, _, sync = _reload(tmp_path, monkeypatch, GARMIN_PERSONAL_API_KEY="k")
    from app import db
    db.init()
    import sqlite3
    import time
    c = sqlite3.connect(tmp_path / "garmin.db")
    c.execute("INSERT INTO sync_lock (id, owner, until) VALUES (1, 'other-process', ?)", (time.time() + 600,))
    c.commit()
    res = sync.run()
    assert res["status"] == "busy" and "another server process" in res["message"]
    assert sync.sync_running_elsewhere()
    c.execute("UPDATE sync_lock SET until=?", (time.time() - 1,))  # stale lock is taken over
    c.commit()
    assert not sync.sync_running_elsewhere()
