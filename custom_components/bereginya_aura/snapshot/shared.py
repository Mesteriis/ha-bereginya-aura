"""Shared helpers for Beregynya AURA snapshot assembly."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from homeassistant.util import dt as dt_util

from ..const import SOURCE_KEY_ALIASES
from .constants import *  # noqa: F403


def _normalize_timezone_token(raw_token: str) -> str | None:
    """Normalize timezone token from format UTC+-N to UTC+-HH."""
    token = raw_token.strip().upper().replace(" ", "")
    if not token:
        return None
    match = _UTC_TOKEN_PATTERN.fullmatch(token)
    if not match:
        return None
    sign = match.group(1)
    hour = int(match.group(2))
    if hour > 14:
        return None
    return f"UTC{sign}{hour:02d}"


def _timezone_token_to_offset(token: str) -> str | None:
    """Convert UTC+HH token to +HH:MM offset."""
    normalized = _normalize_timezone_token(token)
    if normalized is None:
        return None
    sign = normalized[3]
    hour = int(normalized[4:])
    return f"{sign}{hour:02d}:00"

def _resolve_metric_id(source_key: str) -> str | None:
    """Map custom source keys to canonical entity IDs in transcript."""
    key = source_key.strip()
    if not key:
        return None
    if key.startswith("sensor."):
        return key
    return SOURCE_KEY_ALIASES.get(key)


def _build_url(base: str, params: dict[str, Any]) -> str:
    """Build URL with query string."""
    return f"{base}?{urlencode(params)}"


def _hourly_value(hourly: dict[str, Any], key: str, index: int, default: Any) -> Any:
    """Read a value from hourly arrays."""
    values = hourly.get(key)
    if not isinstance(values, list):
        return default
    if index < 0 or index >= len(values):
        return default
    value = values[index]
    if value is None:
        return default
    return value


def _safe_float(value: Any, default: float) -> float:
    """Convert value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int) -> int:
    """Convert value to int."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _optional_float(value: Any, digits: int | None = None) -> float | None:
    """Convert to float or return None."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if digits is None:
        return parsed
    return round(parsed, digits)


