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
    CONF_DAILY_PLAN,
    CONF_DALY_PLAN,
    CONF_FORECAST_DAYS,
    CONF_PLANNER_MODE,
    CONF_TRACKING_ENTITIES,
    CONF_REFRESH_SECONDS,
    CONF_SOURCE_MODE,
    CONF_SOURCES,
    CONF_TIMEZONES,
    CONF_UV_TRACKING_ENTITIES,
    CONF_PERSONAS,
    DEFAULT_DAILY_PLAN,
    DEFAULT_TRACKING_ENTITIES,
    DEFAULT_TIMEZONES,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_PLANNER_MODE,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_SOURCE_MODE,
    INVALID_HA_STATES,
    SOURCE_KEY_ALIASES,
    SOURCE_MODE_HA_ONLY,
    SOURCE_MODE_HYBRID,
    SOURCE_MODE_INTERNAL,
    SUPPORTED_PLANNER_MODES,
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
_METEOALARM_ATOM_SPAIN = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-spain"
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
    "sensor.rip_current_risk": "1f30a",
    "sensor.rip_current_index": "1f30a",
    "sensor.heat_stress_risk": "1f321_fe0f",
    "sensor.heat_stress_index": "1f321_fe0f",
    "sensor.heat_index_c": "1f321_fe0f",
    "sensor.wet_bulb_c": "1f4a7",
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
    "sensor.aura_daily_plan_status": "1f4c5",
    "sensor.aura_planner_mode_default": "1f4c5",
    "sensor.aura_now_vs_3h_outdoor": "23f3",
    "sensor.aura_now_vs_3h_beach": "1f30a",
    "sensor.aura_now_vs_3h_summary": "1f5d2_fe0f",
    "sensor.aura_beach_pack_trigger": "1f392",
    "sensor.aura_beach_pack_list": "1f392",
    "sensor.aura_beach_notification_key": "1f514",
    "sensor.aura_beach_notification_state": "1f514",
    "sensor.uv_dose_sed_1h": "1f31e",
    "sensor.uv_dose_sed_today_est": "1f31e",
    "sensor.uv_dose_status": "1f31e",
    "sensor.wbgt_c": "1f321_fe0f",
    "sensor.dehydration_index": "1f4a7",
    "sensor.dehydration_risk": "1f4a7",
    "sensor.thunderstorm_risk": "26a1_fe0f",
    "sensor.thunderstorm_index": "26a1_fe0f",
    "sensor.thunderstorm_cape": "26a1_fe0f",
    "sensor.thunderstorm_nowcast_3h": "23f3",
    "sensor.tide_level_m": "1f30a",
    "sensor.tide_trend_3h": "1f30a",
    "sensor.tide_range_24h_m": "1f30a",
    "sensor.ocean_current_speed": "1f30a",
    "sensor.ocean_current_direction": "1f9ed",
    "sensor.current_risk": "1f6a9",
    "sensor.algae_bloom_risk": "1f9ab",
    "sensor.algae_bloom_index": "1f9ab",
    "sensor.algae_bloom_signal": "1f9ab",
    "sensor.algae_source": "1f9ab",
    "sensor.smoke_transport_risk": "1f32b_fe0f",
    "sensor.smoke_transport_index": "1f32b_fe0f",
    "sensor.smoke_transport_signal": "1f32b_fe0f",
    "sensor.smoke_source": "1f32b_fe0f",
    "sensor.cap_alert_risk": "1f6a8",
    "sensor.cap_alert_index": "1f6a8",
    "sensor.cap_alerts_active": "1f6a8",
    "sensor.cap_highest_severity": "1f6a8",
    "sensor.cap_top_event": "1f6a8",
    "sensor.cap_top_area": "1f6a8",
    "sensor.cap_top_expires": "1f6a8",
    "sensor.cap_source": "1f6a8",
    "sensor.bite_index": "1f99f",
    "sensor.bite_risk": "1f99f",
    "sensor.bite_outlook_3d": "1f99f",
}
_SKIN_TYPE_MED_J_M2: dict[int, int] = {
    1: 200,
    2: 250,
    3: 300,
    4: 450,
    5: 600,
    6: 1000,
}
_PERSONA_ID_PATTERN = re.compile(r"[^a-z0-9_]+")
_TRACKING_ID_PATTERN = re.compile(r"[^a-z0-9_]+")


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


def _normalize_persona_id(raw_value: Any, index: int) -> str:
    """Normalize persona id to ASCII token."""
    raw = str(raw_value or "").strip().lower()
    if not raw:
        raw = f"persona_{index + 1}"
    normalized = _PERSONA_ID_PATTERN.sub("_", raw).strip("_")
    if not normalized:
        normalized = f"persona_{index + 1}"
    return normalized[:48]


def _normalize_tracking_id(raw_value: Any, index: int) -> str:
    """Normalize tracker id to ASCII token."""
    raw = str(raw_value or "").strip().lower()
    if not raw:
        raw = f"tracker_{index + 1}"
    normalized = _TRACKING_ID_PATTERN.sub("_", raw).strip("_")
    if not normalized:
        normalized = f"tracker_{index + 1}"
    return normalized[:48]


def _normalize_planner_mode(raw_value: Any) -> str:
    """Normalize planner mode to one of supported values."""
    mode = str(raw_value or DEFAULT_PLANNER_MODE).strip().lower()
    if mode not in SUPPORTED_PLANNER_MODES:
        return DEFAULT_PLANNER_MODE
    return mode


def _coerce_bool(raw_value: Any, default: bool) -> bool:
    """Parse bool-like option values from YAML."""
    if raw_value is None:
        return default
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default
    if isinstance(raw_value, (int, float)):
        return raw_value != 0
    return default


def _clamp_float(value: Any, default: float, min_value: float, max_value: float) -> float:
    """Parse float and clamp to [min, max]."""
    parsed = _safe_float(value, default)
    return max(min_value, min(parsed, max_value))


def _normalize_personas(
    raw_personas: Any, *, default_planner_mode: str = DEFAULT_PLANNER_MODE
) -> list[dict[str, Any]]:
    """Normalize personas from YAML into canonical list."""
    rows: list[dict[str, Any]] = []
    if isinstance(raw_personas, dict):
        for key, payload in raw_personas.items():
            if isinstance(payload, dict):
                rows.append({"id": key, **payload})
            else:
                rows.append({"id": key})
    elif isinstance(raw_personas, list):
        rows = [row for row in raw_personas if isinstance(row, dict)]
    else:
        return []

    personas: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for idx, row in enumerate(rows):
        persona_id = _normalize_persona_id(row.get("id"), idx)
        base_id = persona_id
        suffix = 2
        while persona_id in used_ids:
            persona_id = f"{base_id}_{suffix}"
            suffix += 1
        used_ids.add(persona_id)

        name = str(row.get("name") or persona_id).strip() or persona_id
        skin_type = _safe_int(row.get("skin_type"), 3)
        if skin_type < 1:
            skin_type = 1
        if skin_type > 6:
            skin_type = 6

        person_entity_id = row.get("person_entity_id")
        if not isinstance(person_entity_id, str):
            person_entity_id = None
        elif not person_entity_id.strip():
            person_entity_id = None
        else:
            person_entity_id = person_entity_id.strip()

        tracker_entity_id = row.get("tracker_entity_id")
        if not isinstance(tracker_entity_id, str):
            tracker_entity_id = person_entity_id
        elif not tracker_entity_id.strip():
            tracker_entity_id = person_entity_id
        else:
            tracker_entity_id = tracker_entity_id.strip()

        enabled_raw = row.get("enabled", True)
        if isinstance(enabled_raw, str):
            enabled = enabled_raw.strip().lower() not in {"0", "false", "off", "no"}
        else:
            enabled = bool(enabled_raw)

        personas.append(
            {
                "id": persona_id,
                "name": name,
                "person_entity_id": person_entity_id,
                "tracker_entity_id": tracker_entity_id,
                "skin_type": skin_type,
                "spf": _clamp_float(row.get("spf", 1.0), 1.0, 1.0, 100.0),
                "shade_factor": _clamp_float(row.get("shade_factor", 1.0), 1.0, 0.2, 5.0),
                "uv_sensitivity": _clamp_float(
                    row.get("uv_sensitivity", 1.0), 1.0, 0.5, 2.5
                ),
                "heat_sensitivity": _clamp_float(
                    row.get("heat_sensitivity", 1.0), 1.0, 0.6, 1.8
                ),
                "planner_mode": _normalize_planner_mode(
                    row.get("planner_mode", default_planner_mode)
                ),
                "uv_exposure_factor": _clamp_float(
                    row.get("uv_exposure_factor", 1.0), 1.0, 0.0, 2.5
                ),
                "enabled": enabled,
            }
        )

    return personas


