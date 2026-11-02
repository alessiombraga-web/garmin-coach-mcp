"""0.3.1: details for every sport, cadence units, sport filter, explanation for missing details."""
import asyncio
import importlib
import io
import zipfile
from pathlib import Path

HERE = Path(__file__).parent


def _zip(b):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("x_ACTIVITY.fit", b)
    return buf.getvalue()


ACTS = [
    {"activityId": 10, "startTimeLocal": "2026-11-01 09:00:00", "activityName": "Ride",
     "activityType": {"typeKey": "road_biking"}, "distance": 40000, "duration": 4800, "averageSpeed": 8.3},
    {"activityId": 11, "startTimeLocal": "2026-10-31 08:00:00", "activityName": "Run",
     "activityType": {"typeKey": "running"}, "distance": 157.6, "duration": 57, "averageSpeed": 2.77},
]
FILES = {10: (HERE / "sample_ride.fit").read_bytes(), 11: (HERE / "sample_run.fit").read_bytes()}


class FakeOfficial:
    def activities_since(self, start):
        return ACTS

    def download_activity(self, aid):
        return _zip(FILES[int(aid)])

    def activity_workouts(self, aid):
        return []

    def close(self):
        pass


def _setup(tmp_path, monkeypatch, **env):
    for k in ("GC_RUNTIME", "GC_DATA_PARENT", "ENABLE_GARMINCONNECT", "DETAIL_TYPE_MATCH"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("REQUEST_DELAY_S", "0")
    monkeypatch.setenv("GARMIN_PERSONAL_API_KEY", "k")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from app import config, db, fitfile, garmin, official, sync, server
    for m in (config, db, fitfile, garmin, official, sync, server):
        importlib.reload(m)
    monkeypatch.setattr(official, "Client", FakeOfficial)
    return sync, server


def _call(server, name, args):
    res = asyncio.run(server.mcp.call_tool(name, args))
    return (res[0] if isinstance(res, tuple) else res)[0].text


def test_cycling_details_and_units(tmp_path, monkeypatch):
    sync, server = _setup(tmp_path, monkeypatch)
    assert sync.run()["detailed"] == 2
    ride = _call(server, "get_activity", {"activity_id": "latest"})
    assert "Ride" in ride and "cad_rpm" in ride and "kmh" in ride
    assert ",68," in ride  # lap cadence in rpm, not doubled
    run = _call(server, "get_activity", {"activity_id": "latest", "type_filter": "run"})
    assert "'Run'" in run and "cad_spm" in run and ",167," in run
    series = _call(server, "get_activity_series", {"activity_id": "2026-11-01", "every_s": 60})
    assert series.startswith("t,km")


def test_excluded_type_is_explained(tmp_path, monkeypatch):
    sync, server = _setup(tmp_path, monkeypatch, DETAIL_TYPE_MATCH="run")
    sync.run()
    out = _call(server, "get_activity", {"activity_id": "latest", "type_filter": "biking"})
    assert "excluded by the DETAIL_TYPE_MATCH" in out and "not a limit of the Garmin API" in out