def _optional_int(value: Any) -> int | None:
    """Convert to int or return None."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _kmh_to_ms(value: float | None, digits: int = 1) -> float | None:
    """Convert km/h to m/s."""
    if value is None:
        return None
    return round(value / 3.6, digits)


def _ms_to_kmh(value: float | None, digits: int = 1) -> float | None:
    """Convert m/s to km/h."""
    if value is None:
        return None
    return round(value * 3.6, digits)


def _coerce_state_value(raw_state: str, template_value: Any) -> Any:
    """Coerce HA state string to shape of template value."""
    if template_value is None or template_value == "unavailable":
        lowered = raw_state.lower()
        if lowered in {"1", "true", "on", "yes"}:
            return True
        if lowered in {"0", "false", "off", "no"}:
            return False
        try:
            if "." in raw_state:
                return round(float(raw_state), 2)
            return int(raw_state)
        except (TypeError, ValueError):
            return raw_state
    if isinstance(template_value, bool):
        return raw_state.lower() in {"1", "true", "on", "yes"}
    if isinstance(template_value, int):
        return _safe_int(raw_state, template_value)
    if isinstance(template_value, float):
        return round(_safe_float(raw_state, template_value), 2)
    return raw_state


def _risk_from_index(index: int) -> str:
    """Map 0..100 index to compact risk buckets."""
    if index >= 80:
        return "very_high"
    if index >= 60:
        return "high"
    if index >= 35:
        return "moderate"
    if index >= 15:
        return "low"
    return "very_low"


def _alert_level_rank(level: str | None) -> int:
    """Map alert level text to comparable rank."""
    value = str(level or "").strip().lower()
    if value == "red":
        return 4
    if value == "orange":
        return 3
    if value == "green":
        return 2
    if value == "yellow":
        return 2
    return 1


def _noto_icon_bundle(emoji_code: str) -> dict[str, str]:
    """Return PNG/WebP/GIF icon URLs for a Noto Emoji code."""
    base = f"{_NOTO_EMOJI_BASE}/{emoji_code}/512"
    return {
        "emoji_code": emoji_code,
        "icon_url": f"{base}.png",
        "icon_webp_url": f"{base}.webp",
        "icon_gif_url": f"{base}.gif",
    }


def _weather_emoji_code(weather_code: int | None) -> str:
    """Map Open-Meteo weather code to an emoji icon code."""
    if weather_code is None:
        return "2601_fe0f"
    if weather_code == 0:
        return "1f31e"
    if weather_code in {1, 2}:
        return "1f329_fe0f"
    if weather_code in {3}:
        return "2601_fe0f"
    if weather_code in {45, 48}:
        return "1f300"
    if weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        return "1f327_fe0f"
    if weather_code in {71, 73, 75, 77, 85, 86}:
        return "2744_fe0f"
    if weather_code in {95, 96, 99}:
        return "1f329_fe0f"
    return "2601_fe0f"


def _metric_emoji_code(entity_id: str, weather_code: int | None) -> str | None:
    """Pick emoji icon code for a metric."""
    if entity_id in {"sensor.weather_summary", "sensor.weather_code"}:
        return _weather_emoji_code(weather_code)
    if entity_id.startswith("sensor.aura_"):
        if "_tracker_" in entity_id and entity_id.endswith("_uv_sed_today"):
            return "1f31e"
        if "_tracker_" in entity_id and entity_id.endswith("_uv_exposure_state"):
            return "1f4f1"
        if entity_id.endswith("_sunburn_time_min") or entity_id.endswith("_sunburn_risk"):
            return "1f31e"
        if entity_id.endswith("_heat_stress_index") or entity_id.endswith("_heat_stress_risk"):
            return "1f321_fe0f"
        if (
            entity_id.endswith("_daily_plan")
            or entity_id.endswith("_planner_mode")
            or entity_id.endswith("_best_hours_outdoor")
            or entity_id.endswith("_best_hours_beach")
        ):
            return "1f4c5"
        if entity_id.endswith("_pack_list"):
            return "1f392"
        if entity_id.endswith("_smart_notification"):
            return "1f514"
        if entity_id.endswith("_now_vs_3h"):
            return "23f3"
        if entity_id.endswith("_presence") or entity_id.endswith("_profile"):
            return "1f9d1"
    return _METRIC_ICON_EMOJI.get(entity_id)


def _weather_summary(temp_c: float, rain_prob: float) -> str:
    """Build text weather summary."""
    temp_i = int(round(temp_c))
    if rain_prob > 60:
        return f"Rainy, {temp_i} degC"
    if temp_c > 35:
        return f"Very hot, {temp_i} degC"
    if temp_c > 28:
        return f"Hot, {temp_i} degC"
    if temp_c > 20:
        return f"Warm, {temp_i} degC"
    if temp_c > 15:
        return f"Cool, {temp_i} degC"
    return f"Cold, {temp_i} degC"


def _dust_level(dust: float) -> str:
    """Classify Saharan dust level."""
    if dust >= 200:
        return "severe"
    if dust >= 100:
        return "high"
    if dust >= 50:
        return "moderate"
    if dust >= 20:
        return "light"
    return "normal"


def _allergy_index(pollen_total: float, dust: float, aqi: float) -> int:
    """Compute compact 0..100 allergy index."""
    score = pollen_total * 2.2 + max(dust - 15, 0) * 0.25 + max(aqi - 20, 0) * 0.6
    return max(0, min(100, int(round(score))))


def _asthma_risk(aqi: float, pm25: float, dust: float, pollen_total: float) -> str:
    """Classify asthma risk."""
    risk_score = (
        max(aqi - 20, 0) * 0.8
        + max(pm25 - 10, 0) * 1.4
        + max(dust - 20, 0) * 0.3
        + max(pollen_total - 20, 0) * 0.5
    )
    if risk_score >= 80:
        return "very_high"
    if risk_score >= 50:
        return "high"
    if risk_score >= 25:
        return "moderate"
    return "low"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute approximate distance between two points on Earth."""
    rad = math.pi / 180.0
    d_lat = (lat2 - lat1) * rad
    d_lon = (lon2 - lon1) * rad
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin(d_lon / 2) ** 2
    )
    return 6371.0 * (2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a))))