def _normalize_tracking_entities(raw_trackers: Any) -> list[dict[str, Any]]:
    """Normalize extra tracking entities from YAML."""
    if not isinstance(raw_trackers, list):
        return []

    rows: list[dict[str, Any]] = []
    for item in raw_trackers:
        if isinstance(item, str):
            entity_id = item.strip()
            if entity_id:
                rows.append({"entity_id": entity_id})
            continue
        if isinstance(item, dict):
            rows.append(item)

    trackers: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    used_entities: set[str] = set()
    for idx, row in enumerate(rows):
        entity_id = str(row.get("entity_id") or "").strip()
        if not entity_id:
            continue
        if entity_id in used_entities:
            continue
        used_entities.add(entity_id)

        tracker_id = _normalize_tracking_id(row.get("id", entity_id), idx)
        base_id = tracker_id
        suffix = 2
        while tracker_id in used_ids:
            tracker_id = f"{base_id}_{suffix}"
            suffix += 1
        used_ids.add(tracker_id)

        trackers.append(
            {
                "id": tracker_id,
                "entity_id": entity_id,
                "name": str(row.get("name") or tracker_id).strip() or tracker_id,
                "uv_exposure_factor": _clamp_float(
                    row.get("uv_exposure_factor", 1.0), 1.0, 0.0, 2.5
                ),
            }
        )
    return trackers


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

    planner_mode = _normalize_planner_mode(
        options.get(CONF_PLANNER_MODE, DEFAULT_PLANNER_MODE)
    )
    daily_plan = _coerce_bool(
        options.get(
            CONF_DAILY_PLAN,
            options.get(CONF_DALY_PLAN, DEFAULT_DAILY_PLAN),
        ),
        DEFAULT_DAILY_PLAN,
    )
    personas = _normalize_personas(
        options.get(CONF_PERSONAS, []),
        default_planner_mode=planner_mode,
    )
    raw_trackers = options.get(
        CONF_TRACKING_ENTITIES,
        options.get(CONF_UV_TRACKING_ENTITIES, DEFAULT_TRACKING_ENTITIES),
    )
    tracking_entities = _normalize_tracking_entities(raw_trackers)

    return {
        CONF_SOURCE_MODE: source_mode,
        CONF_REFRESH_SECONDS: refresh_seconds,
        CONF_FORECAST_DAYS: forecast_days,
        CONF_TIMEZONES: ",".join(normalized_timezones),
        CONF_SOURCES: sources,
        CONF_PERSONAS: personas,
        CONF_DAILY_PLAN: daily_plan,
        CONF_PLANNER_MODE: planner_mode,
        CONF_TRACKING_ENTITIES: tracking_entities,
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
        self._uv_sed_by_tracker: dict[str, float] = {}
        self._uv_sed_day: str = ""
        self._uv_sed_last_update: datetime | None = None

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
                    "weather_code,uv_index,wind_speed_10m,wind_direction_10m,surface_pressure,"
                    "relative_humidity_2m,cloud_cover,dew_point_2m,direct_radiation,"
                    "shortwave_radiation,cape"
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
                "hourly": (
                    "wave_height,wave_direction,wave_period,sea_surface_temperature,"
                    "sea_level_height_msl,ocean_current_velocity,ocean_current_direction"
                ),
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
        cap_task = self._async_fetch_cap_alerts()
        (
            (weather_data, weather_err),
            (marine_data, marine_err),
            (air_data, air_err),
            (jellyfish_data, jellyfish_err),
            (mosquito_data, mosquito_err),
            (tick_data, tick_err),
            (earthquake_data, earthquake_err),
            (gdacs_events, gdacs_err),
            (cap_data, cap_err),
        ) = await asyncio.gather(
            weather_task,
            marine_task,
            air_task,
            jellyfish_task,
            mosquito_task,
            tick_task,
            earthquake_task,
            gdacs_task,
            cap_task,
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
        climate_extra_metrics = self._build_climate_extra_metrics(
            metrics=metrics,
            weather_data=weather_data,
            marine_data=marine_data,
            air_data=air_data,
            personas=self._options.get(CONF_PERSONAS, []),
            tracking_entities=self._options.get(CONF_TRACKING_ENTITIES, []),
            gdacs_events=gdacs_events,
            cap_data=cap_data,
        )
        metrics.extend(jellyfish_metrics)
        metrics.extend(mosquito_metrics)
        metrics.extend(tick_metrics)
        metrics.extend(earthquake_metrics)
        metrics.extend(wildfire_metrics)
        metrics.extend(hazard_metrics)
        metrics.extend(climate_extra_metrics)
        exposure_persona_metrics = self._build_exposure_and_persona_metrics(
            metrics=metrics,
            personas=self._options.get(CONF_PERSONAS, []),
        )
        metrics.extend(exposure_persona_metrics)

        forecast_daily = self._build_forecast_daily(
            forecast_days=forecast_days,
            weather_data=weather_data,
            marine_data=marine_data,
            air_data=air_data,
            mosquito_baseline_index=mosquito_index_for_forecast,
            jellyfish_baseline_risk=jellyfish_risk_for_forecast,
            tick_baseline_index=tick_index_for_forecast,
        )
        daily_planner_metrics, planner_payload = self._build_daily_planner_metrics(
            metrics=metrics,
            weather_data=weather_data,
            marine_data=marine_data,
            air_data=air_data,
            personas=self._options.get(CONF_PERSONAS, []),
            daily_plan_enabled=_coerce_bool(
                self._options.get(CONF_DAILY_PLAN, DEFAULT_DAILY_PLAN),
                DEFAULT_DAILY_PLAN,
            ),
            default_planner_mode=_normalize_planner_mode(
                self._options.get(CONF_PLANNER_MODE, DEFAULT_PLANNER_MODE)
            ),
        )
        metrics.extend(daily_planner_metrics)
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
            cap_data=cap_data,
        )
        personas_meta: list[dict[str, Any]] = []
        raw_personas = self._options.get(CONF_PERSONAS, [])
        if isinstance(raw_personas, list):
            for persona in raw_personas:
                if not isinstance(persona, dict):
                    continue
                personas_meta.append(
                    {
                        "id": persona.get("id"),
                        "name": persona.get("name"),
                        "person_entity_id": persona.get("person_entity_id"),
                        "tracker_entity_id": persona.get("tracker_entity_id"),
                        "skin_type": persona.get("skin_type"),
                        "spf": persona.get("spf"),
                        "shade_factor": persona.get("shade_factor"),
                        "uv_sensitivity": persona.get("uv_sensitivity"),
                        "uv_exposure_factor": persona.get("uv_exposure_factor"),
                        "heat_sensitivity": persona.get("heat_sensitivity"),
                        "planner_mode": persona.get("planner_mode"),
                        "enabled": persona.get("enabled", True),
                    }
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
                    "cap": "ok" if cap_err is None else cap_err,
                },
                "icons": icon_catalog,
                "personas": personas_meta,
                "daily_plan": planner_payload,
                "daly_plan": planner_payload,
                "tracking_entities": self._options.get(CONF_TRACKING_ENTITIES, []),
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

    async def _async_fetch_cap_alerts(
        self,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch Meteoalarm CAP-like warning feed (Spain) and aggregate active alerts."""
        xml_text, xml_err = await self._async_fetch_text(_METEOALARM_ATOM_SPAIN)
        if not isinstance(xml_text, str):
            return None, xml_err or "cap_feed_unavailable"

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "cap": "urn:oasis:names:tc:emergency:cap:1.2",
        }
        try:
            root = ET.fromstring(xml_text.lstrip("\ufeff\r\n\t "))
        except ET.ParseError as err:
            return None, f"xml_parse_error:{err}"

        now_utc = datetime.now(tz=UTC)
        entries = root.findall("./atom:entry", ns)

        severity_rank = {
            "extreme": 4,
            "severe": 3,
            "moderate": 2,
            "minor": 1,
            "unknown": 0,
        }

        warnings: list[dict[str, Any]] = []
        for entry in entries:
            severity = str(entry.findtext("cap:severity", default="", namespaces=ns)).strip().lower()
            if not severity:
                severity = "unknown"
            event = str(entry.findtext("cap:event", default="", namespaces=ns)).strip() or "unknown"
            area = str(entry.findtext("cap:areaDesc", default="", namespaces=ns)).strip() or "unknown"
            certainty = (
                str(entry.findtext("cap:certainty", default="", namespaces=ns)).strip() or "unknown"
            )
            urgency = str(entry.findtext("cap:urgency", default="", namespaces=ns)).strip() or "unknown"
            status = str(entry.findtext("cap:status", default="", namespaces=ns)).strip() or "unknown"
            link_elem = entry.find("atom:link", ns)
            link = ""
            if link_elem is not None:
                link = str(link_elem.attrib.get("href", "")).strip()

            expires_raw = str(entry.findtext("cap:expires", default="", namespaces=ns)).strip()
            sent_raw = str(entry.findtext("cap:sent", default="", namespaces=ns)).strip()

            expires_at: datetime | None = None
            sent_at: datetime | None = None
            if expires_raw:
                parsed = dt_util.parse_datetime(expires_raw)
                if parsed is not None:
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    expires_at = parsed.astimezone(UTC)
            if sent_raw:
                parsed = dt_util.parse_datetime(sent_raw)
                if parsed is not None:
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    sent_at = parsed.astimezone(UTC)

            if expires_at is not None and expires_at < now_utc:
                continue

            warnings.append(
                {
                    "severity": severity,
                    "severity_rank": severity_rank.get(severity, 0),
                    "event": event,
                    "area": area,
                    "certainty": certainty,
                    "urgency": urgency,
                    "status": status,
                    "link": link if link else None,
                    "expires_at": expires_at.isoformat() if expires_at is not None else None,
                    "expires_ts": int(expires_at.timestamp()) if expires_at is not None else 0,
                    "sent_at": sent_at.isoformat() if sent_at is not None else None,
                    "sent_ts": int(sent_at.timestamp()) if sent_at is not None else 0,
                }
            )

        active_count = len(warnings)
        highest_severity = "unknown"
        cap_index = 0
        top_event = "none"
        top_area = "none"
        top_expires = "unknown"
        top_link: str | None = None

        if warnings:
            top = max(
                warnings,
                key=lambda item: (
                    _safe_int(item.get("severity_rank"), 0),
                    _safe_int(item.get("sent_ts"), 0),
                ),
            )
            highest_severity = str(top.get("severity") or "unknown")
            top_event = str(top.get("event") or "unknown")
            top_area = str(top.get("area") or "unknown")
            top_expires = str(top.get("expires_at") or "unknown")
            top_link = top.get("link")
            cap_index = min(
                100,
                max(
                    0,
                    _safe_int(top.get("severity_rank"), 0) * 22 + min(active_count, 10) * 6,
                ),
            )

        return (
            {
                "active_count": active_count,
                "highest_severity": highest_severity,
                "index": cap_index,
                "top_event": top_event,
                "top_area": top_area,
                "top_expires": top_expires,
                "top_link": top_link,
            },
            None,
        )

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

    def _build_exposure_and_persona_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        personas: Any,
    ) -> list[dict[str, Any]]:
        """Build rip-current/heat metrics and persona-specific exposure sensors."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}

        wave_height = _optional_float(values.get("sensor.wave_height"))
        wave_period = _optional_float(values.get("sensor.wave_period"))
        wind_speed = _optional_float(values.get("sensor.wind_speed"))
        rain_prob = _optional_float(values.get("sensor.precipitation_probability"))
        if rain_prob is None:
            rain_prob = _optional_float(values.get("sensor.rain_next_6h"))
        apparent_temperature = _optional_float(values.get("sensor.apparent_temperature"))
        humidity = _optional_float(values.get("sensor.humidity"))
        uv_index = _optional_float(values.get("sensor.uv_index"))

        rip_index: int | None = None
        rip_risk = "unavailable"
        if (
            wave_height is not None
            and wave_period is not None
            and wind_speed is not None
            and rain_prob is not None
        ):
            rip_index = _rip_current_index(
                wave_height_m=wave_height,
                wave_period_s=wave_period,
                wind_speed_kmh=wind_speed,
                rain_probability_pct=rain_prob,
            )
            rip_risk = _risk_from_index(rip_index)

        heat_index_c: float | None = None
        wet_bulb_c: float | None = None
        heat_stress_index: int | None = None
        heat_stress_risk = "unavailable"
        if apparent_temperature is not None and humidity is not None:
            heat_index_c = _heat_index_c(apparent_temperature, humidity)
            wet_bulb_c = _wet_bulb_c(apparent_temperature, humidity)
            score = 0.0
            if heat_index_c >= 54:
                score = 100
            elif heat_index_c >= 41:
                score = 82 + (heat_index_c - 41) * 1.4
            elif heat_index_c >= 32:
                score = 58 + (heat_index_c - 32) * 2.1
            elif heat_index_c >= 27:
                score = 35 + (heat_index_c - 27) * 4.6
            else:
                score = max(0.0, (heat_index_c - 18) * 2.6)
            heat_stress_index = max(0, min(100, int(round(score))))
            heat_stress_risk = _risk_from_index(heat_stress_index)

        result: list[dict[str, Any]] = [
            {
                "entity_id": "sensor.rip_current_risk",
                "name": "Rip current risk",
                "value": rip_risk,
                "source": "internal_model",
                "icon": "mdi:waves-arrow-right",
            },
            {
                "entity_id": "sensor.rip_current_index",
                "name": "Rip current index",
                "value": rip_index if rip_index is not None else "unavailable",
                "unit": "/100",
                "source": "internal_model",
                "icon": "mdi:chart-line",
            },
            {
                "entity_id": "sensor.heat_stress_risk",
                "name": "Heat stress risk",
                "value": heat_stress_risk,
                "source": "internal_model",
                "icon": "mdi:thermometer-alert",
            },
            {
                "entity_id": "sensor.heat_stress_index",
                "name": "Heat stress index",
                "value": heat_stress_index if heat_stress_index is not None else "unavailable",
                "unit": "/100",
                "source": "internal_model",
                "icon": "mdi:chart-line",
            },
            {
                "entity_id": "sensor.heat_index_c",
                "name": "Heat index",
                "value": heat_index_c if heat_index_c is not None else "unavailable",
                "unit": "degC",
                "source": "internal_model",
                "icon": "mdi:thermometer-high",
            },
            {
                "entity_id": "sensor.wet_bulb_c",
                "name": "Wet bulb temperature",
                "value": wet_bulb_c if wet_bulb_c is not None else "unavailable",
                "unit": "degC",
                "source": "internal_model",
                "icon": "mdi:thermometer-water",
            },
        ]

        if not isinstance(personas, list):
            return result

        for persona in personas:
            if not isinstance(persona, dict):
                continue
            if persona.get("enabled") is False:
                continue

            persona_id = str(persona.get("id") or "").strip()
            if not persona_id:
                continue
            persona_name = str(persona.get("name") or persona_id).strip() or persona_id
            skin_type = _safe_int(persona.get("skin_type"), 3)
            if skin_type < 1:
                skin_type = 1
            if skin_type > 6:
                skin_type = 6
            spf = _clamp_float(persona.get("spf", 1.0), 1.0, 1.0, 100.0)
            shade_factor = _clamp_float(persona.get("shade_factor", 1.0), 1.0, 0.2, 5.0)
            uv_sensitivity = _clamp_float(
                persona.get("uv_sensitivity", 1.0), 1.0, 0.5, 2.5
            )
            heat_sensitivity = _clamp_float(
                persona.get("heat_sensitivity", 1.0), 1.0, 0.6, 1.8
            )
            person_entity_id = persona.get("person_entity_id")
            if not isinstance(person_entity_id, str) or not person_entity_id.strip():
                person_entity_id = None
            else:
                person_entity_id = person_entity_id.strip()

            presence = "unknown"
            if person_entity_id is not None:
                state = self.hass.states.get(person_entity_id)
                if state is None:
                    presence = "unavailable"
                else:
                    presence = str(state.state or "unknown")

            burn_minutes = (
                _sunburn_minutes(
                    uv_index=uv_index,
                    skin_type=skin_type,
                    spf=spf,
                    shade_factor=shade_factor,
                    uv_sensitivity=uv_sensitivity,
                )
                if uv_index is not None
                else None
            )
            burn_risk = _sunburn_risk(burn_minutes)

            persona_heat_index: int | None = None
            persona_heat_risk = "unavailable"
            if heat_stress_index is not None:
                persona_heat_index = max(
                    0, min(100, int(round(heat_stress_index * heat_sensitivity)))
                )
                persona_heat_risk = _risk_from_index(persona_heat_index)

            persona_prefix = f"sensor.aura_{persona_id}"
            result.extend(
                [
                    {
                        "entity_id": f"{persona_prefix}_sunburn_time_min",
                        "name": f"{persona_name} sunburn time",
                        "value": burn_minutes if burn_minutes is not None else "unavailable",
                        "unit": "min",
                        "source": "persona_profile",
                        "icon": "mdi:white-balance-sunny",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_sunburn_risk",
                        "name": f"{persona_name} sunburn risk",
                        "value": burn_risk,
                        "source": "persona_profile",
                        "icon": "mdi:sun-thermometer-outline",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_heat_stress_index",
                        "name": f"{persona_name} heat stress index",
                        "value": (
                            persona_heat_index
                            if persona_heat_index is not None
                            else "unavailable"
                        ),
                        "unit": "/100",
                        "source": "persona_profile",
                        "icon": "mdi:thermometer-alert",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_heat_stress_risk",
                        "name": f"{persona_name} heat stress risk",
                        "value": persona_heat_risk,
                        "source": "persona_profile",
                        "icon": "mdi:thermometer-alert",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_presence",
                        "name": f"{persona_name} presence",
                        "value": presence,
                        "source": "ha_person"
                        if person_entity_id is not None
                        else "persona_profile",
                        "icon": "mdi:account",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_profile",
                        "name": f"{persona_name} profile",
                        "value": (
                            f"skin_type={skin_type}, spf={spf:g}, shade={shade_factor:g}, "
                            f"uv_sens={uv_sensitivity:g}, heat_sens={heat_sensitivity:g}"
                        ),
                        "source": "persona_profile",
                        "icon": "mdi:account-details-outline",
                        "source_entity": person_entity_id,
                    },
                ]
            )

        return result

    def _build_climate_extra_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        weather_data: dict[str, Any] | None,
        marine_data: dict[str, Any] | None,
        air_data: dict[str, Any] | None,
        personas: Any,
        tracking_entities: Any,
        gdacs_events: list[dict[str, Any]] | None,
        cap_data: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Build extra climate/hazard metrics: UV SED, WBGT, thunder, tides, algae, smoke, CAP, bites."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        weather_hourly = weather_data.get("hourly", {}) if isinstance(weather_data, dict) else {}
        marine_hourly = marine_data.get("hourly", {}) if isinstance(marine_data, dict) else {}
        air_hourly = air_data.get("hourly", {}) if isinstance(air_data, dict) else {}
        weather_daily = weather_data.get("daily", {}) if isinstance(weather_data, dict) else {}

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
            source: str = "internal_model",
            source_entity: str | None = None,
            extras: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            item: dict[str, Any] = {
                "entity_id": entity_id,
                "name": name,
                "value": "unavailable" if value is None else value,
                "source": source,
            }
            if unit is not None:
                item["unit"] = unit
            if icon is not None:
                item["icon"] = icon
            if source_entity is not None:
                item["source_entity"] = source_entity
            if isinstance(extras, dict):
                item.update(extras)
            return item

        uv_now = hourly_float(weather_hourly, "uv_index", weather_idx, 1)
        temperature_now = hourly_float(weather_hourly, "temperature_2m", weather_idx, 1)
        apparent_now = hourly_float(weather_hourly, "apparent_temperature", weather_idx, 1)
        humidity_now = hourly_float(weather_hourly, "relative_humidity_2m", weather_idx, 1)
        cloud_cover_now = hourly_float(weather_hourly, "cloud_cover", weather_idx, 1)
        cape_now = hourly_float(weather_hourly, "cape", weather_idx, 1)
        precip_now = hourly_float(weather_hourly, "precipitation", weather_idx, 1)
        wind_now = hourly_float(weather_hourly, "wind_speed_10m", weather_idx, 1)
        shortwave_now = hourly_float(weather_hourly, "shortwave_radiation", weather_idx, 1)
        weather_code_now = hourly_int(weather_hourly, "weather_code", weather_idx)
        sea_temp_now = hourly_float(marine_hourly, "sea_surface_temperature", marine_idx, 1)
        if sea_temp_now is None:
            sea_temp_now = _optional_float(
                values.get("sensor.beach_water_temperature_official"),
                1,
            )
        wave_height_now = hourly_float(marine_hourly, "wave_height", marine_idx, 2)
        if wave_height_now is None:
            wave_height_now = _optional_float(values.get("sensor.wave_height"), 2)
        aqi_now = hourly_float(air_hourly, "european_aqi", air_idx, 0)
        pm25_now = hourly_float(air_hourly, "pm2_5", air_idx, 1)

        uv_sed_1h: float | None = None
        if uv_now is not None:
            uv_sed_1h = round(max(0.0, uv_now) * 0.9, 2)
        uv_status = "unavailable"
        if uv_now is not None:
            if uv_now >= 11:
                uv_status = "extreme"
            elif uv_now >= 8:
                uv_status = "very_high"
            elif uv_now >= 6:
                uv_status = "high"
            elif uv_now >= 3:
                uv_status = "moderate"
            else:
                uv_status = "low"

        trackers: list[dict[str, Any]] = []
        tracker_ids: set[str] = set()
        tracker_entities_set: set[str] = set()

        def add_tracker(
            *,
            tracker_id: str,
            name: str,
            entity_id: str | None,
            exposure_factor: float,
        ) -> None:
            if not isinstance(entity_id, str) or not entity_id.strip():
                return
            normalized_entity = entity_id.strip()
            if normalized_entity in tracker_entities_set:
                return
            normalized_id = tracker_id.strip().lower()
            if not normalized_id:
                normalized_id = _normalize_tracking_id(name, len(trackers))
            if normalized_id in tracker_ids:
                normalized_id = f"{normalized_id}_{len(trackers) + 1}"
            tracker_entities_set.add(normalized_entity)
            tracker_ids.add(normalized_id)
            trackers.append(
                {
                    "id": normalized_id,
                    "name": name,
                    "entity_id": normalized_entity,
                    "uv_exposure_factor": max(0.0, min(2.5, exposure_factor)),
                }
            )

        if isinstance(personas, list):
            for idx, persona in enumerate(personas):
                if not isinstance(persona, dict):
                    continue
                if persona.get("enabled") is False:
                    continue
                persona_id = _normalize_tracking_id(persona.get("id"), idx)
                persona_name = str(persona.get("name") or persona_id).strip() or persona_id
                tracker_entity_id = persona.get("tracker_entity_id")
                person_entity_id = persona.get("person_entity_id")
                if not isinstance(tracker_entity_id, str) or not tracker_entity_id.strip():
                    tracker_entity_id = (
                        person_entity_id if isinstance(person_entity_id, str) else None
                    )
                add_tracker(
                    tracker_id=persona_id,
                    name=persona_name,
                    entity_id=tracker_entity_id,
                    exposure_factor=_clamp_float(
                        persona.get("uv_exposure_factor", 1.0), 1.0, 0.0, 2.5
                    ),
                )

        if isinstance(tracking_entities, list):
            for idx, tracker in enumerate(tracking_entities):
                if not isinstance(tracker, dict):
                    continue
                add_tracker(
                    tracker_id=_normalize_tracking_id(
                        tracker.get("id", tracker.get("entity_id")),
                        idx,
                    ),
                    name=str(tracker.get("name") or tracker.get("id") or f"tracker_{idx + 1}"),
                    entity_id=tracker.get("entity_id")
                    if isinstance(tracker.get("entity_id"), str)
                    else None,
                    exposure_factor=_clamp_float(
                        tracker.get("uv_exposure_factor", 1.0), 1.0, 0.0, 2.5
                    ),
                )

        local_day = dt_util.now().strftime("%Y-%m-%d")
        if self._uv_sed_day != local_day:
            self._uv_sed_by_tracker = {}
            self._uv_sed_day = local_day
            self._uv_sed_last_update = None

        now_utc = datetime.now(tz=UTC)
        delta_hours = 0.0
        if self._uv_sed_last_update is not None:
            delta_hours = max(
                0.0,
                min(
                    1.5,
                    (now_utc - self._uv_sed_last_update).total_seconds() / 3600.0,
                ),
            )
        self._uv_sed_last_update = now_utc

        def outdoor_weight(state_value: str) -> float:
            value = state_value.strip().lower()
            if value in {"", "unknown", "unavailable", "none"}:
                return 0.0
            if value == "home":
                return 0.0
            if value in {"not_home", "away"}:
                return 0.6
            if any(
                token in value
                for token in (
                    "walking",
                    "on_foot",
                    "walk",
                    "foot",
                    "beach",
                    "outdoor",
                    "park",
                    "running",
                    "cycling",
                    "sport",
                    "пеш",
                    "пляж",
                    "улиц",
                    "прогул",
                )
            ):
                return 1.0
            return 0.5

        tracker_metrics: list[dict[str, Any]] = []
        sed_total_today = 0.0
        for tracker in trackers:
            tracker_id = str(tracker.get("id") or "").strip()
            if not tracker_id:
                continue
            entity_id = str(tracker.get("entity_id") or "").strip()
            if not entity_id:
                continue
            tracker_name = str(tracker.get("name") or tracker_id).strip() or tracker_id
            exposure_factor = _clamp_float(
                tracker.get("uv_exposure_factor", 1.0), 1.0, 0.0, 2.5
            )

            state = self.hass.states.get(entity_id)
            state_value = str(state.state or "unknown") if state is not None else "unavailable"
            exposure_state = "indoors"
            weight = outdoor_weight(state_value)
            if state_value in {"unavailable", "unknown"}:
                exposure_state = "unknown"
            elif weight >= 0.9:
                exposure_state = "outdoor"
            elif weight > 0.0:
                exposure_state = "mixed"

            previous_sed = _safe_float(self._uv_sed_by_tracker.get(tracker_id, 0.0), 0.0)
            if uv_sed_1h is not None and delta_hours > 0:
                increment = uv_sed_1h * delta_hours * weight * exposure_factor
                previous_sed += increment
            current_sed = round(max(0.0, min(40.0, previous_sed)), 2)
            self._uv_sed_by_tracker[tracker_id] = current_sed
            sed_total_today += current_sed

            tracker_prefix = f"sensor.aura_tracker_{tracker_id}"
            tracker_metrics.extend(
                [
                    metric(
                        f"{tracker_prefix}_uv_sed_today",
                        f"{tracker_name} UV SED today",
                        current_sed,
                        unit="SED",
                        icon="mdi:white-balance-sunny",
                        source="ha_tracking",
                        source_entity=entity_id,
                        extras={"state": state_value},
                    ),
                    metric(
                        f"{tracker_prefix}_uv_exposure_state",
                        f"{tracker_name} UV exposure state",
                        exposure_state,
                        icon="mdi:walk",
                        source="ha_tracking",
                        source_entity=entity_id,
                    ),
                ]
            )

        sed_total_value: float | None = None
        if trackers:
            sed_total_value = round(sed_total_today, 2)

        wbgt_c: float | None = None
        dehydration_index: int | None = None
        dehydration_risk = "unavailable"
        if temperature_now is not None and humidity_now is not None:
            vapor_hpa = (humidity_now / 100.0) * 6.105 * math.exp(
                (17.27 * temperature_now) / (237.7 + temperature_now)
            )
            wbgt = 0.567 * temperature_now + 0.393 * vapor_hpa + 3.94
            if shortwave_now is not None:
                wbgt += min(4.5, max(0.0, shortwave_now - 180.0) / 140.0)
            if wind_now is not None:
                wbgt -= min(2.5, max(0.0, wind_now) / 20.0)
            wbgt_c = round(wbgt, 1)

            score = max(0.0, (wbgt_c - 20.0) * 4.6)
            if uv_now is not None:
                score += max(0.0, uv_now - 3.0) * 4.2
            if wind_now is not None:
                score += max(0.0, wind_now - 15.0) * 0.7
            if apparent_now is not None:
                score += max(0.0, apparent_now - 30.0) * 1.8
            dehydration_index = max(0, min(100, int(round(score))))
            dehydration_risk = _risk_from_index(dehydration_index)

        def thunder_index_for_offset(offset: int) -> int | None:
            idx = weather_idx + offset
            cape_v = hourly_float(weather_hourly, "cape", idx, 0)
            precip_v = hourly_float(weather_hourly, "precipitation", idx, 1)
            cloud_v = hourly_float(weather_hourly, "cloud_cover", idx, 1)
            humidity_v = hourly_float(weather_hourly, "relative_humidity_2m", idx, 1)
            code_v = hourly_int(weather_hourly, "weather_code", idx)
            if (
                cape_v is None
                and precip_v is None
                and cloud_v is None
                and humidity_v is None
                and code_v is None
            ):
                return None

            score = 0.0
            if code_v in {95, 96, 99}:
                score += 72.0
            elif code_v in {80, 81, 82}:
                score += 14.0

            if cape_v is not None:
                if cape_v >= 2500:
                    score += 35.0
                elif cape_v >= 1500:
                    score += 25.0
                elif cape_v >= 800:
                    score += 16.0
                elif cape_v >= 300:
                    score += 8.0

            if precip_v is not None:
                if precip_v >= 2.0:
                    score += 12.0
                elif precip_v >= 0.5:
                    score += 6.0

            if cloud_v is not None and cloud_v >= 70:
                score += 6.0
            if humidity_v is not None and humidity_v >= 75:
                score += 6.0
            return max(0, min(100, int(round(score))))

        thunder_now = thunder_index_for_offset(0)
        thunder_next = [
            value
            for value in (
                thunder_index_for_offset(1),
                thunder_index_for_offset(2),
                thunder_index_for_offset(3),
            )
            if value is not None
        ]
        thunder_future_max = max(thunder_next) if thunder_next else None
        thunder_index = thunder_now
        if thunder_index is None:
            thunder_index = thunder_future_max
        elif thunder_future_max is not None:
            thunder_index = max(thunder_index, thunder_future_max)
        thunder_risk = _risk_from_index(thunder_index) if thunder_index is not None else "unavailable"
        thunder_nowcast = "unavailable"
        if thunder_now is not None and thunder_future_max is not None:
            if thunder_future_max >= thunder_now + 12:
                thunder_nowcast = "rising"
            elif thunder_now >= thunder_future_max + 12:
                thunder_nowcast = "decreasing"
            elif thunder_future_max >= 65 or thunder_now >= 65:
                thunder_nowcast = "high"
            else:
                thunder_nowcast = "stable_low"
        elif thunder_index is not None:
            thunder_nowcast = "high" if thunder_index >= 65 else "stable_low"

        tide_level = hourly_float(marine_hourly, "sea_level_height_msl", marine_idx, 3)
        tide_plus_3h = hourly_float(marine_hourly, "sea_level_height_msl", marine_idx + 3, 3)
        tide_trend = "unavailable"
        if tide_level is not None and tide_plus_3h is not None:
            delta = tide_plus_3h - tide_level
            if delta > 0.03:
                tide_trend = "rising"
            elif delta < -0.03:
                tide_trend = "falling"
            else:
                tide_trend = "stable"

        tide_values: list[float] = []
        series = marine_hourly.get("sea_level_height_msl")
        if isinstance(series, list):
            for val in series[marine_idx : marine_idx + 24]:
                parsed = _optional_float(val)
                if parsed is not None:
                    tide_values.append(parsed)
        tide_range_24h = (
            round(max(tide_values) - min(tide_values), 3)
            if len(tide_values) >= 2
            else None
        )

        ocean_current_speed = hourly_float(
            marine_hourly, "ocean_current_velocity", marine_idx, 2
        )
        ocean_current_direction = hourly_float(
            marine_hourly, "ocean_current_direction", marine_idx, 1
        )
        current_index: int | None = None
        current_risk = "unavailable"
        if ocean_current_speed is not None:
            score = 0.0
            if ocean_current_speed >= 4.0:
                score += 82
            elif ocean_current_speed >= 3.0:
                score += 62
            elif ocean_current_speed >= 2.0:
                score += 42
            elif ocean_current_speed >= 1.2:
                score += 24
            elif ocean_current_speed >= 0.6:
                score += 12
            if wave_height_now is not None:
                if wave_height_now >= 2.0:
                    score += 18
                elif wave_height_now >= 1.2:
                    score += 10
            current_index = max(0, min(100, int(round(score))))
            current_risk = _risk_from_index(current_index)

        water_quality = str(values.get("sensor.beach_water_quality_official") or "").strip().lower()
        algae_index: int | None = None
        algae_risk = "unavailable"
        algae_signal = "insufficient_data"
        if sea_temp_now is not None and wave_height_now is not None:
            score = max(0.0, (sea_temp_now - 18.0) * 7.0)
            if wave_height_now < 0.6:
                score += 24
            elif wave_height_now < 1.0:
                score += 14
            if shortwave_now is not None:
                score += min(20.0, max(0.0, shortwave_now - 300.0) / 18.0)
            if any(token in water_quality for token in ("bad", "poor", "mala", "deficient")):
                score += 26
            elif any(token in water_quality for token in ("regular", "fair", "acceptable")):
                score += 12
            elif any(token in water_quality for token in ("excellent", "good", "buena", "bona")):
                score -= 6
            algae_index = max(0, min(100, int(round(score))))
            algae_risk = _risk_from_index(algae_index)
            algae_signal = (
                f"sea={sea_temp_now}C,wave={wave_height_now}m,quality={water_quality or 'unknown'}"
            )

        wildfire_distance = _optional_float(values.get("sensor.wildfire_nearest_distance_km"), 1)
        wildfire_alert = str(values.get("sensor.wildfire_max_alert_level") or "").strip().lower()
        smoke_index: int | None = None
        smoke_risk = "unavailable"
        smoke_signal = "insufficient_data"
        if wildfire_distance is not None or aqi_now is not None or pm25_now is not None:
            score = 0.0
            if wildfire_distance is not None:
                if wildfire_distance <= 100:
                    score += 55
                elif wildfire_distance <= 300:
                    score += 40
                elif wildfire_distance <= 700:
                    score += 24
                elif wildfire_distance <= 1500:
                    score += 12
            if wildfire_alert == "red":
                score += 24
            elif wildfire_alert == "orange":
                score += 15
            elif wildfire_alert in {"yellow", "green"}:
                score += 7
            if aqi_now is not None:
                score += max(0.0, aqi_now - 40.0) * 0.6
            if pm25_now is not None:
                score += max(0.0, pm25_now - 15.0) * 1.2
            if wind_now is not None:
                if wind_now > 30:
                    score -= 10
                elif 8 <= wind_now <= 22:
                    score += 4
            smoke_index = max(0, min(100, int(round(score))))
            smoke_risk = _risk_from_index(smoke_index)
            smoke_signal = (
                f"dist={wildfire_distance if wildfire_distance is not None else 'na'}km,"
                f"alert={wildfire_alert or 'na'},aqi={aqi_now if aqi_now is not None else 'na'}"
            )

        cap_index = _optional_int(cap_data.get("index")) if isinstance(cap_data, dict) else None
        cap_active = _optional_int(cap_data.get("active_count")) if isinstance(cap_data, dict) else None
        cap_highest = (
            str(cap_data.get("highest_severity") or "unknown")
            if isinstance(cap_data, dict)
            else "unavailable"
        )
        cap_event = (
            str(cap_data.get("top_event") or "unknown")
            if isinstance(cap_data, dict)
            else "unavailable"
        )
        cap_area = (
            str(cap_data.get("top_area") or "unknown")
            if isinstance(cap_data, dict)
            else "unavailable"
        )
        cap_expires = (
            str(cap_data.get("top_expires") or "unknown")
            if isinstance(cap_data, dict)
            else "unavailable"
        )
        cap_link = cap_data.get("top_link") if isinstance(cap_data, dict) else None
        cap_risk = _risk_from_index(cap_index) if cap_index is not None else "unavailable"
        cap_source = "meteoalarm_atom_spain" if isinstance(cap_data, dict) else "unavailable"

        mosquito_index = _optional_int(values.get("sensor.tiger_mosquito_index"))
        if mosquito_index is None:
            mosquito_index = _optional_int(values.get("sensor.mosquito_index"))
        tick_index = _optional_int(values.get("sensor.tick_index"))
        bite_index: int | None = None
        bite_risk = "unavailable"
        if mosquito_index is not None or tick_index is not None:
            score = 0.0
            if mosquito_index is not None:
                score += mosquito_index * 0.6
            if tick_index is not None:
                score += tick_index * 0.35
            if humidity_now is not None and humidity_now > 65:
                score += min(10.0, (humidity_now - 65) * 0.4)
            if temperature_now is not None and 18 <= temperature_now <= 32:
                score += 8.0
            bite_index = max(0, min(100, int(round(score))))
            bite_risk = _risk_from_index(bite_index)

        bite_outlook = "unavailable"
        daily_time = weather_daily.get("time") if isinstance(weather_daily, dict) else None
        if (
            isinstance(daily_time, list)
            and daily_time
            and mosquito_index is not None
            and tick_index is not None
        ):
            risk_rank = {"very_low": 1, "low": 2, "moderate": 3, "high": 4, "very_high": 5}
            day_scores: list[int] = []
            for idx, _day in enumerate(daily_time[:3]):
                temp_max = _safe_float(
                    _hourly_value(weather_daily, "temperature_2m_max", idx, 0.0), 0.0
                )
                temp_min = _safe_float(
                    _hourly_value(weather_daily, "temperature_2m_min", idx, 0.0), 0.0
                )
                rain_prob_max = _safe_int(
                    _hourly_value(weather_daily, "precipitation_probability_max", idx, 0), 0
                )
                wind_max = _safe_float(
                    _hourly_value(weather_daily, "wind_speed_10m_max", idx, 0.0), 0.0
                )
                mos_risk = _forecast_mosquito_risk(
                    baseline_index=mosquito_index,
                    temp_min=temp_min,
                    temp_max=temp_max,
                    rain_probability_max=rain_prob_max,
                    wind_max_kmh=wind_max,
                )
                tick_risk_est = _forecast_tick_risk(
                    baseline_index=tick_index,
                    temp_min=temp_min,
                    temp_max=temp_max,
                    rain_probability_max=rain_prob_max,
                    wind_max_kmh=wind_max,
                )
                day_score = max(risk_rank.get(mos_risk, 1), risk_rank.get(tick_risk_est, 1))
                day_scores.append(day_score)
            if day_scores:
                avg = sum(day_scores) / len(day_scores)
                if avg >= 4.5:
                    bite_outlook = "very_high"
                elif avg >= 3.5:
                    bite_outlook = "high"
                elif avg >= 2.5:
                    bite_outlook = "moderate"
                elif avg >= 1.5:
                    bite_outlook = "low"
                else:
                    bite_outlook = "very_low"

        result: list[dict[str, Any]] = [
            metric("sensor.uv_dose_sed_1h", "UV dose (1h full exposure)", uv_sed_1h, "SED"),
            metric(
                "sensor.uv_dose_sed_today_est",
                "UV dose today (tracked)",
                sed_total_value,
                "SED",
            ),
            metric("sensor.uv_dose_status", "UV dose status", uv_status),
            metric("sensor.wbgt_c", "WBGT", wbgt_c, "degC"),
            metric(
                "sensor.dehydration_index",
                "Dehydration index",
                dehydration_index,
                "/100",
            ),
            metric("sensor.dehydration_risk", "Dehydration risk", dehydration_risk),
            metric("sensor.thunderstorm_risk", "Thunderstorm risk", thunder_risk),
            metric("sensor.thunderstorm_index", "Thunderstorm index", thunder_index, "/100"),
            metric("sensor.thunderstorm_cape", "CAPE", cape_now, "J/kg"),
            metric(
                "sensor.thunderstorm_nowcast_3h",
                "Thunderstorm nowcast +3h",
                thunder_nowcast,
            ),
            metric("sensor.tide_level_m", "Tide level (MSL)", tide_level, "m"),
            metric("sensor.tide_trend_3h", "Tide trend +3h", tide_trend),
            metric("sensor.tide_range_24h_m", "Tide range 24h", tide_range_24h, "m"),
            metric(
                "sensor.ocean_current_speed",
                "Ocean current speed",
                ocean_current_speed,
                "km/h",
            ),
            metric(
                "sensor.ocean_current_direction",
                "Ocean current direction",
                ocean_current_direction,
                "deg",
            ),
            metric("sensor.current_risk", "Current risk", current_risk),
            metric("sensor.algae_bloom_risk", "Algae bloom risk", algae_risk),
            metric("sensor.algae_bloom_index", "Algae bloom index", algae_index, "/100"),
            metric("sensor.algae_bloom_signal", "Algae bloom signal", algae_signal),
            metric("sensor.algae_source", "Algae source", "internal_model+beach_quality"),
            metric("sensor.smoke_transport_risk", "Smoke transport risk", smoke_risk),
            metric("sensor.smoke_transport_index", "Smoke transport index", smoke_index, "/100"),
            metric("sensor.smoke_transport_signal", "Smoke transport signal", smoke_signal),
            metric("sensor.smoke_source", "Smoke source", "gdacs+air_quality_model"),
            metric("sensor.cap_alert_risk", "CAP alert risk", cap_risk, source=cap_source),
            metric(
                "sensor.cap_alert_index",
                "CAP alert index",
                cap_index,
                "/100",
                source=cap_source,
            ),
            metric(
                "sensor.cap_alerts_active",
                "CAP alerts active",
                cap_active,
                source=cap_source,
            ),
            metric(
                "sensor.cap_highest_severity",
                "CAP highest severity",
                cap_highest,
                source=cap_source,
            ),
            metric("sensor.cap_top_event", "CAP top event", cap_event, source=cap_source),
            metric("sensor.cap_top_area", "CAP top area", cap_area, source=cap_source),
            metric("sensor.cap_top_expires", "CAP top expires", cap_expires, source=cap_source),
            metric(
                "sensor.cap_source",
                "CAP source",
                cap_source,
                source=cap_source,
                extras={"cap_link": cap_link},
            ),
            metric("sensor.bite_index", "Bite index", bite_index, "/100"),
            metric("sensor.bite_risk", "Bite risk", bite_risk),
            metric("sensor.bite_outlook_3d", "Bite outlook 3d", bite_outlook),
        ]
        result.extend(tracker_metrics)
        return result

    def _build_daily_planner_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        weather_data: dict[str, Any] | None,
        marine_data: dict[str, Any] | None,
        air_data: dict[str, Any] | None,
        personas: Any,
        daily_plan_enabled: bool,
        default_planner_mode: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Build daily planner + smart notification hints."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        planner_mode_default = _normalize_planner_mode(default_planner_mode)

        mode_profiles: dict[str, dict[str, float]] = {
            "normal": {
                "uv_limit": 6.0,
                "heat_limit": 31.0,
                "outdoor_threshold": 65.0,
                "beach_threshold": 68.0,
            },
            "child": {
                "uv_limit": 3.5,
                "heat_limit": 28.5,
                "outdoor_threshold": 72.0,
                "beach_threshold": 74.0,
            },
            "elderly": {
                "uv_limit": 5.0,
                "heat_limit": 28.0,
                "outdoor_threshold": 70.0,
                "beach_threshold": 72.0,
            },
            "sport": {
                "uv_limit": 7.0,
                "heat_limit": 33.0,
                "outdoor_threshold": 62.0,
                "beach_threshold": 66.0,
            },
            "beach_day": {
                "uv_limit": 6.5,
                "heat_limit": 32.0,
                "outdoor_threshold": 60.0,
                "beach_threshold": 64.0,
            },
        }
        comparison_hours = 3
        jellyfish_baseline = str(values.get("sensor.jellyfish_risk") or "").strip().lower()
        rip_index = _optional_int(values.get("sensor.rip_current_index"))
        base_jellyfish_penalty = {
            "very_high": 18.0,
            "high": 12.0,
            "moderate": 6.0,
            "low": 2.0,
            "very_low": 1.0,
            "off_season": 0.0,
        }.get(jellyfish_baseline, 3.0)

        weather_hourly = weather_data.get("hourly", {}) if isinstance(weather_data, dict) else {}
        marine_hourly = marine_data.get("hourly", {}) if isinstance(marine_data, dict) else {}
        air_hourly = air_data.get("hourly", {}) if isinstance(air_data, dict) else {}

        weather_times = weather_hourly.get("time")
        hourly_rows: list[dict[str, Any]] = []
        if isinstance(weather_times, list) and weather_times:
            tz = dt_util.get_time_zone(self.hass.config.time_zone) or UTC
            start_idx = self._select_hour_index(weather_hourly)
            end_idx = min(len(weather_times), start_idx + 24)
            for idx in range(start_idx, end_idx):
                raw_time = weather_times[idx]
                if not isinstance(raw_time, str):
                    continue
                parsed = dt_util.parse_datetime(raw_time)
                if parsed is None:
                    continue
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=tz)
                local_dt = parsed.astimezone(tz)
                hourly_rows.append(
                    {
                        "label": local_dt.strftime("%m-%d %H:00"),
                        "uv": _optional_float(_hourly_value(weather_hourly, "uv_index", idx, None)),
                        "apparent_temp": _optional_float(
                            _hourly_value(weather_hourly, "apparent_temperature", idx, None)
                        ),
                        "rain_prob": _optional_float(
                            _hourly_value(weather_hourly, "precipitation_probability", idx, None)
                        ),
                        "wind": _optional_float(
                            _hourly_value(weather_hourly, "wind_speed_10m", idx, None)
                        ),
                        "aqi": _optional_float(
                            _hourly_value(air_hourly, "european_aqi", idx, None)
                        ),
                        "sea_temp": _optional_float(
                            _hourly_value(marine_hourly, "sea_surface_temperature", idx, None)
                        ),
                        "wave_height": _optional_float(
                            _hourly_value(marine_hourly, "wave_height", idx, None)
                        ),
                    }
                )

        personas_rows: list[dict[str, Any]] = []
        if isinstance(personas, list):
            personas_rows = [
                row
                for row in personas
                if isinstance(row, dict)
                and row.get("enabled") is not False
                and str(row.get("id") or "").strip()
            ]

        def planner_metric(
            entity_id: str,
            name: str,
            value: Any,
            *,
            icon: str | None = None,
            source_entity: str | None = None,
            extras: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            item: dict[str, Any] = {
                "entity_id": entity_id,
                "name": name,
                "value": "unavailable" if value is None else value,
                "source": "internal_planner",
            }
            if icon is not None:
                item["icon"] = icon
            if source_entity:
                item["source_entity"] = source_entity
            if isinstance(extras, dict):
                item.update(extras)
            return item

        def score_outdoor(
            row: dict[str, Any],
            *,
            mode: str,
            skin_type: int,
            uv_sensitivity: float,
            heat_sensitivity: float,
        ) -> int:
            profile = mode_profiles.get(mode, mode_profiles["normal"])
            score = 100.0

            uv = _optional_float(row.get("uv"))
            if uv is None:
                score -= 8.0
            else:
                uv_limit = profile["uv_limit"] + (skin_type - 3) * 0.35
                score -= max(0.0, uv - uv_limit) * 14.0 * uv_sensitivity

            apparent_temp = _optional_float(row.get("apparent_temp"))
            if apparent_temp is None:
                score -= 5.0
            else:
                score -= max(0.0, apparent_temp - profile["heat_limit"]) * 4.2 * heat_sensitivity

            rain_prob = _optional_float(row.get("rain_prob"))
            if rain_prob is not None:
                score -= max(0.0, rain_prob - 10.0) * 0.55

            wind = _optional_float(row.get("wind"))
            if wind is not None and wind > 15.0:
                score -= (wind - 15.0) * 1.1

            aqi = _optional_float(row.get("aqi"))
            if aqi is not None and aqi > 35.0:
                score -= (aqi - 35.0) * 0.45

            return max(0, min(100, int(round(score))))

        def score_beach(
            row: dict[str, Any],
            *,
            mode: str,
            skin_type: int,
            uv_sensitivity: float,
            heat_sensitivity: float,
        ) -> int:
            score = float(
                score_outdoor(
                    row,
                    mode=mode,
                    skin_type=skin_type,
                    uv_sensitivity=uv_sensitivity,
                    heat_sensitivity=heat_sensitivity,
                )
            )

            sea_temp = _optional_float(row.get("sea_temp"))
            if sea_temp is None:
                score -= 12.0
            elif sea_temp < 19.0:
                score -= 35.0
            elif sea_temp < 21.0:
                score -= 16.0
            elif sea_temp >= 24.0:
                score += 5.0

            wave_height = _optional_float(row.get("wave_height"))
            if wave_height is None:
                score -= 8.0
            elif wave_height > 2.2:
                score -= 36.0
            elif wave_height > 1.5:
                score -= 22.0
            elif wave_height > 1.1:
                score -= 12.0

            if rip_index is not None:
                score -= rip_index * 0.12
            score -= base_jellyfish_penalty

            return max(0, min(100, int(round(score))))

        def trend_label(now_score: int | None, future_score: int | None) -> str:
            if now_score is None or future_score is None:
                return "unavailable"
            delta = future_score - now_score
            if delta >= 8:
                return "better_in_3h"
            if delta <= -8:
                return "better_now"
            return "stable"

        def best_hours(
            rows: list[dict[str, Any]],
            scores: list[int],
            threshold: float,
        ) -> str:
            accepted = [
                rows[idx]["label"]
                for idx, score in enumerate(scores)
                if idx < len(rows) and score >= threshold
            ]
            if not accepted:
                return "none"
            if len(accepted) > 8:
                return ", ".join(accepted[:8]) + ", ..."
            return ", ".join(accepted)

        def pack_list_for_mode(
            *,
            mode: str,
            sea_temp_now: float | None,
            rain_now: float | None,
            uv_now: float | None,
            trend_outdoor: str,
        ) -> str:
            items = [
                "water",
                "towel",
                "sunscreen SPF50+",
                "hat",
                "sunglasses",
            ]
            if mode == "child":
                items.extend(["UV shirt", "spare clothes", "kids snack"])
            elif mode == "elderly":
                items.extend(["electrolytes", "light chair", "medication kit"])
            elif mode == "sport":
                items.extend(["electrolytes", "sports bottle", "energy snack"])
            elif mode == "beach_day":
                items.extend(["umbrella", "beach mat", "snorkel mask"])

            if sea_temp_now is not None and sea_temp_now < 21.0:
                items.append("light hoodie")
            if rain_now is not None and rain_now >= 35.0:
                items.append("light rain jacket")
            if uv_now is not None and uv_now >= 6.0:
                items.append("after-sun gel")
            if jellyfish_baseline in {"high", "very_high"}:
                items.append("anti-sting kit")
            if trend_outdoor == "better_in_3h":
                items.append("option to start 2-3h later")

            unique_items: list[str] = []
            seen: set[str] = set()
            for item in items:
                key = item.lower().strip()
                if key in seen:
                    continue
                seen.add(key)
                unique_items.append(item)
            return ", ".join(unique_items)

        sea_temp_official = _optional_float(values.get("sensor.beach_water_temperature_official"))
        sea_temp_model = _optional_float(values.get("sensor.sea_temperature_openmeteo"))
        sea_temp_now = sea_temp_official if sea_temp_official is not None else sea_temp_model
        rain_now = _optional_float(hourly_rows[0].get("rain_prob")) if hourly_rows else None
        uv_now = _optional_float(hourly_rows[0].get("uv")) if hourly_rows else None

        default_outdoor_scores: list[int] = []
        default_beach_scores: list[int] = []
        for row in hourly_rows:
            default_outdoor_scores.append(
                score_outdoor(
                    row,
                    mode=planner_mode_default,
                    skin_type=3,
                    uv_sensitivity=1.0,
                    heat_sensitivity=1.0,
                )
            )
            default_beach_scores.append(
                score_beach(
                    row,
                    mode=planner_mode_default,
                    skin_type=3,
                    uv_sensitivity=1.0,
                    heat_sensitivity=1.0,
                )
            )

        comparison_index: int | None = None
        if len(hourly_rows) > 3:
            comparison_index = 3
        elif len(hourly_rows) > 2:
            comparison_index = 2

        outdoor_now = default_outdoor_scores[0] if default_outdoor_scores else None
        outdoor_future = (
            default_outdoor_scores[comparison_index]
            if comparison_index is not None and comparison_index < len(default_outdoor_scores)
            else None
        )
        beach_now = default_beach_scores[0] if default_beach_scores else None
        beach_future = (
            default_beach_scores[comparison_index]
            if comparison_index is not None and comparison_index < len(default_beach_scores)
            else None
        )
        outdoor_trend = trend_label(outdoor_now, outdoor_future)
        beach_trend = trend_label(beach_now, beach_future)
        outdoor_summary = (
            f"{outdoor_now}->{outdoor_future}"
            if outdoor_now is not None and outdoor_future is not None
            else "unavailable"
        )
        beach_summary = (
            f"{beach_now}->{beach_future}"
            if beach_now is not None and beach_future is not None
            else "unavailable"
        )
        now_vs_summary = f"outdoor:{outdoor_summary}, beach:{beach_summary}"

        beach_recommendation = str(values.get("sensor.beach_recommendation") or "").strip().lower()
        beach_flag = str(values.get("sensor.beach_flag_calculated") or "").strip().lower()
        has_beach_premise = (
            sea_temp_now is not None
            and sea_temp_now >= 19.0
            and beach_flag != "red"
            and (
                beach_recommendation == "recommended"
                or (beach_now is not None and beach_now >= 68)
            )
        )

        walking_tokens = ("walking", "on_foot", "walk", "foot", "пеш", "топ")
        is_walking = False
        for persona in personas_rows:
            person_entity_id = persona.get("person_entity_id")
            if not isinstance(person_entity_id, str) or not person_entity_id.strip():
                continue
            state = self.hass.states.get(person_entity_id.strip())
            if state is None:
                continue
            value = str(state.state or "").strip().lower()
            if not value:
                continue
            if any(token in value for token in walking_tokens):
                is_walking = True
                break
            if value not in {"home", "unknown", "unavailable", "none"}:
                is_walking = True

        beach_pack_trigger = "not_ready"
        if not daily_plan_enabled:
            beach_pack_trigger = "disabled"
        elif is_walking and has_beach_premise:
            beach_pack_trigger = "ready"
        global_pack_list = pack_list_for_mode(
            mode=planner_mode_default,
            sea_temp_now=sea_temp_now,
            rain_now=rain_now,
            uv_now=uv_now,
            trend_outdoor=outdoor_trend,
        )
        global_notification_state = "notify" if beach_pack_trigger == "ready" else "idle"
        global_notification_key = "aura_beach_pack_plan"

        result: list[dict[str, Any]] = [
            planner_metric(
                "sensor.aura_daily_plan_status",
                "AURA daily plan status",
                "enabled" if daily_plan_enabled else "disabled",
                icon="mdi:calendar-check",
            ),
            planner_metric(
                "sensor.aura_planner_mode_default",
                "AURA planner mode (default)",
                planner_mode_default,
                icon="mdi:calendar-clock",
            ),
            planner_metric(
                "sensor.aura_now_vs_3h_outdoor",
                "AURA outdoor now vs +2..3h",
                outdoor_trend if daily_plan_enabled else "disabled",
                icon="mdi:walk",
            ),
            planner_metric(
                "sensor.aura_now_vs_3h_beach",
                "AURA beach now vs +2..3h",
                beach_trend if daily_plan_enabled else "disabled",
                icon="mdi:beach",
            ),
            planner_metric(
                "sensor.aura_now_vs_3h_summary",
                "AURA now vs +2..3h summary",
                now_vs_summary if daily_plan_enabled else "daily_plan_disabled",
                icon="mdi:timeline-clock-outline",
            ),
            planner_metric(
                "sensor.aura_beach_pack_trigger",
                "AURA beach pack trigger",
                beach_pack_trigger,
                icon="mdi:bag-suitcase-outline",
            ),
            planner_metric(
                "sensor.aura_beach_pack_list",
                "AURA beach pack list",
                global_pack_list if daily_plan_enabled else "daily_plan_disabled",
                icon="mdi:bag-personal",
            ),
            planner_metric(
                "sensor.aura_beach_notification_key",
                "AURA beach notification key",
                global_notification_key,
                icon="mdi:key-outline",
            ),
            planner_metric(
                "sensor.aura_beach_notification_state",
                "AURA beach notification state",
                global_notification_state,
                icon="mdi:bell-ring-outline",
                extras={
                    "notification_key": global_notification_key,
                    "notification_family": "ai_foundation",
                    "notification_scope": "outdoor",
                    "notification_message_ru": (
                        "Пляжный сбор активирован: условия подходят."
                        if global_notification_state == "notify"
                        else "Пляжный сбор не требуется."
                    ),
                    "notification_message_en": (
                        "Beach pack plan is active: conditions look good."
                        if global_notification_state == "notify"
                        else "Beach pack plan is idle."
                    ),
                },
            ),
        ]

        planner_payload: dict[str, Any] = {
            "enabled": daily_plan_enabled,
            "default_mode": planner_mode_default,
            "comparison_hours": comparison_hours,
            "now_vs_3h": {
                "outdoor": outdoor_trend if daily_plan_enabled else "disabled",
                "beach": beach_trend if daily_plan_enabled else "disabled",
                "outdoor_scores": {
                    "now": outdoor_now,
                    "future": outdoor_future,
                },
                "beach_scores": {
                    "now": beach_now,
                    "future": beach_future,
                },
                "summary": now_vs_summary,
            },
            "beach_pack": {
                "trigger": beach_pack_trigger,
                "is_walking": is_walking,
                "sea_temp_now": sea_temp_now,
                "list": global_pack_list,
                "notification_key": global_notification_key,
                "notification_state": global_notification_state,
            },
            "personas": [],
        }

        for persona in personas_rows:
            persona_id = str(persona.get("id") or "").strip()
            if not persona_id:
                continue
            persona_name = str(persona.get("name") or persona_id).strip() or persona_id
            person_entity_id = persona.get("person_entity_id")
            if not isinstance(person_entity_id, str) or not person_entity_id.strip():
                person_entity_id = None
            else:
                person_entity_id = person_entity_id.strip()
            mode = _normalize_planner_mode(persona.get("planner_mode", planner_mode_default))
            skin_type = _safe_int(persona.get("skin_type"), 3)
            if skin_type < 1:
                skin_type = 1
            if skin_type > 6:
                skin_type = 6
            uv_sensitivity = _clamp_float(persona.get("uv_sensitivity", 1.0), 1.0, 0.5, 2.5)
            heat_sensitivity = _clamp_float(
                persona.get("heat_sensitivity", 1.0), 1.0, 0.6, 1.8
            )

            outdoor_scores: list[int] = []
            beach_scores: list[int] = []
            for row in hourly_rows:
                outdoor_scores.append(
                    score_outdoor(
                        row,
                        mode=mode,
                        skin_type=skin_type,
                        uv_sensitivity=uv_sensitivity,
                        heat_sensitivity=heat_sensitivity,
                    )
                )
                beach_scores.append(
                    score_beach(
                        row,
                        mode=mode,
                        skin_type=skin_type,
                        uv_sensitivity=uv_sensitivity,
                        heat_sensitivity=heat_sensitivity,
                    )
                )

            profile = mode_profiles.get(mode, mode_profiles["normal"])
            best_outdoor = (
                best_hours(hourly_rows, outdoor_scores, profile["outdoor_threshold"])
                if daily_plan_enabled and outdoor_scores
                else "unavailable"
            )
            best_beach = (
                best_hours(hourly_rows, beach_scores, profile["beach_threshold"])
                if daily_plan_enabled and beach_scores
                else "unavailable"
            )

            persona_outdoor_now = outdoor_scores[0] if outdoor_scores else None
            persona_outdoor_future = (
                outdoor_scores[comparison_index]
                if comparison_index is not None and comparison_index < len(outdoor_scores)
                else None
            )
            persona_beach_now = beach_scores[0] if beach_scores else None
            persona_beach_future = (
                beach_scores[comparison_index]
                if comparison_index is not None and comparison_index < len(beach_scores)
                else None
            )
            persona_now_vs = trend_label(persona_outdoor_now, persona_outdoor_future)
            persona_pack_ready = (
                daily_plan_enabled
                and beach_pack_trigger == "ready"
                and best_beach not in {"none", "unavailable"}
            )
            persona_pack_list = pack_list_for_mode(
                mode=mode,
                sea_temp_now=sea_temp_now,
                rain_now=rain_now,
                uv_now=uv_now,
                trend_outdoor=persona_now_vs,
            )
            persona_notification_state = "notify" if persona_pack_ready else "idle"
            persona_notification_key = f"aura_{persona_id}_beach_pack_plan"
            persona_daily_plan = (
                f"mode={mode}; outdoor={best_outdoor}; beach={best_beach}; now_vs_3h={persona_now_vs}"
                if daily_plan_enabled
                else "daily_plan_disabled"
            )

            persona_prefix = f"sensor.aura_{persona_id}"
            result.extend(
                [
                    planner_metric(
                        f"{persona_prefix}_planner_mode",
                        f"{persona_name} planner mode",
                        mode,
                        icon="mdi:calendar-clock",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_best_hours_outdoor",
                        f"{persona_name} best outdoor hours",
                        best_outdoor,
                        icon="mdi:walk",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_best_hours_beach",
                        f"{persona_name} best beach hours",
                        best_beach,
                        icon="mdi:beach",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_now_vs_3h",
                        f"{persona_name} now vs +2..3h",
                        persona_now_vs if daily_plan_enabled else "disabled",
                        icon="mdi:timeline-clock-outline",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_daily_plan",
                        f"{persona_name} daily plan",
                        persona_daily_plan,
                        icon="mdi:calendar-text",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_pack_list",
                        f"{persona_name} beach pack list",
                        persona_pack_list if daily_plan_enabled else "daily_plan_disabled",
                        icon="mdi:bag-personal",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_smart_notification",
                        f"{persona_name} smart notification",
                        persona_notification_state,
                        icon="mdi:bell-ring-outline",
                        source_entity=person_entity_id,
                        extras={
                            "notification_key": persona_notification_key,
                            "notification_family": "ai_foundation",
                            "notification_scope": "outdoor",
                            "notification_message_ru": (
                                f"{persona_name}: собраться на пляж, окно {best_beach}."
                                if persona_notification_state == "notify"
                                else f"{persona_name}: уведомление не требуется."
                            ),
                            "notification_message_en": (
                                f"{persona_name}: beach packing is recommended ({best_beach})."
                                if persona_notification_state == "notify"
                                else f"{persona_name}: notification is idle."
                            ),
                        },
                    ),
                ]
            )

            planner_payload["personas"].append(
                {
                    "id": persona_id,
                    "name": persona_name,
                    "mode": mode,
                    "best_hours_outdoor": best_outdoor,
                    "best_hours_beach": best_beach,
                    "now_vs_3h": persona_now_vs if daily_plan_enabled else "disabled",
                    "outdoor_scores": {
                        "now": persona_outdoor_now,
                        "future": persona_outdoor_future,
                    },
                    "beach_scores": {
                        "now": persona_beach_now,
                        "future": persona_beach_future,
                    },
                    "pack_trigger": "ready" if persona_pack_ready else "idle",
                    "pack_list": persona_pack_list,
                    "notification_key": persona_notification_key,
                    "notification_state": persona_notification_state,
                    "person_entity_id": person_entity_id,
                }
            )

        return result, planner_payload

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
            elif entity_id == "sensor.cap_source":
                cap_link = metric.get("cap_link")
                if isinstance(cap_link, str) and cap_link.startswith(("http://", "https://")):
                    metric["icon_external_url"] = cap_link
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
        cap_data: dict[str, Any] | None,
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
                "rip_current": _noto_icon_bundle("1f30a"),
                "heat_stress": _noto_icon_bundle("1f321_fe0f"),
                "sunburn": _noto_icon_bundle("1f31e"),
                "earthquakes": _noto_icon_bundle("1f30b"),
                "wildfire": _noto_icon_bundle("1f525"),
                "hazards": _noto_icon_bundle("1f6a8"),
                "planner": _noto_icon_bundle("1f4c5"),
                "notifications": _noto_icon_bundle("1f514"),
                "uv_dose": _noto_icon_bundle("1f31e"),
                "hydration": _noto_icon_bundle("1f4a7"),
                "thunderstorm": _noto_icon_bundle("26a1_fe0f"),
                "tides_currents": _noto_icon_bundle("1f30a"),
                "algae": _noto_icon_bundle("1f9ab"),
                "smoke": _noto_icon_bundle("1f32b_fe0f"),
                "cap_alerts": _noto_icon_bundle("1f6a8"),
                "bites": _noto_icon_bundle("1f99f"),
                "tracking": _noto_icon_bundle("1f4f1"),
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
        if isinstance(cap_data, dict):
            catalog["cap_alerts"] = {
                "source": "Meteoalarm",
                "active_alerts": cap_data.get("active_count"),
                "highest_severity": cap_data.get("highest_severity"),
                "top_event": cap_data.get("top_event"),
                "top_area": cap_data.get("top_area"),
                "top_expires": cap_data.get("top_expires"),
                "top_link": cap_data.get("top_link"),
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
