"""Data provider for Beregynya AURA."""

from __future__ import annotations

import asyncio
import math
import re
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

from aiohttp import ClientError
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    CONF_FORECAST_DAYS,
    CONF_REFRESH_SECONDS,
    CONF_SOURCE_MODE,
    CONF_SOURCES,
    CONF_TIMEZONES,
    DEFAULT_TIMEZONES,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_SOURCE_MODE,
    INVALID_HA_STATES,
    SOURCE_KEY_ALIASES,
    SOURCE_MODE_HA_ONLY,
    SOURCE_MODE_HYBRID,
    SOURCE_MODE_INTERNAL,
    SUPPORTED_SOURCE_MODES,
)

_OPEN_METEO_WEATHER = "https://api.open-meteo.com/v1/forecast"
_OPEN_METEO_AIR = "https://air-quality-api.open-meteo.com/v1/air-quality"
_OPEN_METEO_MARINE = "https://marine-api.open-meteo.com/v1/marine"
_PLATGESCAT_FRONT = (
    "https://aplicacions.aca.gencat.cat/platgescat2/"
    "agencia-catalana-del-agua-backend/web/app.php/api/front/"
)
_PLATGESCAT_DETAIL_BASE = (
    "https://aplicacions.aca.gencat.cat/platgescat2/"
    "agencia-catalana-del-agua-backend/web/app.php/api/playadetalle/"
)
_MOSQUITO_ALERT_OBSERVATIONS = "https://api.mosquitoalert.com/v1/observations/"
_TIGER_MOSQUITO_TAXON_ID = 112
_INAT_OBSERVATIONS = "https://api.inaturalist.org/v1/observations"
_INAT_TICKS_TAXON_ID = 51672
_USGS_EQ_QUERY = "https://earthquake.usgs.gov/fdsnws/event/1/query"
_GDACS_RSS = "https://www.gdacs.org/xml/rss.xml"
_UTC_TOKEN_PATTERN = re.compile(r"^UTC([+-])(\d{1,2})$")
_NOTO_EMOJI_BASE = "https://fonts.gstatic.com/s/e/notoemoji/latest"

_METRIC_ICON_EMOJI: dict[str, str] = {
    "sensor.precipitation_probability": "1f327_fe0f",
    "sensor.precipitation": "1f327_fe0f",
    "sensor.uv_index": "1f31e",
    "sensor.rain_next_6h": "1f327_fe0f",
    "sensor.wind_speed": "1f32a_fe0f",
    "sensor.pressure": "1f300",
    "sensor.humidity": "2601_fe0f",
    "sensor.apparent_temperature": "1f321_fe0f",
    "sensor.sea_temperature_openmeteo": "1f30a",
    "sensor.sea_temperature_openmeteo_3h": "1f30a",
    "sensor.sea_temperature_openmeteo_6h": "1f30a",
    "sensor.wave_height": "1f30a",
    "sensor.wave_period": "1f30a",
    "sensor.pollen_total": "1f33f",
    "sensor.pollen_birch": "1f33f",
    "sensor.pollen_alder": "1f33f",
    "sensor.pollen_grass": "1f33f",
    "sensor.pollen_olive": "1f33f",
    "sensor.pollen_ragweed": "1f33f",
    "sensor.pollen_ambrosia": "1f343",
    "sensor.pollen_mugwort": "1f33f",
    "sensor.ambrosia_risk": "1f343",
    "sensor.allergy_index": "1f927",
    "sensor.asthma_risk": "1f637",
    "sensor.air_quality_european_aqi": "1f637",
    "sensor.air_quality_pm25": "1f637",
    "sensor.air_quality_pm10": "1f637",
    "sensor.air_quality_ozone": "1f637",
    "sensor.air_quality_no2": "1f637",
    "sensor.air_quality_so2": "1f637",
    "sensor.air_quality_co": "1f637",
    "sensor.waqi_barcelona": "1f637",
    "sensor.saharan_dust_level": "1faa8",
    "sensor.saharan_dust_forecast_6h": "1faa8",
    "sensor.beach_comfort_index": "1f30a",
    "sensor.beach_danger_index": "1f6a9",
    "sensor.beach_flag_calculated": "1f6a9",
    "sensor.beach_crowding_estimate": "1f30a",
    "sensor.beach_recommendation": "1f6a9",
    "sensor.jellyfish_risk": "1f41f",
    "sensor.jellyfish_official_risk": "1f41f",
    "sensor.jellyfish_official_status": "1f41f",
    "sensor.jellyfish_species_count": "1f41f",
    "sensor.jellyfish_last_update": "1f41f",
    "sensor.jellyfish_icon_code": "1f41f",
    "sensor.jellyfish_nearest_beach": "1f30a",
    "sensor.jellyfish_nearest_beach_distance": "1f30a",
    "sensor.beach_water_quality_official": "1f30a",
    "sensor.beach_water_temperature_official": "1f321_fe0f",
    "sensor.tiger_mosquito_risk": "1f99f",
    "sensor.tiger_mosquito_index": "1f99f",
    "sensor.mosquito_index": "1f99f",
    "sensor.tiger_mosquito_reports_30d": "1f99f",
    "sensor.tiger_mosquito_reports_180d": "1f99f",
    "sensor.tiger_mosquito_high_confidence": "1f99f",
    "sensor.tiger_mosquito_confidence_avg": "1f99f",
    "sensor.tiger_mosquito_last_report": "1f99f",
    "sensor.tiger_mosquito_icon_url": "1f99f",
    "sensor.tick_risk": "1f41b",
    "sensor.tick_index": "1f41b",
    "sensor.tick_reports_30d": "1f41b",
    "sensor.tick_reports_180d": "1f41b",
    "sensor.tick_last_report": "1f41b",
    "sensor.tick_source": "1f41b",
    "sensor.tick_icon_url": "1f41b",
    "sensor.earthquake_risk": "1f30b",
    "sensor.earthquake_index": "1f30b",
    "sensor.earthquake_events_24h": "1f30b",
    "sensor.earthquake_events_7d": "1f30b",
    "sensor.earthquake_max_magnitude_7d": "1f30b",
    "sensor.earthquake_nearest_distance_km": "1f30b",
    "sensor.earthquake_nearest_magnitude": "1f30b",
    "sensor.earthquake_latest_time": "1f30b",
    "sensor.earthquake_latest_place": "1f30b",
    "sensor.earthquake_tsunami_events_24h": "1f30b",
    "sensor.earthquake_event_url": "1f30b",
    "sensor.earthquake_source": "1f30b",
    "sensor.wildfire_risk": "1f525",
    "sensor.wildfire_index": "1f525",
    "sensor.wildfire_active_events_global": "1f525",
    "sensor.wildfire_high_alert_events_global": "1f525",
    "sensor.wildfire_max_alert_level": "1f525",
    "sensor.wildfire_nearest_distance_km": "1f525",
    "sensor.wildfire_nearest_country": "1f525",
    "sensor.wildfire_nearest_title": "1f525",
    "sensor.wildfire_nearest_link": "1f525",
    "sensor.wildfire_icon_url": "1f525",
    "sensor.wildfire_source": "1f525",
    "sensor.hazard_active_events_global": "1f6a8",
    "sensor.hazard_high_alert_events_global": "1f6a8",
    "sensor.hazard_top_event_type": "1f6a8",
    "sensor.hazard_top_event_alert": "1f6a8",
    "sensor.hazard_top_event_title": "1f6a8",
    "sensor.hazard_top_event_country": "1f6a8",
    "sensor.hazard_top_event_distance_km": "1f6a8",
    "sensor.hazard_top_event_icon_url": "1f6a8",
    "sensor.hazard_last_update": "1f6a8",
    "sensor.hazard_source": "1f6a8",
}


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


def normalize_options(raw_options: dict[str, Any] | None) -> dict[str, Any]:
    """Validate and normalize YAML/config-entry options."""
    options = raw_options if isinstance(raw_options, dict) else {}

    source_mode = str(options.get(CONF_SOURCE_MODE, DEFAULT_SOURCE_MODE)).strip().lower()
    if source_mode not in SUPPORTED_SOURCE_MODES:
        source_mode = DEFAULT_SOURCE_MODE

    refresh_seconds = options.get(CONF_REFRESH_SECONDS, DEFAULT_REFRESH_SECONDS)
    try:
        refresh_seconds = int(refresh_seconds)
    except (TypeError, ValueError):
        refresh_seconds = DEFAULT_REFRESH_SECONDS
    refresh_seconds = max(30, min(refresh_seconds, 86_400))

    forecast_days = options.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)
    try:
        forecast_days = int(forecast_days)
    except (TypeError, ValueError):
        forecast_days = DEFAULT_FORECAST_DAYS
    forecast_days = max(1, min(forecast_days, 7))

    timezone_tokens: list[str] = []
    raw_timezones = options.get(CONF_TIMEZONES, DEFAULT_TIMEZONES)
    if isinstance(raw_timezones, str):
        timezone_tokens = [part for part in raw_timezones.split(",")]
    elif isinstance(raw_timezones, list):
        timezone_tokens = [str(part) for part in raw_timezones]
    normalized_timezones: list[str] = []
    for token in timezone_tokens:
        normalized = _normalize_timezone_token(token)
        if normalized is None:
            continue
        if normalized not in normalized_timezones:
            normalized_timezones.append(normalized)

    sources: dict[str, str] = {}
    raw_sources = options.get(CONF_SOURCES, {})
    if isinstance(raw_sources, dict):
        for source_key, entity_id in raw_sources.items():
            if not isinstance(source_key, str) or not isinstance(entity_id, str):
                continue
            key = source_key.strip()
            value = entity_id.strip()
            if not key or not value:
                continue
            sources[key] = value

    return {
        CONF_SOURCE_MODE: source_mode,
        CONF_REFRESH_SECONDS: refresh_seconds,
        CONF_FORECAST_DAYS: forecast_days,
        CONF_TIMEZONES: ",".join(normalized_timezones),
        CONF_SOURCES: sources,
    }


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