def _parse_cams_featureinfo_text(text: str) -> dict[str, Any] | None:
    """Parse CAMS WMS GetFeatureInfo text/plain payload."""
    if not isinstance(text, str) or not text.strip():
        return None

    line_match = _CAMS_VALUE_PATTERN.search(text)
    value: float | None = None
    unit = ""
    if line_match is not None:
        value = _optional_float(line_match.group(1))
        unit = str(line_match.group(2) or "").strip() or ""

    name_match = re.search(r"^Name:\s*(.+)$", text, re.MULTILINE)
    title_match = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
    dist_match = re.search(r"^Distance:\s*([-+]?\d+(?:\.\d+)?)\s*km", text, re.MULTILINE)
    grid_lat_match = re.search(
        r"^Grid point latitude:\s*([-+]?\d+(?:\.\d+)?)\s*$",
        text,
        re.MULTILINE,
    )
    grid_lon_match = re.search(
        r"^Grid point longitude:\s*([-+]?\d+(?:\.\d+)?)\s*$",
        text,
        re.MULTILINE,
    )

    return {
        "name": str(name_match.group(1)).strip() if name_match is not None else "",
        "title": str(title_match.group(1)).strip() if title_match is not None else "",
        "value": value,
        "unit": unit,
        "distance_km": (
            _optional_float(dist_match.group(1), 3) if dist_match is not None else None
        ),
        "grid_lat": (
            _optional_float(grid_lat_match.group(1), 5)
            if grid_lat_match is not None
            else None
        ),
        "grid_lon": (
            _optional_float(grid_lon_match.group(1), 5)
            if grid_lon_match is not None
            else None
        ),
        "raw": text.strip(),
    }


def _parse_hourly_time(raw_time: Any, tz: Any) -> datetime | None:
    """Parse hourly timestamp and normalize to Home Assistant timezone."""
    if not isinstance(raw_time, str):
        return None
    parsed = dt_util.parse_datetime(raw_time)
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(raw_time)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def _solar_elevation_degrees(
    at_local: datetime,
    *,
    latitude: float,
    longitude: float,
) -> float:
    """Estimate solar elevation angle using NOAA approximation."""
    if at_local.tzinfo is None:
        at_local = at_local.replace(tzinfo=UTC)

    day_of_year = at_local.timetuple().tm_yday
    hour = at_local.hour + at_local.minute / 60.0 + at_local.second / 3600.0
    gamma = 2.0 * math.pi / 365.0 * (day_of_year - 1 + (hour - 12.0) / 24.0)

    declination = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2.0 * gamma)
        + 0.000907 * math.sin(2.0 * gamma)
        - 0.002697 * math.cos(3.0 * gamma)
        + 0.00148 * math.sin(3.0 * gamma)
    )
    equation_of_time = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2.0 * gamma)
        - 0.040849 * math.sin(2.0 * gamma)
    )

    utc_offset = at_local.utcoffset()
    offset_hours = utc_offset.total_seconds() / 3600.0 if utc_offset is not None else 0.0
    true_solar_minutes = (
        hour * 60.0 + equation_of_time + 4.0 * longitude - 60.0 * offset_hours
    ) % 1440.0
    hour_angle_deg = true_solar_minutes / 4.0 - 180.0
    if hour_angle_deg < -180.0:
        hour_angle_deg += 360.0

    lat_rad = math.radians(latitude)
    hour_angle = math.radians(hour_angle_deg)
    cos_zenith = (
        math.sin(lat_rad) * math.sin(declination)
        + math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle)
    )
    cos_zenith = max(-1.0, min(1.0, cos_zenith))
    zenith_deg = math.degrees(math.acos(cos_zenith))
    return 90.0 - zenith_deg


def _astro_uv_from_solar(
    *,
    solar_elevation_deg: float,
    cloud_cover_pct: float | None,
) -> float:
    """Estimate UV index from solar elevation with cloud attenuation."""
    if solar_elevation_deg <= -6.0:
        clear_uv = 0.0
    elif solar_elevation_deg <= 0.0:
        clear_uv = ((solar_elevation_deg + 6.0) / 6.0) * 0.3
    else:
        clear_uv = 12.0 * (max(0.0, math.sin(math.radians(solar_elevation_deg))) ** 1.25)
    clear_uv = max(0.0, min(14.0, clear_uv))

    attenuation = 1.0
    if cloud_cover_pct is not None:
        cloud_norm = max(0.0, min(100.0, cloud_cover_pct)) / 100.0
        attenuation = max(0.1, 1.0 - 0.75 * (cloud_norm**3))

    return round(max(0.0, min(14.0, clear_uv * attenuation)), 1)


