"""Body composition and daily summaries from the official Garmin Personal API (read-only, live calls).

The response layouts are not formally documented: values are located by field name anywhere in the JSON,
so the parsing keeps working if Garmin nests them differently.
"""
from __future__ import annotations

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


def parse_weights(payloads: list) -> list[dict]:
    """One row per measurement (dedup), sorted by date."""
    rows, seen = [], set()
    for p in payloads:
        for d in _dicts(p):
            w = _get(d, ["weight"])
            day = _day(d)
            if not isinstance(w, (int, float)) or not day:
                continue
            row = {"date": day}
            for col, names in WEIGHT_FIELDS.items():
                v = _get(d, names)
                if isinstance(v, (int, float)) and col in MASS_FIELDS and v > 500:
                    v = v / 1000.0  # grams -> kg
                row[col] = round(v, 2) if isinstance(v, float) else v
            key = (d.get("samplePk") or d.get("timestampGMT") or d.get("date"), day, row["weight_kg"])
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return sorted(rows, key=lambda r: r["date"])


def parse_daily(payloads: list) -> list[dict]:
    """One row per calendar day (the most complete dict for that day wins)."""
    best: dict[str, dict] = {}
    for p in payloads:
        for d in _dicts(p):
            day = _day(d)
            if not day:
                continue
            row = {"date": day}
            for col, names in DAILY_FIELDS.items():
                name, v = _get_named(d, names)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if col == "distance_km":
                        v = v / 1000.0
                    if name and name.lower().endswith("seconds"):
                        v = v / 60.0
                    v = round(v, 1) if isinstance(v, float) else v
                else:
                    v = None
                row[col] = v
            filled = sum(1 for k, v in row.items() if k != "date" and v is not None)
            if filled and filled >= sum(1 for k, v in best.get(day, {}).items() if k != "date" and v is not None):
                best[day] = row
    return [best[k] for k in sorted(best)]
