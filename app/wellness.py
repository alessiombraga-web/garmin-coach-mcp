"""Body composition and daily summaries from the official Garmin Personal API (read-only, live calls).

The response layouts are not formally documented: values are located by field name anywhere in the JSON,
so the parsing keeps working if Garmin nests them differently.
"""
from __future__ import annotations

import re

from datetime import date, datetime, timedelta, timezone

CHUNK_DAYS = 28  # requests are split into windows of this size

# output column -> candidate field names (case-insensitive leaf names)
WEIGHT_FIELDS = {
    "weight_kg": ["weight"],
    "bmi": ["bmi"],
    "body_fat_pct": ["bodyFat", "bodyFatPercentage"],
    "body_water_pct": ["bodyWater", "bodyWaterPercentage"],
    "muscle_mass_kg": ["muscleMass", "skeletalMuscleMass"],
    "bone_mass_kg": ["boneMass"],
    "visceral_fat": ["visceralFat", "visceralFatRating"],
    "metabolic_age": ["metabolicAge"],
    "source": ["sourceType"],
}
MASS_FIELDS = {"weight_kg", "muscle_mass_kg", "bone_mass_kg"}  # grams in Garmin payloads

DAILY_FIELDS = {
    "total_kcal": ["totalKilocalories", "totalCalories"],
    "active_kcal": ["activeKilocalories", "activeCalories"],
    "resting_kcal": ["bmrKilocalories", "bmrCalories", "restingKilocalories"],
    "steps": ["totalSteps", "steps"],
    "distance_km": ["totalDistanceMeters", "totalDistance"],
    "resting_hr": ["restingHeartRate", "restingHeartRateInBeatsPerMinute"],
    "min_hr": ["minHeartRate", "minHeartRateInBeatsPerMinute"],
    "max_hr": ["maxHeartRate", "maxHeartRateInBeatsPerMinute"],
    "avg_stress": ["averageStressLevel", "averageStress"],
    "body_battery_max": ["bodyBatteryHighestValue", "highestBodyBattery"],
    "body_battery_min": ["bodyBatteryLowestValue", "lowestBodyBattery"],
    "moderate_min": ["moderateIntensityMinutes", "moderateIntensityDurationInSeconds"],
    "vigorous_min": ["vigorousIntensityMinutes", "vigorousIntensityDurationInSeconds"],
}
DATE_FIELDS = ["calendarDate", "summaryDate", "date", "measurementDate", "timestampGMT"]


def windows(start: str, end: str, days: int = CHUNK_DAYS):
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    if b < a:
        a, b = b, a
    while a <= b:
        c = min(a + timedelta(days=days - 1), b)
        yield a.isoformat(), c.isoformat()
        a = c + timedelta(days=1)


def _dicts(obj):
    """All dicts nested anywhere in a JSON value."""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _dicts(v)


def _get_named(d: dict, names: list[str]):
    low = {k.lower(): v for k, v in d.items()}
    for n in names:
        v = low.get(n.lower())
        if v is not None and not isinstance(v, (dict, list)):
            return n, v
    return None, None


def _get(d: dict, names: list[str]):
    return _get_named(d, names)[1]


def _day(d: dict) -> str | None:
    v = _get(d, DATE_FIELDS)
    if v is None:
        return None
    if isinstance(v, (int, float)):  # epoch milliseconds
        return datetime.fromtimestamp(v / 1000, tz=timezone.utc).date().isoformat()
    return str(v)[:10]


def _path(d: dict, path: str):
    """Value at a dotted path (case-insensitive keys), or None."""
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        low = {k.lower(): v for k, v in cur.items()}
        cur = low.get(part.lower())
    return None if isinstance(cur, (dict, list)) else cur


def _in_range(day: str, start: str | None, end: str | None) -> bool:
    return (not start or day >= start) and (not end or day <= end)


def parse_weights(payloads: list, start: str | None = None, end: str | None = None) -> list[dict]:
    """One row per real measurement (dicts carrying a samplePk), deduplicated, inside [start, end]."""
    rows, seen = [], set()
    for p in payloads:
        for d in _dicts(p):
            w = _get(d, ["weight"])
            day = _day(d)
            pk = _get(d, ["samplePk"])
            if not isinstance(w, (int, float)) or not day or pk is None:
                continue  # skips averages and previous/next-date references
            if pk in seen or not _in_range(day, start, end):
                continue
            seen.add(pk)
            row = {"date": day}
            for col, names in WEIGHT_FIELDS.items():
                v = _get(d, names)
                if isinstance(v, (int, float)) and col in MASS_FIELDS and v > 500:
                    v = v / 1000.0  # grams -> kg
                row[col] = round(v, 2) if isinstance(v, float) else v
            rows.append(row)
    return sorted(rows, key=lambda r: r["date"])