def _geo_to_wmts_tile(
    latitude: float,
    longitude: float,
    *,
    zoom: int,
) -> tuple[int, int, int, int]:
    """Convert WGS84 lat/lon to WMTS WebMercator tile + pixel."""
    lat = max(-85.05112878, min(85.05112878, latitude))
    lon = max(-180.0, min(180.0, longitude))
    n = 2**zoom
    x = n * ((lon + 180.0) / 360.0)
    y = n * (
        1.0
        - (
            math.log(
                math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))
            )
            / math.pi
        )
    ) / 2.0
    col = max(0, min(n - 1, int(math.floor(x))))
    row = max(0, min(n - 1, int(math.floor(y))))
    pixel_x = max(0, min(255, int(math.floor((x - col) * 256.0))))
    pixel_y = max(0, min(255, int(math.floor((y - row) * 256.0))))
    return col, row, pixel_x, pixel_y


def _jellyfish_risk_from_weather(sea_temp: float, wave_height: float, wind_speed: float) -> str:
    """Compute jellyfish risk from marine conditions."""
    score = 0.0
    if sea_temp >= 25:
        score += 2.0
    elif sea_temp >= 23:
        score += 1.0

    if wave_height <= 0.6:
        score += 1.0
    elif wave_height >= 1.5:
        score -= 1.0

    if wind_speed <= 12:
        score += 1.0
    elif wind_speed >= 25:
        score -= 1.0

    if score >= 3.0:
        return "high"
    if score >= 1.5:
        return "moderate"
    return "low"


def _normalize_jellyfish_risk(
    *,
    status_label: str | None,
    status_tag: str | None,
    off_season: bool,
) -> str:
    """Normalize PlatgesCat jellyfish labels to compact risk buckets."""
    if off_season:
        return "off_season"

    source = f"{status_label or ''} {status_tag or ''}".lower()
    if not source.strip():
        return "unknown"
    if any(token in source for token in ("_molt_perill_", "molt perill", "muy alto", "very high")):
        return "very_high"
    if any(token in source for token in ("_amb_perill_", "amb perill", "con peligro", "dangerous")):
        return "high"
    if any(token in source for token in ("_sense_perill_", "sense perill", "sin peligro")):
        return "moderate"
    if any(token in source for token in ("_sense_presencia_", "sense meduses", "sin medusas", "no jellyfish")):
        return "low"
    if any(token in source for token in ("_fora_de_temporada_", "fora de temporada", "fuera de temporada")):
        return "off_season"
    return "unknown"


def _mosquito_index_from_weather(humidity: float, rain_prob_next_6h: float, wind_speed: float) -> int:
    """Estimate mosquito suitability from weather."""
    score = humidity * 0.45 + rain_prob_next_6h * 0.55 - max(0.0, wind_speed - 10.0) * 1.4
    return max(0, min(100, int(round(score))))


def _mosquito_risk_from_index(index: int) -> str:
    """Map 0..100 index to compact risk."""
    if index >= 75:
        return "very_high"
    if index >= 55:
        return "high"
    if index >= 35:
        return "moderate"
    if index >= 20:
        return "low"
    return "very_low"


def _forecast_mosquito_risk(
    *,
    baseline_index: int,
    temp_min: float,
    temp_max: float,
    rain_probability_max: int,
    wind_max_kmh: float,
) -> str:
    """Estimate day-level mosquito risk from forecast + current baseline."""
    avg_temp = (temp_min + temp_max) / 2
    score = baseline_index / 22.0

    if 22 <= avg_temp <= 32:
        score += 1.7
    elif 18 <= avg_temp < 22:
        score += 0.8
    elif avg_temp < 12 or avg_temp > 36:
        score -= 1.0

    if rain_probability_max >= 65:
        score += 1.0
    elif rain_probability_max >= 35:
        score += 0.4

    if wind_max_kmh >= 28:
        score -= 1.0
    elif wind_max_kmh >= 20:
        score -= 0.4

    if score >= 4.6:
        return "very_high"
    if score >= 3.2:
        return "high"
    if score >= 2.0:
        return "moderate"
    if score >= 1.0:
        return "low"
    return "very_low"


