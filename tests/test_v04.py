"""0.4: dated HR zones from chat, body composition and daily summary tools."""
import asyncio
import importlib
import sqlite3

WEIGHT_PAYLOAD = {
    "dailyWeightSummaries": [{
        "summaryDate": "2026-11-01", "numOfWeightEntries": 1,
        "latestWeight": {"samplePk": 1, "date": 1761984000000, "calendarDate": "2026-11-01",
                         "weight": 72500.0, "bmi": 24.2, "bodyFat": 17.8, "bodyWater": 58.9,
                         "boneMass": 3300, "muscleMass": 33100, "sourceType": "INDEX_SCALE"},
        "allWeightMetrics": [{"samplePk": 1, "date": 1761984000000, "calendarDate": "2026-11-01",
                              "weight": 72500.0, "bmi": 24.2, "bodyFat": 17.8, "bodyWater": 58.9,
                              "boneMass": 3300, "muscleMass": 33100, "sourceType": "INDEX_SCALE"}],
    }, {
        "summaryDate": "2026-11-02",
        "allWeightMetrics": [{"samplePk": 2, "calendarDate": "2026-11-02", "weight": 72300.0,
                              "sourceType": "MANUAL"}],
    }],
    "totalAverage": {"weight": 72400.0},
}
DAILY_PAYLOAD = {"data": [
    {"calendarDate": "2026-11-01", "totalKilocalories": 2890, "activeKilocalories": 980,
     "bmrKilocalories": 1910, "totalSteps": 15234, "restingHeartRate": 48, "averageStressLevel": 27},
    {"calendarDate": "2026-11-02", "totalKilocalories": 2210, "bmrKilocalories": 1910, "totalSteps": 6012},
]}


class FakeOfficial:
    def weight_measurements(self, a, b):
        return WEIGHT_PAYLOAD

    def daily_summaries(self, a, b):
        return DAILY_PAYLOAD

    def close(self):
        pass


def _setup(tmp_path, monkeypatch, **env):
    for k in ("GC_RUNTIME", "GC_DATA_PARENT", "HR_BANDS"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("REQUEST_DELAY_S", "0")
    monkeypatch.setenv("GARMIN_PERSONAL_API_KEY", "k")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from app import config, db, official, wellness, server
    for m in (config, db, official, wellness, server):
        importlib.reload(m)
    monkeypatch.setattr(official, "Client", FakeOfficial)
    db.init()
    return server


def _call(server, name, args):
    res = asyncio.run(server.mcp.call_tool(name, args))
    return (res[0] if isinstance(res, tuple) else res)[0].text


def _add_run(tmp_path, aid, day, hr):
    c = sqlite3.connect(tmp_path / "garmin.db")
    c.execute("INSERT INTO activities(activity_id,start_local,name,type_key,distance_m,duration_s,"
              "avg_speed,has_details) VALUES (?,?,?,?,1000,600,2.8,1)", (aid, f"{day} 08:00:00", "Run", "running"))
    c.execute("INSERT INTO laps(activity_id,lap_index,start_offset_s,elapsed_s,timer_s,distance_m) "
              "VALUES (?,1,0,600,600,1000)", (aid,))
    c.executemany("INSERT INTO records(activity_id,t_s,hr) VALUES (?,?,?)", [(aid, t, hr) for t in range(601)])
    c.commit()


def test_zones_from_chat_are_dated(tmp_path, monkeypatch):
    server = _setup(tmp_path, monkeypatch, HR_BANDS="135,150,160,170")
    _add_run(tmp_path, 1, "2026-08-10", 162)
    _add_run(tmp_path, 2, "2026-10-20", 162)
    assert "Zones not saved" in _call(server, "set_hr_zones", {"thresholds": "170,160"})
    out = _call(server, "set_hr_zones", {"thresholds": "158,166,170,175", "valid_from": "2026-10-01",
                                         "note": "test 30'"})
    assert "activities from 2026-10-01" in out and "Z2 158-165" in out
    old = _call(server, "get_activity", {"activity_id": "1"})
    new = _call(server, "get_activity", {"activity_id": "2"})
    assert "starting zones" in old and "Z4 160-169: 10:00" in old      # August: settings zones
    assert "valid from 2026-10-01" in new and "Z2 158-165: 10:00" in new  # October: saved zones
    cur = _call(server, "get_activity", {"activity_id": "1", "zones": "current"})
    assert "Z2 158-165: 10:00" in cur
    summ = _call(server, "training_summary", {"weeks": 20, "end_date": "2026-10-25"})
    assert summ.startswith("HR zones used") and "Z5" in summ.splitlines()[1]
    hist = _call(server, "get_hr_zones", {})
    assert "from 2026-10-01: 158,166,170,175 — test 30'" in hist
    import re
    zid = int(re.search(r"- id (\d+):", hist).group(1))
    assert "Deleted" in _call(server, "delete_hr_zones", {"zone_id": zid})
    assert "starting zones" in _call(server, "get_hr_zones", {}).splitlines()[0]


def test_zones_for_whole_history(tmp_path, monkeypatch):
    server = _setup(tmp_path, monkeypatch)
    _add_run(tmp_path, 1, "2025-01-10", 162)
    assert "whole history" in _call(server, "set_hr_zones", {"thresholds": "150 160 170 180", "valid_from": "all"})
    assert "Z3 160-169: 10:00" in _call(server, "get_activity", {"activity_id": "1"})


def test_body_composition(tmp_path, monkeypatch):
    server = _setup(tmp_path, monkeypatch)
    out = _call(server, "get_body_composition", {"start_date": "2026-10-01", "end_date": "2026-11-02"})
    lines = out.splitlines()
    assert lines[0].startswith("2 measurements")
    assert "2026-11-01,72.5,24.2,17.8,58.9,33.1,3.3" in out
    assert "2026-11-02,72.3" in out


def test_daily_summary(tmp_path, monkeypatch):
    server = _setup(tmp_path, monkeypatch)
    out = _call(server, "get_daily_summary", {"start_date": "2026-11-01", "end_date": "2026-11-02"})
    assert "date,total_kcal,active_kcal,resting_kcal,steps" in out
    assert "2026-11-01,2890,980,1910,15234" in out and ",48," in out


def test_wellness_needs_official_key(tmp_path, monkeypatch):
    server = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(server.config, "read_source", lambda: "garminconnect")
    assert "GARMIN_PERSONAL_API_KEY" in _call(server, "get_daily_summary", {})