# Personal API v2 daily summaries: nested layout (verified on a real account, Nov 2026)
DAILY_PATHS = {
    "total_kcal": "calories.burnedTotal",
    "active_kcal": "calories.burnedActive",
    "resting_kcal": "calories.burnedResting",
    "steps": "movement.steps.value",
    "distance_km": "movement.steps.distanceInMeters",
    "floors_up": "movement.floorsAscended.value",
    "resting_hr": "heartRate.restingValue",
    "min_hr": "heartRate.minValue",
    "max_hr": "heartRate.maxValue",
    "avg_stress": "stress.avgLevel",
    "max_stress": "stress.maxLevel",
    "body_battery_max": "bodyBattery.maxValue",
    "body_battery_min": "bodyBattery.minValue",
    "body_battery_charged": "bodyBattery.chargedValue",
    "body_battery_drained": "bodyBattery.drainedValue",
    "moderate_min": "intensityMinutes.moderate",
    "vigorous_min": "intensityMinutes.vigorous",
    "avg_respiration": "respiration.avgValue",
    "avg_spo2": "pulseOx.avgValue",
    "min_spo2": "pulseOx.minValue",
}


def _daily_row(d: dict, day: str) -> dict:
    row = {"date": day}
    for col, path in DAILY_PATHS.items():
        v = _path(d, path)
        if v is None and col in DAILY_FIELDS:  # older/flat layouts
            name, v = _get_named(d, DAILY_FIELDS[col])
            if isinstance(v, (int, float)) and not isinstance(v, bool) and name and name.lower().endswith("seconds"):
                v = v / 60.0
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if col == "distance_km":
                v = v / 1000.0
            v = round(v, 1) if isinstance(v, float) else v
        else:
            v = None
        row[col] = v
    return row


def parse_daily(payloads: list, start: str | None = None, end: str | None = None) -> list[dict]:
    """One row per calendar day (the most complete record for that day wins)."""
    best: dict[str, dict] = {}
    for p in payloads:
        for d in _dicts(p):
            day = _get(d, ["calendarDate", "summaryDate"])
            if not day:
                continue
            day = str(day)[:10]
            if not _in_range(day, start, end):
                continue
            row = _daily_row(d, day)
            filled = sum(1 for k, v in row.items() if k != "date" and v is not None)
            if filled and filled >= sum(1 for k, v in best.get(day, {}).items() if k != "date" and v is not None):
                best[day] = row
    return [best[k] for k in sorted(best)]


# ---- generic per-day flattening (sleep, HRV and other endpoints whose layout is not pinned down)
_NOISE = re.compile(r"(^id$|pk$|uuid|userprofile|deviceid|timestamp|gmt$|local$|version|^date$|calendardate"
                    r"|summarydate|^source|feedback|^msg|messages?$)", re.I)


def _flatten(d: dict, prefix: str = "", out: dict | None = None) -> dict:
    out = {} if out is None else out
    for k, v in d.items():
        key = f"{prefix}{k}"
        if _NOISE.search(k):
            continue
        if isinstance(v, dict):
            _flatten(v, key + ".", out)
        elif isinstance(v, list):
            continue  # per-minute/epoch samples: too verbose for a daily table
        elif isinstance(v, bool) or v is None or v == "":
            continue
        elif isinstance(v, (int, float)):
            low = k.lower()
            if low.endswith("inseconds") or low.endswith("seconds"):
                key, v = re.sub(r"(?i)(in)?seconds$", "", key) + "_min", v / 60.0
            elif low.endswith("inmillis") or low.endswith("millis"):
                key, v = re.sub(r"(?i)(in)?millis$", "", key) + "_min", v / 60000.0
            out[key] = round(v, 1) if isinstance(v, float) else v
        else:
            out[key] = str(v)[:40]
    return out


def flatten_days(payloads: list, start: str | None = None, end: str | None = None) -> list[dict]:
    """One row per calendar day: the outermost dicts that carry a calendar date, flattened to dotted keys."""
    best: dict[str, dict] = {}

    def walk(obj):
        if isinstance(obj, dict):
            day = _get(obj, ["calendarDate", "summaryDate"])
            if day:
                day = str(day)[:10]
                if _in_range(day, start, end):
                    row = _flatten(obj)
                    if len(row) > len(best.get(day, {})) - 1:
                        best[day] = {"date": day, **row}
                return  # don't descend: nested dicts are already flattened
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for p in payloads:
        walk(p)
    return [best[k] for k in sorted(best)]


def table(rows: list[dict], max_cols: int = 40) -> tuple[list[str], list[list]]:
    """Columns ordered by how many days have them (most common first), capped."""
    counts: dict[str, int] = {}
    for r in rows:
        for k in r:
            if k != "date":
                counts[k] = counts.get(k, 0) + 1
    cols = ["date"] + [k for k, _ in sorted(counts.items(), key=lambda kv: -kv[1])][:max_cols]
    return cols, [[r.get(c, "") for c in cols] for r in rows]