def _forecast_jellyfish_risk(
    *,
    baseline_risk: str,
    sea_temp_avg: float,
    wave_height_max: float,
    wind_max_kmh: float,
) -> str:
    """Estimate day-level jellyfish risk from marine forecast + baseline."""
    if baseline_risk == "off_season":
        return "off_season"

    rank = {
        "unknown": 0.5,
        "low": 1.0,
        "moderate": 2.0,
        "high": 3.0,
        "very_high": 4.0,
    }.get(baseline_risk, 0.5)

    if sea_temp_avg >= 25:
        rank += 1.0
    elif sea_temp_avg >= 23:
        rank += 0.5

    if wave_height_max <= 0.6:
        rank += 0.6
    elif wave_height_max >= 1.5:
        rank -= 0.8

    if wind_max_kmh <= 12:
        rank += 0.6
    elif wind_max_kmh >= 25:
        rank -= 0.8

    if rank >= 4.5:
        return "very_high"
    if rank >= 3.0:
        return "high"
    if rank >= 1.8:
        return "moderate"
    return "low"


def _tick_index_from_weather(
    *,
    temperature: float,
    humidity: float,
    rain_prob_next_6h: float,
    wind_speed: float,
) -> int:
    """Estimate tick suitability from weather."""
    temp_score = 0.0
    if 7 <= temperature <= 25:
        temp_score = 26.0
    elif 4 <= temperature < 7 or 25 < temperature <= 30:
        temp_score = 12.0
    elif temperature < 0 or temperature > 34:
        temp_score = 0.0
    else:
        temp_score = 6.0

    humidity_score = max(0.0, min(35.0, (humidity - 35.0) * 0.8))
    rain_score = max(0.0, min(20.0, rain_prob_next_6h * 0.25))
    wind_penalty = max(0.0, wind_speed - 18.0) * 1.1

    index = temp_score + humidity_score + rain_score - wind_penalty
    return max(0, min(100, int(round(index))))


def _tick_risk_from_index(index: int) -> str:
    """Map tick index to risk level."""
    if index >= 75:
        return "very_high"
    if index >= 55:
        return "high"
    if index >= 35:
        return "moderate"
    if index >= 18:
        return "low"
    return "very_low"


def _forecast_tick_risk(
    *,
    baseline_index: int,
    temp_min: float,
    temp_max: float,
    rain_probability_max: int,
    wind_max_kmh: float,
) -> str:
    """Estimate day-level tick risk from forecast + current baseline."""
    avg_temp = (temp_min + temp_max) / 2
    score = baseline_index / 24.0

    if 8 <= avg_temp <= 24:
        score += 2.0
    elif 5 <= avg_temp < 8 or 24 < avg_temp <= 30:
        score += 0.9
    elif avg_temp < 0 or avg_temp > 34:
        score -= 1.2

    if rain_probability_max >= 65:
        score += 1.0
    elif rain_probability_max >= 35:
        score += 0.5

    if wind_max_kmh >= 30:
        score -= 0.9
    elif wind_max_kmh >= 22:
        score -= 0.4

    if score >= 4.7:
        return "very_high"
    if score >= 3.3:
        return "high"
    if score >= 2.0:
        return "moderate"
    if score >= 1.0:
        return "low"
    return "very_low"


def _heat_index_c(temperature_c: float, humidity_pct: float) -> float:
    """Estimate heat index in Celsius using Rothfusz-like regression."""
    t = temperature_c
    rh = max(0.0, min(100.0, humidity_pct))
    if t < 20:
        return round(t, 1)
    hi = (
        -8.784695
        + 1.61139411 * t
        + 2.338549 * rh
        - 0.14611605 * t * rh
        - 0.012308094 * t * t
        - 0.016424828 * rh * rh
        + 0.002211732 * t * t * rh
        + 0.00072546 * t * rh * rh
        - 0.000003582 * t * t * rh * rh
    )
    return round(max(t, hi), 1)