class AuraSnapshotProvider:
    """Fetch, compute and cache the Beregynya AURA transcript."""

    def __init__(self, hass: HomeAssistant, options: dict[str, Any] | None) -> None:
        """Initialize provider."""
        self.hass = hass
        self._session = async_get_clientsession(hass)
        self._options = normalize_options(options)
        self._cache: dict[str, Any] | None = None
        self._cache_until = datetime.fromtimestamp(0, tz=UTC)
        self._lock = asyncio.Lock()

    @property
    def options(self) -> dict[str, Any]:
        """Return active provider options."""
        return self._options

    def update_options(self, options: dict[str, Any] | None) -> None:
        """Apply new options and invalidate cache."""
        self._options = normalize_options(options)
        self._cache_until = datetime.fromtimestamp(0, tz=UTC)

    async def async_get_snapshot(self, *, force_refresh: bool = False) -> dict[str, Any]:
        """Return cached snapshot or refresh it."""
        now = datetime.now(tz=UTC)
        if not force_refresh and self._cache is not None and now < self._cache_until:
            return self._cache

        async with self._lock:
            now = datetime.now(tz=UTC)
            if not force_refresh and self._cache is not None and now < self._cache_until:
                return self._cache

            snapshot = await self._async_build_snapshot()
            ttl = int(self._options[CONF_REFRESH_SECONDS])
            self._cache = snapshot
            self._cache_until = now + timedelta(seconds=ttl)
            return snapshot

    async def _async_build_snapshot(self) -> dict[str, Any]:
        """Build snapshot from internal APIs and optional HA overrides."""
        latitude = float(self.hass.config.latitude)
        longitude = float(self.hass.config.longitude)
        elevation = float(self.hass.config.elevation)
        timezone = self.hass.config.time_zone
        forecast_days = int(self._options[CONF_FORECAST_DAYS])

        weather_url = _build_url(
            _OPEN_METEO_WEATHER,
            {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": (
                    "temperature_2m,apparent_temperature,precipitation_probability,precipitation,"
                    "weather_code,uv_index,wind_speed_10m,surface_pressure,"
                    "relative_humidity_2m"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,precipitation_sum,uv_index_max,"
                    "wind_speed_10m_max"
                ),
                "timezone": timezone,
                "forecast_days": forecast_days,
            },
        )
        marine_url = _build_url(
            _OPEN_METEO_MARINE,
            {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "wave_height,wave_direction,wave_period,sea_surface_temperature",
                "timezone": timezone,
                "forecast_days": forecast_days,
            },
        )
        air_url = _build_url(
            _OPEN_METEO_AIR,
            {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": (
                    "european_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,"
                    "sulphur_dioxide,ozone,dust,grass_pollen,birch_pollen,"
                    "alder_pollen,olive_pollen,ragweed_pollen,mugwort_pollen"
                ),
                "timezone": timezone,
                "forecast_days": forecast_days,
            },
        )

        weather_task = self._async_fetch_json(weather_url)
        marine_task = self._async_fetch_json(marine_url)
        air_task = self._async_fetch_json(air_url)
        jellyfish_task = self._async_fetch_jellyfish_data(
            latitude=latitude, longitude=longitude
        )
        mosquito_task = self._async_fetch_tiger_mosquito_data(
            latitude=latitude, longitude=longitude
        )
        tick_task = self._async_fetch_tick_data(latitude=latitude, longitude=longitude)
        earthquake_task = self._async_fetch_earthquake_data(
            latitude=latitude, longitude=longitude
        )
        gdacs_task = self._async_fetch_gdacs_events()
        (
            (weather_data, weather_err),
            (marine_data, marine_err),
            (air_data, air_err),
            (jellyfish_data, jellyfish_err),
            (mosquito_data, mosquito_err),
            (tick_data, tick_err),
            (earthquake_data, earthquake_err),
            (gdacs_events, gdacs_err),
        ) = await asyncio.gather(
            weather_task,
            marine_task,
            air_task,
            jellyfish_task,
            mosquito_task,
            tick_task,
            earthquake_task,
            gdacs_task,
        )

        metrics = self._build_internal_metrics(
            latitude=latitude,
            longitude=longitude,
            weather_data=weather_data,
            marine_data=marine_data,
            air_data=air_data,
        )
        jellyfish_metrics, jellyfish_risk_for_forecast = self._build_jellyfish_metrics(
            metrics=metrics,
            jellyfish_data=jellyfish_data,
        )
        mosquito_metrics, mosquito_index_for_forecast = self._build_tiger_mosquito_metrics(
            metrics=metrics,
            mosquito_data=mosquito_data,
        )
        tick_metrics, tick_index_for_forecast = self._build_tick_metrics(
            metrics=metrics,
            tick_data=tick_data,
        )
        earthquake_metrics = self._build_earthquake_metrics(
            earthquake_data=earthquake_data,
        )
        wildfire_metrics = self._build_wildfire_metrics(
            latitude=latitude,
            longitude=longitude,
            gdacs_events=gdacs_events,
        )
        hazard_metrics = self._build_hazard_metrics(
            latitude=latitude,
            longitude=longitude,
            gdacs_events=gdacs_events,
        )
        metrics.extend(jellyfish_metrics)
        metrics.extend(mosquito_metrics)
        metrics.extend(tick_metrics)
        metrics.extend(earthquake_metrics)
        metrics.extend(wildfire_metrics)
        metrics.extend(hazard_metrics)

        forecast_daily = self._build_forecast_daily(
            forecast_days=forecast_days,
            weather_data=weather_data,
            marine_data=marine_data,
            air_data=air_data,
            mosquito_baseline_index=mosquito_index_for_forecast,
            jellyfish_baseline_risk=jellyfish_risk_for_forecast,
            tick_baseline_index=tick_index_for_forecast,
        )
        overrides = self._apply_ha_sources(metrics)
        self._decorate_entity_icons(metrics)
        self._decorate_forecast_icons(forecast_daily)

        timezone_clock = _build_multi_timezone_clock(
            str(self._options.get(CONF_TIMEZONES, DEFAULT_TIMEZONES))
        )
        icon_catalog = self._build_icon_catalog(
            metrics=metrics,
            forecast_daily=forecast_daily,
            jellyfish_data=jellyfish_data,
            mosquito_data=mosquito_data,
            tick_data=tick_data,
            earthquake_data=earthquake_data,
            gdacs_events=gdacs_events,
        )

        return {
            "meta": {
                "source": "bereginya_aura_internal_api",
                "source_mode": self._options[CONF_SOURCE_MODE],
                "refresh_seconds": self._options[CONF_REFRESH_SECONDS],
                "forecast_days": forecast_days,
                "generated_at": datetime.now(tz=UTC).isoformat(),
                "timezones": timezone_clock,
                "home_position": {
                    "latitude": round(latitude, 6),
                    "longitude": round(longitude, 6),
                    "elevation_m": elevation,
                    "timezone": timezone,
                },
                "fetch": {
                    "weather": "ok" if weather_err is None else weather_err,
                    "marine": "ok" if marine_err is None else marine_err,
                    "air_quality": "ok" if air_err is None else air_err,
                    "jellyfish": "ok" if jellyfish_err is None else jellyfish_err,
                    "tiger_mosquito": "ok" if mosquito_err is None else mosquito_err,
                    "ticks": "ok" if tick_err is None else tick_err,
                    "earthquakes": "ok" if earthquake_err is None else earthquake_err,
                    "gdacs": "ok" if gdacs_err is None else gdacs_err,
                },
                "icons": icon_catalog,
                "ha_overrides": overrides,
                "forecast_count": len(forecast_daily),
            },
            "entities": metrics,
            "forecast_daily": forecast_daily,
        }

    async def _async_fetch_json(self, url: str) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch JSON from remote API."""
        try:
            async with self._session.get(url, timeout=25) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
            if not isinstance(payload, dict):
                return None, "invalid_payload"
            return payload, None
        except (TimeoutError, ClientError, ValueError) as err:
            return None, str(err)

    async def _async_fetch_text(self, url: str) -> tuple[str | None, str | None]:
        """Fetch text payload from remote API."""
        try:
            async with self._session.get(url, timeout=25) as response:
                response.raise_for_status()
                payload = await response.text()
            if not isinstance(payload, str) or not payload.strip():
                return None, "empty_payload"
            return payload, None
        except (TimeoutError, ClientError, ValueError) as err:
            return None, str(err)

    async def _async_fetch_earthquake_data(
        self, *, latitude: float, longitude: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch recent earthquake activity around home point from USGS."""
        now = datetime.now(tz=UTC)
        start_24h = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
        start_7d = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        common = {
            "format": "geojson",
            "latitude": f"{latitude:.6f}",
            "longitude": f"{longitude:.6f}",
            "maxradiuskm": 700,
            "orderby": "time",
            "limit": 200,
        }
        url_24h = _build_url(
            _USGS_EQ_QUERY,
            {
                **common,
                "starttime": start_24h,
                "endtime": end_time,
            },
        )
        url_7d = _build_url(
            _USGS_EQ_QUERY,
            {
                **common,
                "starttime": start_7d,
                "endtime": end_time,
            },
        )
        (data_24h, err_24h), (data_7d, err_7d) = await asyncio.gather(
            self._async_fetch_json(url_24h),
            self._async_fetch_json(url_7d),
        )
        if not isinstance(data_24h, dict) and not isinstance(data_7d, dict):
            return None, err_24h or err_7d or "earthquake_api_unavailable"

        features_24h = data_24h.get("features", []) if isinstance(data_24h, dict) else []
        features_7d = data_7d.get("features", []) if isinstance(data_7d, dict) else []
        if not isinstance(features_24h, list):
            features_24h = []
        if not isinstance(features_7d, list):
            features_7d = []

        count_24h = _safe_int(
            data_24h.get("metadata", {}).get("count") if isinstance(data_24h, dict) else len(features_24h),
            len(features_24h),
        )
        count_7d = _safe_int(
            data_7d.get("metadata", {}).get("count") if isinstance(data_7d, dict) else len(features_7d),
            len(features_7d),
        )

        max_mag_7d: float | None = None
        nearest_dist_km: float | None = None
        nearest_mag: float | None = None
        nearest_url: str | None = None
        latest_time_ms: int | None = None
        latest_place: str | None = None

        for feature in features_7d:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties")
            geometry = feature.get("geometry")
            if not isinstance(properties, dict):
                continue
            mag = _optional_float(properties.get("mag"), 1)
            if mag is not None and (max_mag_7d is None or mag > max_mag_7d):
                max_mag_7d = mag

            raw_time = properties.get("time")
            if isinstance(raw_time, (int, float)):
                ts = int(raw_time)
                if latest_time_ms is None or ts > latest_time_ms:
                    latest_time_ms = ts
                    latest_place = str(properties.get("place") or "unknown")

            if not isinstance(geometry, dict):
                continue
            coordinates = geometry.get("coordinates")
            if not isinstance(coordinates, list) or len(coordinates) < 2:
                continue
            ev_lon = _optional_float(coordinates[0])
            ev_lat = _optional_float(coordinates[1])
            if ev_lon is None or ev_lat is None:
                continue
            dist_km = _haversine_km(latitude, longitude, ev_lat, ev_lon)
            if nearest_dist_km is None or dist_km < nearest_dist_km:
                nearest_dist_km = round(dist_km, 1)
                nearest_mag = mag
                nearest_url = properties.get("url")

        tsunami_24h = 0
        for feature in features_24h:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                continue
            tsunami_flag = _safe_int(properties.get("tsunami"), 0)
            if tsunami_flag == 1:
                tsunami_24h += 1

        latest_iso = "unknown"
        if latest_time_ms is not None:
            latest_iso = datetime.fromtimestamp(latest_time_ms / 1000, tz=UTC).isoformat()

        partial_errors = [err for err in (err_24h, err_7d) if err is not None]
        error_text = "; ".join(partial_errors) if partial_errors else None
        return (
            {
                "count_24h": count_24h,
                "count_7d": count_7d,
                "max_mag_7d": max_mag_7d,
                "nearest_distance_km": nearest_dist_km,
                "nearest_magnitude": nearest_mag,
                "nearest_event_url": nearest_url,
                "latest_time": latest_iso,
                "latest_place": latest_place or "unknown",
                "tsunami_events_24h": tsunami_24h,
            },
            error_text,
        )

    async def _async_fetch_gdacs_events(self) -> tuple[list[dict[str, Any]] | None, str | None]:
        """Fetch GDACS events feed and parse current event metadata."""
        xml_text, xml_err = await self._async_fetch_text(_GDACS_RSS)
        if not isinstance(xml_text, str):
            return None, xml_err or "gdacs_feed_unavailable"

        ns = {
            "gdacs": "http://www.gdacs.org",
            "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
            "georss": "http://www.georss.org/georss",
        }
        try:
            root = ET.fromstring(xml_text.lstrip("\ufeff\r\n\t "))
        except ET.ParseError as err:
            return None, f"xml_parse_error:{err}"

        events: list[dict[str, Any]] = []
        for item in root.findall("./channel/item"):
            title = str(item.findtext("title", default="")).strip()
            link = str(item.findtext("link", default="")).strip()
            pub_date_raw = str(item.findtext("pubDate", default="")).strip()
            event_type = str(item.findtext("gdacs:eventtype", default="", namespaces=ns)).strip().upper()
            alert_level = str(item.findtext("gdacs:alertlevel", default="", namespaces=ns)).strip().lower()
            country = str(item.findtext("gdacs:country", default="", namespaces=ns)).strip()
            icon_url = str(item.findtext("gdacs:icon", default="", namespaces=ns)).strip()
            severity = str(item.findtext("gdacs:severity", default="", namespaces=ns)).strip()
            is_current = str(
                item.findtext("gdacs:iscurrent", default="false", namespaces=ns)
            ).strip().lower() == "true"

            pub_iso = None
            pub_ts = 0
            if pub_date_raw:
                try:
                    parsed = parsedate_to_datetime(pub_date_raw)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    parsed = parsed.astimezone(UTC)
                    pub_iso = parsed.isoformat()
                    pub_ts = int(parsed.timestamp())
                except (TypeError, ValueError, OverflowError):
                    pub_iso = None
                    pub_ts = 0

            lat = None
            lon = None
            point = str(item.findtext("georss:point", default="", namespaces=ns)).strip()
            if point:
                parts = [part for part in point.split(" ") if part]
                if len(parts) >= 2:
                    lat = _optional_float(parts[0], 4)
                    lon = _optional_float(parts[1], 4)
            if lat is None or lon is None:
                lat = _optional_float(item.findtext("geo:Point/geo:lat", default="", namespaces=ns), 4)
                lon = _optional_float(item.findtext("geo:Point/geo:long", default="", namespaces=ns), 4)

            if not event_type:
                continue

            events.append(
                {
                    "event_type": event_type,
                    "alert_level": alert_level if alert_level else "unknown",
                    "is_current": is_current,
                    "title": title or "unknown",
                    "country": country or "unknown",
                    "link": link or None,
                    "icon_url": icon_url or None,
                    "severity": severity or None,
                    "latitude": lat,
                    "longitude": lon,
                    "published_at": pub_iso,
                    "published_ts": pub_ts,
                }
            )

        return events, None

    async def _async_fetch_jellyfish_data(
        self, *, latitude: float, longitude: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch nearest-beach jellyfish data from PlatgesCat."""
        front_data, front_err = await self._async_fetch_json(_PLATGESCAT_FRONT)
        if not isinstance(front_data, dict):
            return None, front_err or "front_unavailable"

        beaches = front_data.get("playas")
        if not isinstance(beaches, list) or not beaches:
            return None, "no_beaches_in_front_payload"

        nearest: dict[str, Any] | None = None
        nearest_dist_km = 10_000.0
        for beach in beaches:
            if not isinstance(beach, dict):
                continue
            lat = _safe_float(beach.get("latitud"), math.nan)
            lon = _safe_float(beach.get("longitud"), math.nan)
            if math.isnan(lat) or math.isnan(lon):
                continue
            dist_km = _haversine_km(latitude, longitude, lat, lon)
            if dist_km < nearest_dist_km:
                nearest = beach
                nearest_dist_km = dist_km

        if nearest is None:
            return None, "no_nearest_beach"

        detail_data: dict[str, Any] | None = None
        detail_err: str | None = None
        beach_id = nearest.get("id")
        if isinstance(beach_id, int):
            detail_url = f"{_PLATGESCAT_DETAIL_BASE}{beach_id}"
            detail_data, detail_err = await self._async_fetch_json(detail_url)

        result: dict[str, Any] = {
            "beach_id": nearest.get("id"),
            "beach_name": nearest.get("nombre"),
            "beach_municipality": nearest.get("municipio"),
            "distance_km": round(nearest_dist_km, 2),
            "lat": _safe_float(nearest.get("latitud"), latitude),
            "lon": _safe_float(nearest.get("longitud"), longitude),
            "front_medusa_tag": nearest.get("medusaetiqueta"),
            "front_medusa_label": nearest.get("medusasliteral"),
            "front_water_quality_tag": nearest.get("calidadaguaetiqueta"),
            "front_water_temp": _safe_float(nearest.get("temperaturaagua"), 0.0),
        }

        items = detail_data.get("items", {}) if isinstance(detail_data, dict) else {}
        if isinstance(items, dict):
            medusas = items.get("medusas")
            if isinstance(medusas, dict):
                result["status_label"] = medusas.get("peligrosidadTrad")
                result["status_tag"] = medusas.get("peligrosidadEtiqueta")
                result["status_icon"] = medusas.get("icono")
                result["species_list"] = (
                    medusas.get("llistatMeduses")
                    if isinstance(medusas.get("llistatMeduses"), list)
                    else []
                )
                fecha_mod = medusas.get("fechaModificacion")
                if isinstance(fecha_mod, dict):
                    result["last_update"] = fecha_mod.get("date")
                elif isinstance(fecha_mod, str):
                    result["last_update"] = fecha_mod

            quality = items.get("calidadPlaya")
            if isinstance(quality, dict):
                result["water_quality"] = quality.get("estado")
                result["water_quality_tag"] = quality.get("estado_etiqueta")

            state = items.get("estadoPlaya")
            if isinstance(state, dict):
                result["water_temp_c"] = _safe_float(
                    state.get("temperaturaAgua"), result["front_water_temp"]
                )
                result["sky_text"] = state.get("traduccionCielo")

            sea = items.get("estadoMar")
            if isinstance(sea, dict):
                result["wave_height"] = _safe_float(sea.get("alturaolas"), 0.0)
                result["wind_speed"] = _safe_float(sea.get("velocidadviento"), 0.0)

            result["off_season"] = bool(items.get("foraTemporada"))

        if detail_err is not None:
            return result, f"detail_partial:{detail_err}"
        return result, None

    async def _async_fetch_tiger_mosquito_data(
        self, *, latitude: float, longitude: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch tiger mosquito observations from Mosquito Alert API."""
        now = datetime.now(tz=UTC)
        after_180 = (now - timedelta(days=180)).isoformat().replace("+00:00", "Z")
        after_30 = (now - timedelta(days=30)).isoformat().replace("+00:00", "Z")
        point = f"{longitude:.6f},{latitude:.6f}"

        common_params = {
            "point": point,
            "dist": 20_000,
            "identification_taxon_ids": str(_TIGER_MOSQUITO_TAXON_ID),
            "order_by": "-received_at",
        }
        url_180 = _build_url(
            _MOSQUITO_ALERT_OBSERVATIONS,
            {
                **common_params,
                "received_at_after": after_180,
                "page_size": 200,
            },
        )
        url_30 = _build_url(
            _MOSQUITO_ALERT_OBSERVATIONS,
            {
                **common_params,
                "received_at_after": after_30,
                "page_size": 1,
            },
        )

        (data_180, err_180), (data_30, err_30) = await asyncio.gather(
            self._async_fetch_json(url_180),
            self._async_fetch_json(url_30),
        )

        if not isinstance(data_180, dict) and not isinstance(data_30, dict):
            return None, err_180 or err_30 or "mosquito_api_unavailable"

        results_180 = data_180.get("results", []) if isinstance(data_180, dict) else []
        if not isinstance(results_180, list):
            results_180 = []

        count_180 = _safe_int(
            data_180.get("count") if isinstance(data_180, dict) else len(results_180),
            len(results_180),
        )
        count_30 = _safe_int(
            data_30.get("count") if isinstance(data_30, dict) else 0,
            0,
        )

        high_confidence = 0
        confidence_sum = 0.0
        confidence_count = 0
        latest_received_at: datetime | None = None
        latest_uuid: str | None = None
        icon_url: str | None = None

        for row in results_180:
            if not isinstance(row, dict):
                continue
            received_raw = row.get("received_at") or row.get("created_at")
            if isinstance(received_raw, str):
                parsed = dt_util.parse_datetime(received_raw)
                if parsed is not None:
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    if latest_received_at is None or parsed > latest_received_at:
                        latest_received_at = parsed
                        latest_uuid = row.get("uuid")

            ident = row.get("identification")
            result = ident.get("result") if isinstance(ident, dict) else {}
            if isinstance(result, dict):
                if result.get("is_high_confidence") is True:
                    high_confidence += 1
                confidence = result.get("confidence")
                if confidence is not None:
                    confidence_sum += _safe_float(confidence, 0.0)
                    confidence_count += 1

            if icon_url is None:
                if isinstance(ident, dict):
                    ident_photo = ident.get("photo")
                    if isinstance(ident_photo, dict):
                        candidate = ident_photo.get("url")
                        if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                            icon_url = candidate
                if icon_url is None:
                    photos = row.get("photos")
                    if isinstance(photos, list):
                        for photo in photos:
                            if not isinstance(photo, dict):
                                continue
                            candidate = photo.get("url")
                            if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                                icon_url = candidate
                                break

        high_conf_pct = 0
        if results_180:
            high_conf_pct = int(round((high_confidence / len(results_180)) * 100))
        confidence_avg = 0
        if confidence_count > 0:
            confidence_avg = int(round((confidence_sum / confidence_count) * 100))

        latest_iso: str | None = None
        latest_days_ago = 999
        if latest_received_at is not None:
            latest_iso = latest_received_at.astimezone(UTC).isoformat()
            latest_days_ago = max(0, int((now - latest_received_at).total_seconds() / 86_400))

        partial_errors = [err for err in (err_180, err_30) if err is not None]
        error_text = "; ".join(partial_errors) if partial_errors else None

        return (
            {
                "count_30d": count_30,
                "count_180d": count_180,
                "high_confidence_pct": high_conf_pct,
                "confidence_avg_pct": confidence_avg,
                "latest_received_at": latest_iso,
                "latest_days_ago": latest_days_ago,
                "latest_uuid": latest_uuid,
                "icon_url": icon_url,
            },
            error_text,
        )

    async def _async_fetch_tick_data(
        self, *, latitude: float, longitude: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch tick observations around home point from iNaturalist API."""
        now = datetime.now(tz=UTC)
        d1_180 = (now - timedelta(days=180)).strftime("%Y-%m-%d")
        d1_30 = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        common = {
            "lat": f"{latitude:.6f}",
            "lng": f"{longitude:.6f}",
            "radius": 50,
            "taxon_id": _INAT_TICKS_TAXON_ID,
            "order_by": "observed_on",
            "order": "desc",
        }
        url_180 = _build_url(
            _INAT_OBSERVATIONS,
            {
                **common,
                "d1": d1_180,
                "per_page": 200,
            },
        )
        url_30 = _build_url(
            _INAT_OBSERVATIONS,
            {
                **common,
                "d1": d1_30,
                "per_page": 1,
            },
        )
        (data_180, err_180), (data_30, err_30) = await asyncio.gather(
            self._async_fetch_json(url_180),
            self._async_fetch_json(url_30),
        )
        if not isinstance(data_180, dict) and not isinstance(data_30, dict):
            return None, err_180 or err_30 or "ticks_api_unavailable"

        results_180 = data_180.get("results", []) if isinstance(data_180, dict) else []
        if not isinstance(results_180, list):
            results_180 = []

        count_180 = _safe_int(
            data_180.get("total_results") if isinstance(data_180, dict) else len(results_180),
            len(results_180),
        )
        count_30 = _safe_int(
            data_30.get("total_results") if isinstance(data_30, dict) else 0,
            0,
        )

        latest_observed = None
        research_count = 0
        needs_id_count = 0
        icon_url = None
        taxon_name = None
        common_name = None

        for row in results_180:
            if not isinstance(row, dict):
                continue
            observed_on = row.get("observed_on")
            if isinstance(observed_on, str):
                parsed = dt_util.parse_datetime(f"{observed_on}T00:00:00+00:00")
                if parsed is not None and (latest_observed is None or parsed > latest_observed):
                    latest_observed = parsed

            quality_grade = str(row.get("quality_grade") or "").lower()
            if quality_grade == "research":
                research_count += 1
            elif quality_grade == "needs_id":
                needs_id_count += 1

            taxon = row.get("taxon")
            if isinstance(taxon, dict):
                if taxon_name is None:
                    taxon_name = taxon.get("name")
                if common_name is None:
                    common_name = taxon.get("preferred_common_name")
                if icon_url is None:
                    photo = taxon.get("default_photo")
                    if isinstance(photo, dict):
                        icon_url = photo.get("square_url") or photo.get("small_url")

        latest_iso = latest_observed.isoformat() if latest_observed is not None else None
        latest_days_ago = 999
        if latest_observed is not None:
            latest_days_ago = max(0, int((now - latest_observed).total_seconds() / 86_400))

        total_quality = research_count + needs_id_count
        research_pct = int(round((research_count / total_quality) * 100)) if total_quality > 0 else 0

        partial_errors = [err for err in (err_180, err_30) if err is not None]
        error_text = "; ".join(partial_errors) if partial_errors else None

        return (
            {
                "count_30d": count_30,
                "count_180d": count_180,
                "latest_observed_at": latest_iso,
                "latest_days_ago": latest_days_ago,
                "research_pct": research_pct,
                "taxon_name": taxon_name,
                "common_name": common_name,
                "icon_url": icon_url,
            },
            error_text,
        )

    def _build_tick_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        tick_data: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """Build tick metrics from iNaturalist observations + weather suitability."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        temperature = _optional_float(values.get("sensor.apparent_temperature"))
        if temperature is None:
            temperature = _optional_float(values.get("sensor.sea_temperature_openmeteo"))
        humidity = _optional_float(values.get("sensor.humidity"))
        rain_next_6h = _optional_float(values.get("sensor.rain_next_6h"))
        wind_speed = _optional_float(values.get("sensor.wind_speed"))

        weather_index: int | None = None
        if (
            temperature is not None
            and humidity is not None
            and rain_next_6h is not None
            and wind_speed is not None
        ):
            weather_index = _tick_index_from_weather(
                temperature=temperature,
                humidity=humidity,
                rain_prob_next_6h=rain_next_6h,
                wind_speed=wind_speed,
            )

        count_30d = 0
        count_180d = 0
        latest_report = "unknown"
        latest_days_ago = 999
        research_pct = 0
        source = "internal_model"
        taxon_label = "Ixodida"
        icon_url = None

        if isinstance(tick_data, dict):
            source = "inaturalist_api"
            count_30d = _safe_int(tick_data.get("count_30d"), 0)
            count_180d = _safe_int(tick_data.get("count_180d"), 0)
            latest_report = str(tick_data.get("latest_observed_at") or "unknown")
            latest_days_ago = _safe_int(tick_data.get("latest_days_ago"), 999)
            research_pct = _safe_int(tick_data.get("research_pct"), 0)
            icon_url = tick_data.get("icon_url")
            taxon_name = tick_data.get("taxon_name")
            common_name = tick_data.get("common_name")
            if isinstance(common_name, str) and common_name.strip():
                taxon_label = common_name
            elif isinstance(taxon_name, str) and taxon_name.strip():
                taxon_label = taxon_name

        obs_boost = min(count_30d * 5, 45) + min(count_180d, 25)
        quality_boost = int(round((research_pct - 45) / 6))
        if weather_index is None and source != "inaturalist_api":
            tick_index: int | None = None
        else:
            base = weather_index if weather_index is not None else 20
            tick_index = base + obs_boost + quality_boost

        if tick_index is not None:
            if latest_days_ago > 120:
                tick_index = min(tick_index, 25)
            elif latest_days_ago > 60:
                tick_index = min(tick_index, 40)
            elif latest_days_ago > 30:
                tick_index = min(tick_index, 55)
            tick_index = max(0, min(100, tick_index))
        tick_risk = _tick_risk_from_index(tick_index) if tick_index is not None else "unavailable"

        if source == "internal_model" and tick_index is None:
            source = "unavailable"

        return (
            [
                {
                    "entity_id": "sensor.tick_risk",
                    "name": "Tick risk",
                    "value": tick_risk,
                    "source": source,
                    "icon": "mdi:bug-outline",
                },
                {
                    "entity_id": "sensor.tick_index",
                    "name": "Tick index",
                    "value": tick_index if tick_index is not None else "unavailable",
                    "unit": "/100",
                    "source": source,
                    "icon": "mdi:chart-line",
                },
                {
                    "entity_id": "sensor.tick_reports_30d",
                    "name": "Tick reports 30d",
                    "value": count_30d,
                    "source": source,
                    "icon": "mdi:calendar-month",
                },
                {
                    "entity_id": "sensor.tick_reports_180d",
                    "name": "Tick reports 180d",
                    "value": count_180d,
                    "source": source,
                    "icon": "mdi:calendar-range",
                },
                {
                    "entity_id": "sensor.tick_last_report",
                    "name": "Tick last report",
                    "value": latest_report,
                    "source": source,
                    "icon": "mdi:clock-outline",
                },
                {
                    "entity_id": "sensor.tick_source",
                    "name": "Tick source",
                    "value": taxon_label,
                    "source": source,
                    "icon": "mdi:database-search-outline",
                },
                {
                    "entity_id": "sensor.tick_icon_url",
                    "name": "Tick icon URL",
                    "value": icon_url if isinstance(icon_url, str) and icon_url else "unavailable",
                    "source": source,
                    "icon": "mdi:image-outline",
                },
            ],
            tick_index,
        )

    def _build_jellyfish_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        jellyfish_data: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], str]:
        """Build jellyfish-related metrics with official + model estimate."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        sea_temp = _optional_float(values.get("sensor.sea_temperature_openmeteo"))
        wave_height = _optional_float(values.get("sensor.wave_height"))
        wind_speed = _optional_float(values.get("sensor.wind_speed"))
        estimated_risk = (
            _jellyfish_risk_from_weather(sea_temp, wave_height, wind_speed)
            if sea_temp is not None and wave_height is not None and wind_speed is not None
            else "unavailable"
        )

        official_status = None
        official_tag = None
        official_species_count = 0
        official_last_update = "unknown"
        nearest_beach = "unknown"
        nearest_dist_km: float | None = None
        water_quality = "unknown"
        water_temp_official: float | None = None
        off_season = False
        source = "internal_model"
        icon_code = None

        if isinstance(jellyfish_data, dict):
            source = "platgescat_api"
            official_status = jellyfish_data.get("status_label") or jellyfish_data.get(
                "front_medusa_label"
            )
            official_tag = jellyfish_data.get("status_tag") or jellyfish_data.get(
                "front_medusa_tag"
            )
            species = jellyfish_data.get("species_list")
            if isinstance(species, list):
                official_species_count = len(species)
            official_last_update = str(jellyfish_data.get("last_update") or "unknown")
            nearest_beach = str(jellyfish_data.get("beach_name") or "unknown")
            nearest_dist_km = _optional_float(jellyfish_data.get("distance_km"), 2)
            icon_code = jellyfish_data.get("status_icon")
            water_quality = str(
                jellyfish_data.get("water_quality")
                or jellyfish_data.get("front_water_quality_tag")
                or "unknown"
            )
            water_temp_official = _optional_float(
                jellyfish_data.get("water_temp_c", jellyfish_data.get("front_water_temp")),
                1,
            )
            off_season = bool(jellyfish_data.get("off_season"))

        official_risk = _normalize_jellyfish_risk(
            status_label=official_status if isinstance(official_status, str) else None,
            status_tag=official_tag if isinstance(official_tag, str) else None,
            off_season=off_season,
        )
        combined_risk = official_risk if official_risk not in {"unknown", ""} else estimated_risk

        return (
            [
                {
                    "entity_id": "sensor.jellyfish_risk",
                    "name": "Jellyfish risk",
                    "value": combined_risk,
                    "source": source,
                    "icon": "mdi:jellyfish",
                },
                {
                    "entity_id": "sensor.jellyfish_official_risk",
                    "name": "Jellyfish official risk",
                    "value": official_risk,
                    "source": source,
                    "icon": "mdi:shield-wave",
                },
                {
                    "entity_id": "sensor.jellyfish_official_status",
                    "name": "Jellyfish official status",
                    "value": official_status or "unknown",
                    "source": source,
                    "icon": "mdi:information-outline",
                },
                {
                    "entity_id": "sensor.jellyfish_species_count",
                    "name": "Jellyfish species count",
                    "value": official_species_count,
                    "source": source,
                    "icon": "mdi:fishbowl-outline",
                },
                {
                    "entity_id": "sensor.jellyfish_last_update",
                    "name": "Jellyfish last update",
                    "value": official_last_update,
                    "source": source,
                    "icon": "mdi:clock-outline",
                },
                {
                    "entity_id": "sensor.jellyfish_nearest_beach",
                    "name": "Nearest beach (PlatgesCat)",
                    "value": nearest_beach,
                    "source": source,
                    "icon": "mdi:beach",
                },
                {
                    "entity_id": "sensor.jellyfish_nearest_beach_distance",
                    "name": "Nearest beach distance",
                    "value": nearest_dist_km if nearest_dist_km is not None else "unavailable",
                    "unit": "km",
                    "source": source,
                    "icon": "mdi:map-marker-distance",
                },
                {
                    "entity_id": "sensor.beach_water_quality_official",
                    "name": "Beach water quality (official)",
                    "value": water_quality,
                    "source": source,
                    "icon": "mdi:water-check",
                },
                {
                    "entity_id": "sensor.beach_water_temperature_official",
                    "name": "Beach water temperature (official)",
                    "value": (
                        water_temp_official
                        if water_temp_official is not None
                        else "unavailable"
                    ),
                    "unit": "degC",
                    "source": source,
                    "icon": "mdi:coolant-temperature",
                },
                {
                    "entity_id": "sensor.jellyfish_icon_code",
                    "name": "Jellyfish icon code",
                    "value": icon_code if isinstance(icon_code, str) and icon_code else "unknown",
                    "source": source,
                    "icon": "mdi:image-outline",
                },
            ],
            combined_risk,
        )

    def _build_tiger_mosquito_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        mosquito_data: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """Build tiger-mosquito metrics with observations + weather."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        humidity = _optional_float(values.get("sensor.humidity"))
        rain_next_6h = _optional_float(values.get("sensor.rain_next_6h"))
        wind_speed = _optional_float(values.get("sensor.wind_speed"))

        weather_index: int | None = None
        if humidity is not None and rain_next_6h is not None and wind_speed is not None:
            weather_index = _mosquito_index_from_weather(humidity, rain_next_6h, wind_speed)
        count_30d = 0
        count_180d = 0
        high_conf_pct = 0
        confidence_avg_pct = 0
        latest_report = "unknown"
        latest_days_ago = 999
        source = "internal_model"
        icon_url = None

        if isinstance(mosquito_data, dict):
            source = "mosquito_alert_api"
            count_30d = _safe_int(mosquito_data.get("count_30d"), 0)
            count_180d = _safe_int(mosquito_data.get("count_180d"), 0)
            high_conf_pct = _safe_int(mosquito_data.get("high_confidence_pct"), 0)
            confidence_avg_pct = _safe_int(mosquito_data.get("confidence_avg_pct"), 0)
            latest_report = str(mosquito_data.get("latest_received_at") or "unknown")
            latest_days_ago = _safe_int(mosquito_data.get("latest_days_ago"), 999)
            icon_url = mosquito_data.get("icon_url")

        observation_boost = min(count_30d * 4, 42) + min(count_180d, 30)
        confidence_adjustment = int(round((high_conf_pct - 50) / 5))
        if weather_index is None and source != "mosquito_alert_api":
            mosquito_index: int | None = None
        else:
            base = weather_index if weather_index is not None else 20
            mosquito_index = base + observation_boost + confidence_adjustment
            if latest_days_ago > 120:
                mosquito_index = min(mosquito_index, 30)
            elif latest_days_ago > 60:
                mosquito_index = min(mosquito_index, 45)
            elif latest_days_ago > 30:
                mosquito_index = min(mosquito_index, 60)
            mosquito_index = max(0, min(100, mosquito_index))
        mosquito_risk = (
            _mosquito_risk_from_index(mosquito_index)
            if mosquito_index is not None
            else "unavailable"
        )

        if source == "internal_model" and mosquito_index is None:
            source = "unavailable"

        return (
            [
                {
                    "entity_id": "sensor.tiger_mosquito_risk",
                    "name": "Tiger mosquito risk",
                    "value": mosquito_risk,
                    "source": source,
                    "icon": "mdi:mosquito",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_index",
                    "name": "Tiger mosquito index",
                    "value": mosquito_index if mosquito_index is not None else "unavailable",
                    "unit": "/100",
                    "source": source,
                    "icon": "mdi:chart-bell-curve-cumulative",
                },
                {
                    "entity_id": "sensor.mosquito_index",
                    "name": "Mosquito index",
                    "value": mosquito_index if mosquito_index is not None else "unavailable",
                    "unit": "/100",
                    "source": source,
                    "icon": "mdi:chart-bell-curve-cumulative",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_reports_30d",
                    "name": "Tiger mosquito reports 30d",
                    "value": count_30d,
                    "source": source,
                    "icon": "mdi:calendar-month",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_reports_180d",
                    "name": "Tiger mosquito reports 180d",
                    "value": count_180d,
                    "source": source,
                    "icon": "mdi:calendar-range",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_high_confidence",
                    "name": "Tiger mosquito high confidence",
                    "value": high_conf_pct,
                    "unit": "%",
                    "source": source,
                    "icon": "mdi:certificate-outline",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_confidence_avg",
                    "name": "Tiger mosquito confidence avg",
                    "value": confidence_avg_pct,
                    "unit": "%",
                    "source": source,
                    "icon": "mdi:percent-outline",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_last_report",
                    "name": "Tiger mosquito last report",
                    "value": latest_report,
                    "source": source,
                    "icon": "mdi:clock-outline",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_icon_url",
                    "name": "Tiger mosquito icon URL",
                    "value": icon_url if isinstance(icon_url, str) and icon_url else "unavailable",
                    "source": source,
                    "icon": "mdi:image-outline",
                },
            ],
            mosquito_index,
        )

    def _build_earthquake_metrics(
        self,
        *,
        earthquake_data: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Build earthquake metrics from USGS observations near home point."""
        source = "usgs_api" if isinstance(earthquake_data, dict) else "unavailable"

        count_24h: Any = "unavailable"
        count_7d: Any = "unavailable"
        max_mag_7d: Any = "unavailable"
        nearest_distance_km: Any = "unavailable"
        nearest_magnitude: Any = "unavailable"
        latest_time: Any = "unavailable"
        latest_place: Any = "unavailable"
        tsunami_24h: Any = "unavailable"
        event_url: Any = "unavailable"
        eq_index: Any = "unavailable"
        eq_risk: Any = "unavailable"

        if isinstance(earthquake_data, dict):
            count_24h = _safe_int(earthquake_data.get("count_24h"), 0)
            count_7d = _safe_int(earthquake_data.get("count_7d"), 0)
            max_mag = _optional_float(earthquake_data.get("max_mag_7d"), 1)
            nearest_dist = _optional_float(earthquake_data.get("nearest_distance_km"), 1)
            nearest_mag = _optional_float(earthquake_data.get("nearest_magnitude"), 1)
            latest_time = str(earthquake_data.get("latest_time") or "unknown")
            latest_place = str(earthquake_data.get("latest_place") or "unknown")
            tsunami_24h = _safe_int(earthquake_data.get("tsunami_events_24h"), 0)
            event_url = str(earthquake_data.get("nearest_event_url") or "unavailable")

            score = min(count_7d * 3, 30)
            if max_mag is not None:
                max_mag_7d = max_mag
                if max_mag >= 7.0:
                    score += 45
                elif max_mag >= 6.0:
                    score += 35
                elif max_mag >= 5.0:
                    score += 25
                elif max_mag >= 4.0:
                    score += 15
                elif max_mag >= 3.0:
                    score += 8

            if nearest_dist is not None:
                nearest_distance_km = nearest_dist
                nearest_magnitude = nearest_mag if nearest_mag is not None else "unavailable"
                if nearest_dist <= 100:
                    score += 30
                elif nearest_dist <= 300:
                    score += 20
                elif nearest_dist <= 700:
                    score += 10

            score += min(tsunami_24h * 12, 24)
            eq_index = max(0, min(100, score))
            eq_risk = _risk_from_index(eq_index)

        return [
            {
                "entity_id": "sensor.earthquake_risk",
                "name": "Earthquake risk",
                "value": eq_risk,
                "source": source,
                "icon": "mdi:pulse",
            },
            {
                "entity_id": "sensor.earthquake_index",
                "name": "Earthquake index",
                "value": eq_index,
                "unit": "/100",
                "source": source,
                "icon": "mdi:chart-line",
            },
            {
                "entity_id": "sensor.earthquake_events_24h",
                "name": "Earthquakes 24h",
                "value": count_24h,
                "source": source,
                "icon": "mdi:clock-alert-outline",
            },
            {
                "entity_id": "sensor.earthquake_events_7d",
                "name": "Earthquakes 7d",
                "value": count_7d,
                "source": source,
                "icon": "mdi:calendar-week",
            },
            {
                "entity_id": "sensor.earthquake_max_magnitude_7d",
                "name": "Earthquake max magnitude 7d",
                "value": max_mag_7d,
                "unit": "M",
                "source": source,
                "icon": "mdi:magnitude",
            },
            {
                "entity_id": "sensor.earthquake_nearest_distance_km",
                "name": "Nearest earthquake distance",
                "value": nearest_distance_km,
                "unit": "km",
                "source": source,
                "icon": "mdi:map-marker-distance",
            },
            {
                "entity_id": "sensor.earthquake_nearest_magnitude",
                "name": "Nearest earthquake magnitude",
                "value": nearest_magnitude,
                "unit": "M",
                "source": source,
                "icon": "mdi:chart-bubble",
            },
            {
                "entity_id": "sensor.earthquake_latest_time",
                "name": "Latest earthquake time",
                "value": latest_time,
                "source": source,
                "icon": "mdi:clock-outline",
            },
            {
                "entity_id": "sensor.earthquake_latest_place",
                "name": "Latest earthquake place",
                "value": latest_place,
                "source": source,
                "icon": "mdi:map-marker",
            },
            {
                "entity_id": "sensor.earthquake_tsunami_events_24h",
                "name": "Tsunami-flagged earthquakes 24h",
                "value": tsunami_24h,
                "source": source,
                "icon": "mdi:waves-arrow-up",
            },
            {
                "entity_id": "sensor.earthquake_event_url",
                "name": "Nearest earthquake event URL",
                "value": event_url,
                "source": source,
                "icon": "mdi:link-variant",
            },
            {
                "entity_id": "sensor.earthquake_source",
                "name": "Earthquake source",
                "value": source,
                "source": source,
                "icon": "mdi:database-search-outline",
            },
        ]

    def _build_wildfire_metrics(
        self,
        *,
        latitude: float,
        longitude: float,
        gdacs_events: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        """Build wildfire metrics from GDACS current wildfire events."""
        source = "gdacs_rss" if isinstance(gdacs_events, list) else "unavailable"

        wildfire_risk: Any = "unavailable"
        wildfire_index: Any = "unavailable"
        active_events: Any = "unavailable"
        high_alert_events: Any = "unavailable"
        max_alert_level: Any = "unavailable"
        nearest_distance_km: Any = "unavailable"
        nearest_country: Any = "unavailable"
        nearest_title: Any = "unavailable"
        nearest_link: Any = "unavailable"
        nearest_icon_url: Any = "unavailable"

        if isinstance(gdacs_events, list):
            wildfire_events = [
                event
                for event in gdacs_events
                if event.get("is_current") is True and event.get("event_type") == "WF"
            ]
            active_events = len(wildfire_events)
            high_alert_events = sum(
                1
                for event in wildfire_events
                if str(event.get("alert_level") or "").lower() in {"orange", "red"}
            )

            if wildfire_events:
                max_alert_rank = max(
                    _alert_level_rank(str(event.get("alert_level"))) for event in wildfire_events
                )
                if max_alert_rank >= 4:
                    max_alert_level = "red"
                elif max_alert_rank >= 3:
                    max_alert_level = "orange"
                elif max_alert_rank >= 2:
                    max_alert_level = "green"
                else:
                    max_alert_level = "unknown"

                nearest_event: dict[str, Any] | None = None
                nearest_dist = 100_000.0
                for event in wildfire_events:
                    ev_lat = _optional_float(event.get("latitude"))
                    ev_lon = _optional_float(event.get("longitude"))
                    if ev_lat is None or ev_lon is None:
                        continue
                    dist = _haversine_km(latitude, longitude, ev_lat, ev_lon)
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_event = event

                score = min(active_events * 2, 26) + min(high_alert_events * 12, 32)
                score += _alert_level_rank(str(max_alert_level)) * 8

                if nearest_event is not None:
                    nearest_distance_km = round(nearest_dist, 1)
                    nearest_country = str(nearest_event.get("country") or "unknown")
                    nearest_title = str(nearest_event.get("title") or "unknown")
                    nearest_link = str(nearest_event.get("link") or "unavailable")
                    nearest_icon_url = str(nearest_event.get("icon_url") or "unavailable")
                    if nearest_dist <= 500:
                        score += 30
                    elif nearest_dist <= 1500:
                        score += 20
                    elif nearest_dist <= 3500:
                        score += 10

                wildfire_index = max(0, min(100, score))
                wildfire_risk = _risk_from_index(wildfire_index)
            else:
                wildfire_index = 0
                wildfire_risk = "very_low"
                max_alert_level = "none"

        return [
            {
                "entity_id": "sensor.wildfire_risk",
                "name": "Wildfire risk",
                "value": wildfire_risk,
                "source": source,
                "icon": "mdi:fire-alert",
            },
            {
                "entity_id": "sensor.wildfire_index",
                "name": "Wildfire index",
                "value": wildfire_index,
                "unit": "/100",
                "source": source,
                "icon": "mdi:chart-line",
            },
            {
                "entity_id": "sensor.wildfire_active_events_global",
                "name": "Wildfire active events (global)",
                "value": active_events,
                "source": source,
                "icon": "mdi:fire",
            },
            {
                "entity_id": "sensor.wildfire_high_alert_events_global",
                "name": "Wildfire high-alert events (global)",
                "value": high_alert_events,
                "source": source,
                "icon": "mdi:alert-octagon",
            },
            {
                "entity_id": "sensor.wildfire_max_alert_level",
                "name": "Wildfire max alert level",
                "value": max_alert_level,
                "source": source,
                "icon": "mdi:alarm-light-outline",
            },
            {
                "entity_id": "sensor.wildfire_nearest_distance_km",
                "name": "Nearest wildfire distance",
                "value": nearest_distance_km,
                "unit": "km",
                "source": source,
                "icon": "mdi:map-marker-distance",
            },
            {
                "entity_id": "sensor.wildfire_nearest_country",
                "name": "Nearest wildfire country",
                "value": nearest_country,
                "source": source,
                "icon": "mdi:flag-outline",
            },
            {
                "entity_id": "sensor.wildfire_nearest_title",
                "name": "Nearest wildfire title",
                "value": nearest_title,
                "source": source,
                "icon": "mdi:text-box-outline",
            },
            {
                "entity_id": "sensor.wildfire_nearest_link",
                "name": "Nearest wildfire report URL",
                "value": nearest_link,
                "source": source,
                "icon": "mdi:link-variant",
            },
            {
                "entity_id": "sensor.wildfire_icon_url",
                "name": "Nearest wildfire icon URL",
                "value": nearest_icon_url,
                "source": source,
                "icon": "mdi:image-outline",
            },
            {
                "entity_id": "sensor.wildfire_source",
                "name": "Wildfire source",
                "value": source,
                "source": source,
                "icon": "mdi:database-search-outline",
            },
        ]

    def _build_hazard_metrics(
        self,
        *,
        latitude: float,
        longitude: float,
        gdacs_events: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        """Build multi-hazard summary metrics from GDACS current events."""
        source = "gdacs_rss" if isinstance(gdacs_events, list) else "unavailable"

        active_total: Any = "unavailable"
        high_alert_total: Any = "unavailable"
        top_event_type: Any = "unavailable"
        top_event_alert: Any = "unavailable"
        top_event_title: Any = "unavailable"
        top_event_country: Any = "unavailable"
        top_event_distance_km: Any = "unavailable"
        top_event_icon_url: Any = "unavailable"
        last_update: Any = "unavailable"

        if isinstance(gdacs_events, list):
            current_events = [event for event in gdacs_events if event.get("is_current") is True]
            active_total = len(current_events)
            high_alert_total = sum(
                1
                for event in current_events
                if str(event.get("alert_level") or "").lower() in {"orange", "red"}
            )

            if current_events:
                latest_ts = max(
                    _safe_int(event.get("published_ts"), 0) for event in current_events
                )
                if latest_ts > 0:
                    last_update = datetime.fromtimestamp(latest_ts, tz=UTC).isoformat()
                else:
                    last_update = "unknown"

                top_event: dict[str, Any] | None = None
                top_key = (-1, -100_000.0, -1)
                for event in current_events:
                    event_alert = str(event.get("alert_level") or "unknown")
                    rank = _alert_level_rank(event_alert)
                    ev_lat = _optional_float(event.get("latitude"))
                    ev_lon = _optional_float(event.get("longitude"))
                    dist = None
                    if ev_lat is not None and ev_lon is not None:
                        dist = _haversine_km(latitude, longitude, ev_lat, ev_lon)
                    dist_key = -(dist if dist is not None else 100_000.0)
                    pub_ts = _safe_int(event.get("published_ts"), 0)
                    key = (rank, dist_key, pub_ts)
                    if key > top_key:
                        top_key = key
                        top_event = event

                if top_event is not None:
                    top_event_type = str(top_event.get("event_type") or "unknown")
                    top_event_alert = str(top_event.get("alert_level") or "unknown")
                    top_event_title = str(top_event.get("title") or "unknown")
                    top_event_country = str(top_event.get("country") or "unknown")
                    top_event_icon_url = str(top_event.get("icon_url") or "unavailable")
                    ev_lat = _optional_float(top_event.get("latitude"))
                    ev_lon = _optional_float(top_event.get("longitude"))
                    if ev_lat is not None and ev_lon is not None:
                        top_event_distance_km = round(
                            _haversine_km(latitude, longitude, ev_lat, ev_lon),
                            1,
                        )
            else:
                active_total = 0
                high_alert_total = 0
                top_event_type = "none"
                top_event_alert = "none"
                top_event_title = "none"
                top_event_country = "none"
                top_event_distance_km = "unavailable"
                top_event_icon_url = "unavailable"
                last_update = "unknown"

        return [
            {
                "entity_id": "sensor.hazard_active_events_global",
                "name": "Hazard active events (global)",
                "value": active_total,
                "source": source,
                "icon": "mdi:alert-circle-outline",
            },
            {
                "entity_id": "sensor.hazard_high_alert_events_global",
                "name": "Hazard high-alert events (global)",
                "value": high_alert_total,
                "source": source,
                "icon": "mdi:alert-octagon-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_type",
                "name": "Top hazard event type",
                "value": top_event_type,
                "source": source,
                "icon": "mdi:shape-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_alert",
                "name": "Top hazard event alert",
                "value": top_event_alert,
                "source": source,
                "icon": "mdi:alarm-light-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_title",
                "name": "Top hazard event title",
                "value": top_event_title,
                "source": source,
                "icon": "mdi:text-box-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_country",
                "name": "Top hazard event country",
                "value": top_event_country,
                "source": source,
                "icon": "mdi:flag-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_distance_km",
                "name": "Top hazard event distance",
                "value": top_event_distance_km,
                "unit": "km",
                "source": source,
                "icon": "mdi:map-marker-distance",
            },
            {
                "entity_id": "sensor.hazard_top_event_icon_url",
                "name": "Top hazard event icon URL",
                "value": top_event_icon_url,
                "source": source,
                "icon": "mdi:image-outline",
            },
            {
                "entity_id": "sensor.hazard_last_update",
                "name": "Hazard feed last update",
                "value": last_update,
                "source": source,
                "icon": "mdi:clock-outline",
            },
            {
                "entity_id": "sensor.hazard_source",
                "name": "Hazard source",
                "value": source,
                "source": source,
                "icon": "mdi:database-search-outline",
            },
        ]

    def _select_hour_index(self, hourly: dict[str, Any]) -> int:
        """Pick index matching current local time or return 0."""
        times = hourly.get("time")
        if not isinstance(times, list) or not times:
            return 0

        tz = dt_util.get_time_zone(self.hass.config.time_zone) or UTC
        now_local = dt_util.now().astimezone(tz)
        for idx, raw_time in enumerate(times):
            if not isinstance(raw_time, str):
                continue
            parsed = dt_util.parse_datetime(raw_time)
            if parsed is None:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=tz)
            if parsed >= now_local:
                return idx
        return 0

    def _build_internal_metrics(
        self,
        *,
        latitude: float,
        longitude: float,
        weather_data: dict[str, Any] | None,
        marine_data: dict[str, Any] | None,
        air_data: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Build metrics from remote APIs without synthetic substitute values."""
        weather_hourly = weather_data.get("hourly", {}) if isinstance(weather_data, dict) else {}
        marine_hourly = marine_data.get("hourly", {}) if isinstance(marine_data, dict) else {}
        air_hourly = air_data.get("hourly", {}) if isinstance(air_data, dict) else {}

        weather_idx = self._select_hour_index(weather_hourly)
        marine_idx = self._select_hour_index(marine_hourly)
        air_idx = self._select_hour_index(air_hourly)

        def hourly_float(
            hourly: dict[str, Any], key: str, idx: int, digits: int | None = None
        ) -> float | None:
            value = _hourly_value(hourly, key, idx, None)
            return _optional_float(value, digits)

        def hourly_int(hourly: dict[str, Any], key: str, idx: int) -> int | None:
            value = _hourly_value(hourly, key, idx, None)
            return _optional_int(value)

        def metric(
            entity_id: str,
            name: str,
            value: Any,
            unit: str | None = None,
            icon: str | None = None,
        ) -> dict[str, Any]:
            item: dict[str, Any] = {
                "entity_id": entity_id,
                "name": name,
                "value": "unavailable" if value is None else value,
                "source": "internal_api",
            }
            if unit is not None:
                item["unit"] = unit
            if icon is not None:
                item["icon"] = icon
            return item

        temperature = hourly_float(weather_hourly, "temperature_2m", weather_idx, 1)
        apparent_temperature = hourly_float(
            weather_hourly, "apparent_temperature", weather_idx, 1
        )
        precipitation_probability = hourly_int(
            weather_hourly, "precipitation_probability", weather_idx
        )
        precipitation = hourly_float(weather_hourly, "precipitation", weather_idx, 1)
        weather_code = hourly_int(weather_hourly, "weather_code", weather_idx)
        uv_index = hourly_float(weather_hourly, "uv_index", weather_idx, 1)
        wind_speed = hourly_float(weather_hourly, "wind_speed_10m", weather_idx, 1)
        pressure = hourly_int(weather_hourly, "surface_pressure", weather_idx)
        humidity = hourly_int(weather_hourly, "relative_humidity_2m", weather_idx)

        rain_next_6h: int | None = None
        weather_rain = weather_hourly.get("precipitation_probability")
        if isinstance(weather_rain, list) and weather_rain:
            rain_window = weather_rain[weather_idx : weather_idx + 6]
            numeric = [_optional_float(val) for val in rain_window]
            numeric = [val for val in numeric if val is not None]
            if numeric:
                rain_next_6h = int(round(max(numeric)))

        sea_temperature = hourly_float(
            marine_hourly, "sea_surface_temperature", marine_idx, 1
        )
        sea_temperature_3h = hourly_float(
            marine_hourly, "sea_surface_temperature", marine_idx + 3, 1
        )
        sea_temperature_6h = hourly_float(
            marine_hourly, "sea_surface_temperature", marine_idx + 6, 1
        )
        wave_height = hourly_float(marine_hourly, "wave_height", marine_idx, 2)
        wave_period = hourly_float(marine_hourly, "wave_period", marine_idx, 1)

        aqi = hourly_int(air_hourly, "european_aqi", air_idx)
        pm25 = hourly_float(air_hourly, "pm2_5", air_idx, 1)
        pm10 = hourly_float(air_hourly, "pm10", air_idx, 1)
        ozone = hourly_float(air_hourly, "ozone", air_idx, 1)
        no2 = hourly_float(air_hourly, "nitrogen_dioxide", air_idx, 1)
        so2 = hourly_float(air_hourly, "sulphur_dioxide", air_idx, 1)
        co = hourly_int(air_hourly, "carbon_monoxide", air_idx)
        dust_now = hourly_float(air_hourly, "dust", air_idx, 1)
        dust_6h = hourly_float(air_hourly, "dust", air_idx + 6, 1)

        pollen_grass = hourly_int(air_hourly, "grass_pollen", air_idx)
        pollen_birch = hourly_int(air_hourly, "birch_pollen", air_idx)
        pollen_alder = hourly_int(air_hourly, "alder_pollen", air_idx)
        pollen_olive = hourly_int(air_hourly, "olive_pollen", air_idx)
        pollen_ragweed = hourly_int(air_hourly, "ragweed_pollen", air_idx)
        pollen_mugwort = hourly_int(air_hourly, "mugwort_pollen", air_idx)
        pollen_values = [
            pollen_grass,
            pollen_birch,
            pollen_alder,
            pollen_olive,
            pollen_ragweed,
            pollen_mugwort,
        ]
        pollen_total = sum(pollen_values) if all(v is not None for v in pollen_values) else None

        ambrosia_risk: str | None = None
        if pollen_ragweed is not None:
            ambrosia_risk = "low"
            if pollen_ragweed > 50:
                ambrosia_risk = "very_high"
            elif pollen_ragweed > 20:
                ambrosia_risk = "high"
            elif pollen_ragweed > 5:
                ambrosia_risk = "moderate"

        dust_level = _dust_level(dust_now) if dust_now is not None else None
        allergy_index = (
            _allergy_index(float(pollen_total), float(dust_now), float(aqi))
            if pollen_total is not None and dust_now is not None and aqi is not None
            else None
        )
        asthma_risk = (
            _asthma_risk(float(aqi), float(pm25), float(dust_now), float(pollen_total))
            if aqi is not None
            and pm25 is not None
            and dust_now is not None
            and pollen_total is not None
            else None
        )

        beach_flag: str | None = None
        if wave_height is not None and wind_speed is not None:
            beach_flag = "green"
            if wave_height > 2.0 or wind_speed > 40:
                beach_flag = "red"
            elif wave_height > 1.2 or wind_speed > 25:
                beach_flag = "yellow"

        beach_danger_index: str | None = None
        if beach_flag is not None and uv_index is not None:
            beach_danger_index = "Low"
            if beach_flag == "red" or uv_index > 10:
                beach_danger_index = "High"
            elif beach_flag == "yellow" or uv_index > 8:
                beach_danger_index = "Medium"

        beach_crowding: str | None = None
        if temperature is not None and precipitation_probability is not None:
            hour = dt_util.now().hour
            weekday = dt_util.now().weekday()
            crowd_score = 0
            if 11 <= hour <= 14:
                crowd_score += 3
            elif 10 <= hour <= 16:
                crowd_score += 2
            elif 9 <= hour <= 18:
                crowd_score += 1
            if weekday >= 5:
                crowd_score += 2
            if temperature > 25 and precipitation_probability < 20:
                crowd_score += 2
            elif temperature > 20 and precipitation_probability < 40:
                crowd_score += 1
            if precipitation_probability > 50:
                crowd_score -= 3

            if crowd_score >= 6:
                beach_crowding = "very_crowded"
            elif crowd_score >= 4:
                beach_crowding = "crowded"
            elif crowd_score >= 2:
                beach_crowding = "normal"
            else:
                beach_crowding = "empty"

        beach_comfort: int | None = None
        if (
            beach_flag is not None
            and sea_temperature is not None
            and uv_index is not None
            and beach_crowding is not None
        ):
            score = 10
            if beach_flag == "red":
                score -= 5
            elif beach_flag == "yellow":
                score -= 2
            if sea_temperature < 18:
                score -= 2
            elif sea_temperature < 20:
                score -= 1
            elif sea_temperature >= 24:
                score += 1
            if uv_index > 10:
                score -= 2
            elif uv_index > 8:
                score -= 1
            if beach_crowding == "very_crowded":
                score -= 1
            beach_comfort = max(0, min(10, score))

        beach_recommendation: str | None = None
        if (
            beach_comfort is not None
            and beach_flag is not None
            and precipitation_probability is not None
        ):
            beach_recommendation = "Not ideal"
            if (
                beach_comfort >= 7
                and beach_flag == "green"
                and precipitation_probability < 20
            ):
                beach_recommendation = "Recommended"

        weather_summary = (
            _weather_summary(float(temperature), float(precipitation_probability))
            if temperature is not None and precipitation_probability is not None
            else None
        )
        waqi_proxy = aqi + 12 if aqi is not None else None

        return [
            metric("sensor.weather_summary", "Weather summary", weather_summary),
            metric("sensor.weather_code", "Weather code", weather_code),
            metric(
                "sensor.precipitation_probability",
                "Precipitation probability",
                precipitation_probability,
                "%",
            ),
            metric("sensor.precipitation", "Precipitation", precipitation, "mm"),
            metric("sensor.uv_index", "UV index", uv_index),
            metric(
                "sensor.rain_next_6h",
                "Rain probability next 6h",
                rain_next_6h,
                "%",
            ),
            metric("sensor.wind_speed", "Wind speed", wind_speed, "km/h"),
            metric("sensor.pressure", "Pressure", pressure, "hPa"),
            metric("sensor.humidity", "Humidity", humidity, "%"),
            metric(
                "sensor.apparent_temperature",
                "Apparent temperature",
                apparent_temperature if apparent_temperature is not None else temperature,
                "degC",
            ),
            metric(
                "sensor.sea_temperature_openmeteo",
                "Sea temperature",
                sea_temperature,
                "degC",
            ),
            metric(
                "sensor.sea_temperature_openmeteo_3h",
                "Sea temperature +3h",
                sea_temperature_3h,
                "degC",
            ),
            metric(
                "sensor.sea_temperature_openmeteo_6h",
                "Sea temperature +6h",
                sea_temperature_6h,
                "degC",
            ),
            metric("sensor.wave_height", "Wave height", wave_height, "m"),
            metric("sensor.wave_period", "Wave period", wave_period, "s"),
            metric("sensor.pollen_total", "Pollen total", pollen_total, "grains/m3"),
            metric("sensor.pollen_birch", "Pollen birch", pollen_birch, "grains/m3"),
            metric("sensor.pollen_alder", "Pollen alder", pollen_alder, "grains/m3"),
            metric("sensor.pollen_grass", "Pollen grass", pollen_grass, "grains/m3"),
            metric("sensor.pollen_olive", "Pollen olive", pollen_olive, "grains/m3"),
            metric("sensor.pollen_ragweed", "Pollen ragweed", pollen_ragweed, "grains/m3"),
            metric("sensor.pollen_ambrosia", "Pollen ambrosia", pollen_ragweed, "grains/m3"),
            metric("sensor.ambrosia_risk", "Ambrosia risk", ambrosia_risk),
            metric("sensor.allergy_index", "Allergy index", allergy_index, "/100"),
            metric("sensor.asthma_risk", "Asthma risk", asthma_risk),
            metric("sensor.pollen_mugwort", "Pollen mugwort", pollen_mugwort, "grains/m3"),
            metric("sensor.air_quality_european_aqi", "European AQI", aqi, "AQI"),
            metric("sensor.air_quality_pm25", "PM2.5", pm25, "ug/m3"),
            metric("sensor.air_quality_pm10", "PM10", pm10, "ug/m3"),
            metric("sensor.air_quality_ozone", "Ozone (O3)", ozone, "ug/m3"),
            metric("sensor.air_quality_no2", "Nitrogen dioxide", no2, "ug/m3"),
            metric("sensor.air_quality_so2", "Sulfur dioxide", so2, "ug/m3"),
            metric("sensor.air_quality_co", "Carbon monoxide", co, "ug/m3"),
            metric("sensor.waqi_barcelona", "WAQI proxy", waqi_proxy),
            metric("sensor.saharan_dust_level", "Saharan dust level", dust_level),
            metric(
                "sensor.saharan_dust_forecast_6h",
                "Saharan dust forecast +6h",
                dust_6h,
                "ug/m3",
            ),
            metric("sensor.beach_flag_calculated", "Beach flag (calculated)", beach_flag),
            metric("sensor.beach_danger_index", "Beach danger index", beach_danger_index),
            metric(
                "sensor.beach_crowding_estimate",
                "Beach crowding estimate",
                beach_crowding,
            ),
            metric("sensor.beach_comfort_index", "Beach comfort index", beach_comfort, "/10"),
            metric("sensor.beach_recommendation", "Beach recommendation", beach_recommendation),
        ]

    def _build_forecast_daily(
        self,
        *,
        forecast_days: int,
        weather_data: dict[str, Any] | None,
        marine_data: dict[str, Any] | None,
        air_data: dict[str, Any] | None,
        mosquito_baseline_index: int | None,
        jellyfish_baseline_risk: str,
        tick_baseline_index: int | None,
    ) -> list[dict[str, Any]]:
        """Build 1..7 day forecast summary."""
        weather_daily = weather_data.get("daily", {}) if isinstance(weather_data, dict) else {}
        weather_days = weather_daily.get("time")
        if not isinstance(weather_days, list) or not weather_days:
            return []

        marine_hourly = marine_data.get("hourly", {}) if isinstance(marine_data, dict) else {}
        air_hourly = air_data.get("hourly", {}) if isinstance(air_data, dict) else {}

        result: list[dict[str, Any]] = []
        for idx, day in enumerate(weather_days[:forecast_days]):
            if not isinstance(day, str):
                continue

            temp_max = round(
                _safe_float(_hourly_value(weather_daily, "temperature_2m_max", idx, 0.0), 0.0), 1
            )
            temp_min = round(
                _safe_float(_hourly_value(weather_daily, "temperature_2m_min", idx, 0.0), 0.0), 1
            )
            rain_prob_max = _safe_int(
                _hourly_value(weather_daily, "precipitation_probability_max", idx, 0), 0
            )
            rain_sum = round(
                _safe_float(_hourly_value(weather_daily, "precipitation_sum", idx, 0.0), 0.0), 1
            )
            uv_max = round(
                _safe_float(_hourly_value(weather_daily, "uv_index_max", idx, 0.0), 0.0), 1
            )
            wind_max = round(
                _safe_float(_hourly_value(weather_daily, "wind_speed_10m_max", idx, 0.0), 0.0), 1
            )
            weather_code = _safe_int(_hourly_value(weather_daily, "weather_code", idx, 0), 0)

            sea_values = _daily_hourly_values(marine_hourly, "sea_surface_temperature", day)
            wave_values = _daily_hourly_values(marine_hourly, "wave_height", day)
            wave_period_values = _daily_hourly_values(marine_hourly, "wave_period", day)
            aqi_values = _daily_hourly_values(air_hourly, "european_aqi", day)
            pm25_values = _daily_hourly_values(air_hourly, "pm2_5", day)
            dust_values = _daily_hourly_values(air_hourly, "dust", day)
            pollen_grass = _daily_hourly_values(air_hourly, "grass_pollen", day)
            pollen_birch = _daily_hourly_values(air_hourly, "birch_pollen", day)
            pollen_alder = _daily_hourly_values(air_hourly, "alder_pollen", day)
            pollen_olive = _daily_hourly_values(air_hourly, "olive_pollen", day)
            pollen_ragweed = _daily_hourly_values(air_hourly, "ragweed_pollen", day)
            pollen_mugwort = _daily_hourly_values(air_hourly, "mugwort_pollen", day)

            sea_temp_avg = round(sum(sea_values) / len(sea_values), 1) if sea_values else 0.0
            wave_height_max = round(max(wave_values), 2) if wave_values else 0.0
            wave_period_avg = (
                round(sum(wave_period_values) / len(wave_period_values), 1)
                if wave_period_values
                else 0.0
            )
            aqi_max = int(round(max(aqi_values))) if aqi_values else 0
            pm25_max = round(max(pm25_values), 1) if pm25_values else 0.0
            dust_max = round(max(dust_values), 1) if dust_values else 0.0
            pollen_total = int(
                round(
                    (
                        (sum(pollen_grass) / len(pollen_grass) if pollen_grass else 0.0)
                        + (sum(pollen_birch) / len(pollen_birch) if pollen_birch else 0.0)
                        + (sum(pollen_alder) / len(pollen_alder) if pollen_alder else 0.0)
                        + (sum(pollen_olive) / len(pollen_olive) if pollen_olive else 0.0)
                        + (sum(pollen_ragweed) / len(pollen_ragweed) if pollen_ragweed else 0.0)
                        + (sum(pollen_mugwort) / len(pollen_mugwort) if pollen_mugwort else 0.0)
                    )
                )
            )

            allergy_index = _allergy_index(float(pollen_total), float(dust_max), float(aqi_max))
            asthma_risk = _asthma_risk(
                float(aqi_max), float(pm25_max), float(dust_max), float(pollen_total)
            )

            beach_flag = "green"
            if wave_height_max > 2.0 or wind_max > 40:
                beach_flag = "red"
            elif wave_height_max > 1.2 or wind_max > 25:
                beach_flag = "yellow"

            beach_score = 10
            if beach_flag == "red":
                beach_score -= 5
            elif beach_flag == "yellow":
                beach_score -= 2
            if sea_temp_avg < 18:
                beach_score -= 2
            elif sea_temp_avg < 20:
                beach_score -= 1
            elif sea_temp_avg >= 24:
                beach_score += 1
            if uv_max > 10:
                beach_score -= 2
            elif uv_max > 8:
                beach_score -= 1
            if rain_prob_max > 60:
                beach_score -= 2
            elif rain_prob_max > 30:
                beach_score -= 1
            beach_score = max(0, min(10, beach_score))

            mosquito_risk_est = (
                _forecast_mosquito_risk(
                    baseline_index=mosquito_baseline_index,
                    temp_min=temp_min,
                    temp_max=temp_max,
                    rain_probability_max=rain_prob_max,
                    wind_max_kmh=wind_max,
                )
                if mosquito_baseline_index is not None
                else "unavailable"
            )
            jellyfish_risk_est = _forecast_jellyfish_risk(
                baseline_risk=jellyfish_baseline_risk,
                sea_temp_avg=sea_temp_avg,
                wave_height_max=wave_height_max,
                wind_max_kmh=wind_max,
            )
            tick_risk_est = (
                _forecast_tick_risk(
                    baseline_index=tick_baseline_index,
                    temp_min=temp_min,
                    temp_max=temp_max,
                    rain_probability_max=rain_prob_max,
                    wind_max_kmh=wind_max,
                )
                if tick_baseline_index is not None
                else "unavailable"
            )

            result.append(
                {
                    "date": day,
                    "weather_code": weather_code,
                    "temp_min": temp_min,
                    "temp_max": temp_max,
                    "rain_probability_max": rain_prob_max,
                    "rain_sum_mm": rain_sum,
                    "uv_max": uv_max,
                    "wind_max_kmh": wind_max,
                    "sea_temp_avg": sea_temp_avg,
                    "wave_height_max": wave_height_max,
                    "wave_period_avg": wave_period_avg,
                    "aqi_max": aqi_max,
                    "dust_max": dust_max,
                    "pollen_total_est": pollen_total,
                    "allergy_index": allergy_index,
                    "asthma_risk": asthma_risk,
                    "beach_flag": beach_flag,
                    "beach_score": beach_score,
                    "mosquito_risk_est": mosquito_risk_est,
                    "jellyfish_risk_est": jellyfish_risk_est,
                    "tick_risk_est": tick_risk_est,
                }
            )

        return result

    def _decorate_entity_icons(self, metrics: list[dict[str, Any]]) -> None:
        """Attach icon URLs (PNG/WebP/GIF) to each metric."""
        weather_code: int | None = None
        for metric in metrics:
            if metric.get("entity_id") != "sensor.weather_code":
                continue
            weather_code = _optional_int(metric.get("value"))
            break

        for metric in metrics:
            entity_id = metric.get("entity_id")
            if not isinstance(entity_id, str):
                continue
            emoji_code = _metric_emoji_code(entity_id, weather_code)
            if emoji_code is None:
                continue

            bundle = _noto_icon_bundle(emoji_code)
            metric["icon_emoji"] = bundle["emoji_code"]
            metric["icon_url"] = bundle["icon_url"]
            metric["icon_webp_url"] = bundle["icon_webp_url"]
            metric["icon_gif_url"] = bundle["icon_gif_url"]

            value = metric.get("value")
            if entity_id == "sensor.tick_icon_url":
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    metric["icon_external_url"] = value
            elif entity_id == "sensor.tiger_mosquito_icon_url":
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    metric["icon_external_url"] = value
            elif entity_id in {
                "sensor.wildfire_icon_url",
                "sensor.hazard_top_event_icon_url",
                "sensor.earthquake_event_url",
                "sensor.wildfire_nearest_link",
            }:
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    metric["icon_external_url"] = value
            elif entity_id == "sensor.jellyfish_icon_code":
                if isinstance(value, str) and value not in {"", "unknown", "unavailable"}:
                    metric["icon_external_code"] = value

    def _decorate_forecast_icons(self, forecast_daily: list[dict[str, Any]]) -> None:
        """Attach icon URLs to each forecast day row."""
        mosquito_bundle = _noto_icon_bundle("1f99f")
        jellyfish_bundle = _noto_icon_bundle("1f41f")
        tick_bundle = _noto_icon_bundle("1f41b")

        for day in forecast_daily:
            if not isinstance(day, dict):
                continue
            weather_code = _optional_int(day.get("weather_code"))
            weather_bundle = _noto_icon_bundle(_weather_emoji_code(weather_code))

            day["weather_icon_emoji"] = weather_bundle["emoji_code"]
            day["weather_icon_url"] = weather_bundle["icon_url"]
            day["weather_icon_webp_url"] = weather_bundle["icon_webp_url"]
            day["weather_icon_gif_url"] = weather_bundle["icon_gif_url"]

            day["mosquito_icon_gif_url"] = mosquito_bundle["icon_gif_url"]
            day["jellyfish_icon_gif_url"] = jellyfish_bundle["icon_gif_url"]
            day["tick_icon_gif_url"] = tick_bundle["icon_gif_url"]

    def _build_icon_catalog(
        self,
        *,
        metrics: list[dict[str, Any]],
        forecast_daily: list[dict[str, Any]],
        jellyfish_data: dict[str, Any] | None,
        mosquito_data: dict[str, Any] | None,
        tick_data: dict[str, Any] | None,
        earthquake_data: dict[str, Any] | None,
        gdacs_events: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Build icon catalog for external reuse."""
        weather_code: int | None = None
        for metric in metrics:
            if metric.get("entity_id") == "sensor.weather_code":
                weather_code = _optional_int(metric.get("value"))
                break
        weather_bundle = _noto_icon_bundle(_weather_emoji_code(weather_code))

        entity_icons: dict[str, dict[str, Any]] = {}
        icon_keys = (
            "icon",
            "icon_emoji",
            "icon_url",
            "icon_webp_url",
            "icon_gif_url",
            "icon_external_url",
            "icon_external_code",
        )
        for metric in metrics:
            entity_id = metric.get("entity_id")
            if not isinstance(entity_id, str):
                continue
            payload: dict[str, Any] = {}
            for key in icon_keys:
                value = metric.get(key)
                if isinstance(value, str) and value:
                    payload[key] = value
            if payload:
                entity_icons[entity_id] = payload

        catalog: dict[str, Any] = {
            "weather_current": {
                "weather_code": weather_code if weather_code is not None else "unavailable",
                **weather_bundle,
            },
            "categories": {
                "weather": weather_bundle,
                "marine": _noto_icon_bundle("1f30a"),
                "allergy": _noto_icon_bundle("1f927"),
                "air_quality": _noto_icon_bundle("1f637"),
                "jellyfish": _noto_icon_bundle("1f41f"),
                "tiger_mosquito": _noto_icon_bundle("1f99f"),
                "ticks": _noto_icon_bundle("1f41b"),
                "earthquakes": _noto_icon_bundle("1f30b"),
                "wildfire": _noto_icon_bundle("1f525"),
                "hazards": _noto_icon_bundle("1f6a8"),
            },
            "entities": entity_icons,
        }

        if isinstance(jellyfish_data, dict):
            catalog["jellyfish"] = {
                "status_icon_code": jellyfish_data.get("status_icon"),
                "nearest_beach": jellyfish_data.get("beach_name"),
                **_noto_icon_bundle("1f41f"),
            }
        if isinstance(mosquito_data, dict):
            catalog["tiger_mosquito"] = {
                "latest_report": mosquito_data.get("latest_received_at"),
                "external_icon_url": mosquito_data.get("icon_url"),
                **_noto_icon_bundle("1f99f"),
            }
        if isinstance(tick_data, dict):
            catalog["ticks"] = {
                "taxon": tick_data.get("taxon_name"),
                "external_icon_url": tick_data.get("icon_url"),
                "source": "iNaturalist",
                **_noto_icon_bundle("1f41b"),
            }
        if isinstance(earthquake_data, dict):
            catalog["earthquakes"] = {
                "source": "USGS",
                "count_24h": earthquake_data.get("count_24h"),
                "count_7d": earthquake_data.get("count_7d"),
                "max_magnitude_7d": earthquake_data.get("max_mag_7d"),
                "nearest_distance_km": earthquake_data.get("nearest_distance_km"),
                "event_url": earthquake_data.get("nearest_event_url"),
                **_noto_icon_bundle("1f30b"),
            }
        if isinstance(gdacs_events, list):
            current_events = [
                event for event in gdacs_events if isinstance(event, dict) and event.get("is_current") is True
            ]
            wf_events = [event for event in current_events if event.get("event_type") == "WF"]
            top_hazard_icon = None
            top_hazard_alert = "unknown"
            if current_events:
                top_event = max(
                    current_events,
                    key=lambda event: (
                        _alert_level_rank(str(event.get("alert_level"))),
                        _safe_int(event.get("published_ts"), 0),
                    ),
                )
                top_hazard_icon = top_event.get("icon_url")
                top_hazard_alert = top_event.get("alert_level")

            catalog["wildfire"] = {
                "source": "GDACS",
                "active_events_global": len(wf_events),
                "high_alert_events_global": sum(
                    1
                    for event in wf_events
                    if str(event.get("alert_level") or "").lower() in {"orange", "red"}
                ),
                "top_icon_url": wf_events[0].get("icon_url") if wf_events else None,
                **_noto_icon_bundle("1f525"),
            }
            catalog["hazards"] = {
                "source": "GDACS",
                "active_events_global": len(current_events),
                "top_alert_level": top_hazard_alert,
                "top_icon_url": top_hazard_icon,
                **_noto_icon_bundle("1f6a8"),
            }

        if forecast_daily:
            catalog["forecast_daily"] = [
                {
                    "date": day.get("date"),
                    "weather_code": day.get("weather_code"),
                    "weather_icon_url": day.get("weather_icon_url"),
                    "weather_icon_gif_url": day.get("weather_icon_gif_url"),
                    "mosquito_icon_gif_url": day.get("mosquito_icon_gif_url"),
                    "jellyfish_icon_gif_url": day.get("jellyfish_icon_gif_url"),
                    "tick_icon_gif_url": day.get("tick_icon_gif_url"),
                }
                for day in forecast_daily
                if isinstance(day, dict)
            ]

        return catalog

    def _apply_ha_sources(self, metrics: list[dict[str, Any]]) -> dict[str, int]:
        """Apply optional HA entity mappings on top of internal metrics."""
        source_mode = str(self._options[CONF_SOURCE_MODE])
        if source_mode == SOURCE_MODE_INTERNAL:
            return {"attempted": 0, "applied": 0, "missing": 0}

        source_map = self._options[CONF_SOURCES]
        if not isinstance(source_map, dict) or not source_map:
            return {"attempted": 0, "applied": 0, "missing": 0}

        metric_by_entity = {item["entity_id"]: item for item in metrics}
        attempted = 0
        applied = 0
        missing = 0

        for source_key, ha_entity_id in source_map.items():
            metric_id = _resolve_metric_id(source_key)
            if metric_id is None:
                continue
            metric = metric_by_entity.get(metric_id)
            if metric is None:
                continue

            attempted += 1
            state: State | None = self.hass.states.get(ha_entity_id)
            if state is None or state.state in INVALID_HA_STATES:
                missing += 1
                if source_mode == SOURCE_MODE_HA_ONLY:
                    metric["value"] = "unavailable"
                    metric["source"] = "ha_entity_missing"
                    metric["source_entity"] = ha_entity_id
                continue

            metric["value"] = _coerce_state_value(state.state, metric.get("value"))
            state_unit = state.attributes.get("unit_of_measurement")
            if isinstance(state_unit, str) and state_unit.strip():
                metric["unit"] = state_unit
            metric["source"] = "ha_entity"
            metric["source_entity"] = ha_entity_id
            applied += 1

        if source_mode == SOURCE_MODE_HA_ONLY:
            for metric in metrics:
                if metric.get("source") == "internal_api":
                    metric["value"] = "unavailable"
                    metric["source"] = "ha_only_unmapped"

        if source_mode == SOURCE_MODE_HYBRID and attempted == 0:
            for metric in metrics:
                if metric.get("source") != "ha_entity":
                    metric["source"] = "internal_api"

        return {"attempted": attempted, "applied": applied, "missing": missing}
