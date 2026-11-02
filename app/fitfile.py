"""Parsing of original FIT files (laps and per-second records)."""
from __future__ import annotations

import io
import zipfile
from datetime import datetime
from pathlib import Path

import fitdecode

SEMI_TO_DEG = 180.0 / 2**31


def extract_fit(blob: bytes) -> bytes:
    """Garmin "ORIGINAL" download is a zip containing the .fit file."""
    if blob[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".fit")]
            if not names:
                raise ValueError("zip without a .fit file")
            return z.read(names[0])
    return blob


def _v(msg: fitdecode.FitDataMessage, *names):
    for n in names:
        if msg.has_field(n):
            val = msg.get_value(n)
            if val is not None and not isinstance(val, tuple):
                return val
    return None


# Sports whose FIT cadence is in strides/min (one leg): shown as steps/min (x2).
# Cycling and other sports keep the FIT value as is (rpm).
STEP_SPORTS = {"running", "walking", "hiking", "training", "generic", "trail_running"}


def _cad(msg, bases: tuple[str, ...], frac: str):
    """Raw FIT cadence (+ fraction), unit as recorded by the device."""
    c = _v(msg, *bases)
    if c is None:
        return None
    return c + (_v(msg, frac) or 0.0)


def _scale(x, k):
    return None if x is None else round(x * k, 1)


def _mul(x, k, nd=2):
    return None if x is None else round(x * k, nd)


def parse(path: Path | str) -> dict:
    laps, records, session = [], {}, {}
    t0: datetime | None = None
    with fitdecode.FitReader(str(path), check_crc=fitdecode.CrcCheck.DISABLED) as reader:
        for frame in reader:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue
            name = frame.name
            if name == "record":
                ts = _v(frame, "timestamp")
                if ts is None:
                    continue
                if t0 is None:
                    t0 = ts
                t = int((ts - t0).total_seconds())
                lat, lon = _v(frame, "position_lat"), _v(frame, "position_long")
                cad = _cad(frame, ("cadence",), "fractional_cadence")
                records[t] = dict(
                    t_s=t,
                    distance_m=_v(frame, "distance"),
                    speed=_v(frame, "enhanced_speed", "speed"),
                    hr=_v(frame, "heart_rate"),
                    cadence=cad,
                    altitude=_v(frame, "enhanced_altitude", "altitude"),
                    power=_v(frame, "power"),
                    gct_ms=_v(frame, "stance_time"),
                    gct_bal_left=_v(frame, "stance_time_balance"),
                    vo_cm=_mul(_v(frame, "vertical_oscillation"), 0.1),
                    vratio=_v(frame, "vertical_ratio"),
                    step_len_m=_mul(_v(frame, "step_length"), 0.001, 3),
                    temp=_v(frame, "temperature"),
                    lat=_mul(lat, SEMI_TO_DEG, 6),
                    lon=_mul(lon, SEMI_TO_DEG, 6),
                )
            elif name == "lap":
                laps.append(frame)
            elif name == "sport" and "sport" not in session:
                session["sport"] = _v(frame, "sport")
            elif name == "session" and not session.get("start_time"):
                session = {
                    "sport": _v(frame, "sport") or session.get("sport"),
                    "sub_sport": _v(frame, "sub_sport"),
                    "start_time": _v(frame, "start_time"),
                }

    start = session.get("start_time") or t0
    lap_rows = []
    for i, m in enumerate(laps, start=1):
        st = _v(m, "start_time")
        lap_rows.append(dict(
            lap_index=i,
            start_time=st.isoformat() if st else None,
            start_offset_s=(st - start).total_seconds() if (st and start) else None,
            trigger=_v(m, "lap_trigger"),
            intensity=_v(m, "intensity"),
            elapsed_s=_v(m, "total_elapsed_time"),
            timer_s=_v(m, "total_timer_time"),
            distance_m=_v(m, "total_distance"),
            avg_speed=_v(m, "enhanced_avg_speed", "avg_speed"),
            max_speed=_v(m, "enhanced_max_speed", "max_speed"),
            avg_hr=_v(m, "avg_heart_rate"),
            max_hr=_v(m, "max_heart_rate"),
            avg_cadence=_cad(m, ("avg_running_cadence", "avg_cadence"), "avg_fractional_cadence"),
            max_cadence=_cad(m, ("max_running_cadence", "max_cadence"), "max_fractional_cadence"),
            avg_power=_v(m, "avg_power"),
            max_power=_v(m, "max_power"),
            gct_ms=_v(m, "avg_stance_time"),
            gct_bal_left=_v(m, "avg_stance_time_balance"),
            vo_cm=_mul(_v(m, "avg_vertical_oscillation"), 0.1),
            vratio=_v(m, "avg_vertical_ratio"),
            step_len_m=_mul(_v(m, "avg_step_length"), 0.001, 3),
            ascent_m=_v(m, "total_ascent"),
            descent_m=_v(m, "total_descent"),
            calories=_v(m, "total_calories"),
            avg_temp=_v(m, "avg_temperature"),
        ))
    sport = str(session.get("sport") or (laps and _v(laps[0], "sport")) or "running")
    k = 2 if sport in STEP_SPORTS else 1
    for row in lap_rows:
        row["avg_cadence"], row["max_cadence"] = _scale(row["avg_cadence"], k), _scale(row["max_cadence"], k)
    recs = list(records.values())
    for r in recs:
        r["cadence"] = _scale(r["cadence"], k)
    session["sport"] = sport
    return {"session": session, "laps": lap_rows, "records": recs}
