"""0.5: real Personal API layouts (daily summaries v2, weight with previous/next references), sleep, HRV."""
from tests import test_v04 as base

# trimmed from a real response (Nov 2026)
DAILY_V2 = [{"data": [{
    "uuid": "x", "userProfilePk": 1, "calendarDate": "2026-11-01", "source": "garmin",
    "movement": {"steps": {"goal": 12300, "value": 25337, "distanceInMeters": 22558.0},
                 "floorsAscended": {"goal": 999, "value": 72}},
    "calories": {"burnedResting": 1886, "burnedActive": 1254, "burnedTotal": 3140},
    "heartRate": {"minValue": 56, "maxValue": 175, "restingValue": 64},
    "intensityMinutes": {"goal": 150, "moderate": 28, "vigorous": 99},
    "stress": {"avgLevel": 39, "maxLevel": 98},
    "bodyBattery": {"minValue": 5, "maxValue": 36, "chargedValue": 31, "drainedValue": 31},
    "respiration": {"avgValue": 18}, "pulseOx": {"avgValue": 93, "minValue": 82},
}]}]

WEIGHT_REAL = {
    "dailyWeightSummaries": [{
        "summaryDate": "2026-10-11",
        "latestWeight": {"samplePk": 10, "calendarDate": "2026-10-11", "weight": 67500.0, "sourceType": "MANUAL"},
        "allWeightMetrics": [{"samplePk": 10, "calendarDate": "2026-10-11", "weight": 67500.0,
                              "sourceType": "MANUAL"}],
    }],
    "totalAverage": {"weight": 67550.0},
    "previousDateWeight": {"calendarDate": "2026-09-30", "weight": 67800.0},
    "nextDateWeight": {"calendarDate": "2026-11-01", "weight": 67500.0},
}

SLEEP = [{"calendarDate": "2026-11-02", "sleepTimeSeconds": 25200, "deepSleepSeconds": 5400,
          "remSleepSeconds": 6000, "sleepScores": {"overall": {"value": 78}}, "sleepLevels": [{"x": 1}],
          "id": 5, "sleepStartTimestampGMT": 1}]
HRV = {"hrvSummaries": [{"calendarDate": "2026-11-02", "lastNightAvg": 41, "weeklyAvg": 44,
                         "baseline": {"balancedLow": 39, "balancedUpper": 50}, "status": "BALANCED"}]}


class Fake(base.FakeOfficial):
    def daily_summaries(self, a, b):
        return DAILY_V2

    def weight_measurements(self, a, b):
        return WEIGHT_REAL

    def sleep_summaries(self, a, b):
        return SLEEP

    def hrv_summaries(self, a, b):
        return HRV


def _server(tmp_path, monkeypatch):
    server = base._setup(tmp_path, monkeypatch)
    from app import official
    monkeypatch.setattr(official, "Client", Fake)
    return server


def test_daily_v2_layout(tmp_path, monkeypatch):
    s = _server(tmp_path, monkeypatch)
    out = base._call(s, "get_daily_summary", {"start_date": "2026-11-01", "end_date": "2026-11-01"})
    assert "1 days" in out
    assert "2026-11-01,3140,1254,1886,25337,22.6,72,64,56,175,39,98,36,5,31,31,28,99,18,93,82" in out


def test_weight_skips_references_and_duplicates(tmp_path, monkeypatch):
    s = _server(tmp_path, monkeypatch)
    out = base._call(s, "get_body_composition", {"start_date": "2026-10-01", "end_date": "2026-10-31"})
    assert out.startswith("1 measurements")
    assert "2026-10-11,67.5,MANUAL" in out
    assert "2026-09-30" not in out and "2026-11-01" not in out


def test_sleep_and_hrv(tmp_path, monkeypatch):
    s = _server(tmp_path, monkeypatch)
    out = base._call(s, "get_sleep", {"start_date": "2026-11-01", "end_date": "2026-11-03"})
    assert "sleepTime_min" in out and "420" in out and "sleepScores.overall.value" in out
    assert "sleepLevels" not in out and "Timestamp" not in out
    out = base._call(s, "get_hrv", {"start_date": "2026-11-01", "end_date": "2026-11-03"})
    assert "lastNightAvg" in out and "BALANCED" in out and "baseline.balancedLow" in out


def test_garmin_zones_format():
    from app import wellness
    real = [{"trainingMethod": "CUSTOM", "zone1Floor": 120, "zone2Floor": 158, "zone3Floor": 167,
             "zone4Floor": 175, "zone5Floor": 182, "maxHeartRateUsed": 191, "sport": "DEFAULT"}]
    out = wellness.format_hr_zones(real)
    assert "Z1 120-157 | Z2 158-166 | Z3 167-174 | Z4 175-181 | Z5 >=182" in out
    assert "thresholds for set_hr_zones: 158,167,175,182" in out


def test_sleep_drops_score_ranges():
    from app import wellness
    rows = wellness.flatten_days([{"calendarDate": "2026-11-02", "ageGroup": "ADULT",
                                   "sleepScores": {"totalDuration": {"qualifierKey": "FAIR", "optimalStart": 28200}}}])
    assert rows == [{"date": "2026-11-02", "sleepScores.totalDuration.qualifierKey": "FAIR"}]