def _wet_bulb_c(temperature_c: float, humidity_pct: float) -> float:
    """Approximate wet-bulb temperature in Celsius (Stull 2011)."""
    t = temperature_c
    rh = max(1.0, min(100.0, humidity_pct))
    wb = (
        t * math.atan(0.151977 * math.sqrt(rh + 8.313659))
        + math.atan(t + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * (rh ** 1.5) * math.atan(0.023101 * rh)
        - 4.686035
    )
    return round(wb, 1)


def _rip_current_index(
    *,
    wave_height_m: float,
    wave_period_s: float,
    wind_speed_kmh: float,
    rain_probability_pct: float,
) -> int:
    """Estimate rip-current risk index from marine/weather proxies."""
    score = 0.0

    if wave_height_m >= 2.0:
        score += 40
    elif wave_height_m >= 1.4:
        score += 30
    elif wave_height_m >= 0.9:
        score += 20
    elif wave_height_m >= 0.5:
        score += 10

    if wave_period_s >= 10:
        score += 26
    elif wave_period_s >= 8:
        score += 18
    elif wave_period_s >= 6:
        score += 10

    if wind_speed_kmh >= 35:
        score += 20
    elif wind_speed_kmh >= 25:
        score += 14
    elif wind_speed_kmh >= 15:
        score += 8

    if rain_probability_pct >= 70:
        score += 8
    elif rain_probability_pct >= 40:
        score += 4

    return max(0, min(100, int(round(score))))


def _sunburn_minutes(
    *,
    uv_index: float,
    skin_type: int,
    spf: float,
    shade_factor: float,
    uv_sensitivity: float,
) -> int | None:
    """Estimate minutes to minimal erythema (sunburn) for a persona."""
    uv = max(0.0, uv_index)
    if uv < 0.1:
        return None
    med = _SKIN_TYPE_MED_J_M2.get(skin_type, _SKIN_TYPE_MED_J_M2[3])
    adjusted_med = med * max(1.0, spf) * max(0.2, shade_factor) / max(0.5, uv_sensitivity)
    minutes = int(round((adjusted_med * 40.0) / (uv * 60.0)))
    return max(1, min(720, minutes))


def _sunburn_risk(minutes_to_burn: int | None) -> str:
    """Map burn-time estimate to compact risk."""
    if minutes_to_burn is None:
        return "very_low"
    if minutes_to_burn <= 20:
        return "very_high"
    if minutes_to_burn <= 40:
        return "high"
    if minutes_to_burn <= 70:
        return "moderate"
    if minutes_to_burn <= 120:
        return "low"
    return "very_low"


def _daily_hourly_values(hourly: dict[str, Any], key: str, day: str) -> list[float]:
    """Extract numeric values for one day from hourly arrays."""
    times = hourly.get("time")
    values = hourly.get(key)
    if not isinstance(times, list) or not isinstance(values, list):
        return []

    result: list[float] = []
    for idx, timestamp in enumerate(times):
        if idx >= len(values):
            break
        if not isinstance(timestamp, str) or not timestamp.startswith(day):
            continue
        value = values[idx]
        if value is None:
            continue
        result.append(_safe_float(value, 0.0))
    return result


def _build_multi_timezone_clock(raw_timezones: str) -> list[dict[str, str]]:
    """Build current time values for custom UTC offsets."""
    if not isinstance(raw_timezones, str) or not raw_timezones.strip():
        return []

    now_utc = datetime.now(tz=UTC)
    result: list[dict[str, str]] = []
    for token in [item.strip() for item in raw_timezones.split(",")]:
        normalized = _normalize_timezone_token(token)
        offset = _timezone_token_to_offset(token)
        if normalized is None or offset is None:
            continue
        sign = 1 if offset.startswith("+") else -1
        hours = int(offset[1:3])
        shifted = now_utc + timedelta(hours=sign * hours)
        result.append(
            {
                "timezone": normalized,
                "offset": offset,
                "iso": shifted.isoformat(),
                "date": shifted.strftime("%Y-%m-%d"),
                "time": shifted.strftime("%H:%M"),
            }
        )
    return result


__all__ = [name for name in globals() if not name.startswith("__")]
