"""Configuration normalization for Beregynya AURA."""

from __future__ import annotations

from typing import Any

from ..const import (
    CONF_DAILY_PLAN,
    CONF_DALY_PLAN,
    CONF_DEBUG,
    CONF_FORECAST_DAYS,
    CONF_PLANNER_MODE,
    CONF_PUBLIC_SENSOR,
    CONF_TRACKING_ENTITIES,
    CONF_REFRESH_SECONDS,
    CONF_SOURCE_MODE,
    CONF_SOURCES,
    CONF_TIMEZONES,
    CONF_UV_TRACKING_ENTITIES,
    CONF_PERSONAS,
    DEFAULT_DAILY_PLAN,
    DEFAULT_DEBUG,
    DEFAULT_TRACKING_ENTITIES,
    DEFAULT_TIMEZONES,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_PLANNER_MODE,
    DEFAULT_PUBLIC_SENSOR,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_SOURCE_MODE,
    SOURCE_KEY_ALIASES,
    SUPPORTED_PLANNER_MODES,
    SUPPORTED_SOURCE_MODES,
)
from .constants import _PERSONA_ID_PATTERN, _TRACKING_ID_PATTERN
from .shared import (
    _normalize_timezone_token,
    _safe_float,
    _safe_int,
    _timezone_token_to_offset,
)


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


def _coerce_public_sensor(raw_value: Any, default: bool) -> bool:
    """Parse public/private style option for public sensor export."""
    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
        if normalized in {"public", "shared", "global"}:
            return True
        if normalized in {"private", "local"}:
            return False
    return _coerce_bool(raw_value, default)


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
    debug_enabled = _coerce_bool(
        options.get(CONF_DEBUG, DEFAULT_DEBUG),
        DEFAULT_DEBUG,
    )
    public_sensor_enabled = _coerce_public_sensor(
        options.get(CONF_PUBLIC_SENSOR, DEFAULT_PUBLIC_SENSOR),
        DEFAULT_PUBLIC_SENSOR,
    )

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
        CONF_DEBUG: debug_enabled,
        CONF_PUBLIC_SENSOR: public_sensor_enabled,
    }
