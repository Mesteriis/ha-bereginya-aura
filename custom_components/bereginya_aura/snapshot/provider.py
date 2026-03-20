"""Main snapshot provider for Beregynya AURA."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from ..const import (
    CONF_DAILY_PLAN,
    CONF_DEBUG,
    CONF_FORECAST_DAYS,
    CONF_PERSONAS,
    CONF_PLANNER_MODE,
    CONF_PUBLIC_SENSOR,
    CONF_REFRESH_SECONDS,
    CONF_SOURCE_MODE,
    CONF_TIMEZONES,
    CONF_TRACKING_ENTITIES,
    DEFAULT_DAILY_PLAN,
    DEFAULT_PLANNER_MODE,
    DEFAULT_PUBLIC_SENSOR,
    DEFAULT_TIMEZONES,
    DOMAIN,
)
from .constants import (
    _OPEN_METEO_AIR,
    _OPEN_METEO_MARINE,
    _OPEN_METEO_WEATHER,
    _PERSISTENT_CACHE_BOOTSTRAP_SECONDS,
)
from .fetchers import AuraFetchersMixin
from .metrics_core import AuraCoreMetricsMixin
from .metrics_external import AuraExternalMetricsMixin
from .metrics_persona import AuraPersonaMetricsMixin
from .options import _coerce_bool, _coerce_public_sensor, _normalize_planner_mode, normalize_options
from .shared import _build_multi_timezone_clock, _build_url, _optional_float

_LOGGER = logging.getLogger(__name__)


class AuraSnapshotProvider(
    AuraFetchersMixin,
    AuraExternalMetricsMixin,
    AuraPersonaMetricsMixin,
    AuraCoreMetricsMixin,
):
    def __init__(self, hass: HomeAssistant, options: dict[str, Any] | None) -> None:
        """Initialize provider."""
        self.hass = hass
        self._session = async_get_clientsession(hass)
        self._options = normalize_options(options)
        self._cache: dict[str, Any] | None = None
        self._cache_until = datetime.fromtimestamp(0, tz=UTC)
        self._cache_file = Path(
            self.hass.config.path(".storage", f"{DOMAIN}_snapshot.json")
        )
        self._persistent_cache_loaded = False
        self._lock = asyncio.Lock()
        self._uv_sed_by_tracker: dict[str, float] = {}
        self._uv_sed_day: str = ""
        self._uv_sed_last_update: datetime | None = None
        self._published_public_entities: set[str] = set()

    @property
    def options(self) -> dict[str, Any]:
        """Return active provider options."""
        return self._options

    def update_options(self, options: dict[str, Any] | None) -> None:
        """Apply new options and invalidate cache."""
        was_public = _coerce_public_sensor(
            self._options.get(CONF_PUBLIC_SENSOR, DEFAULT_PUBLIC_SENSOR),
            DEFAULT_PUBLIC_SENSOR,
        )
        self._options = normalize_options(options)
        is_public = _coerce_public_sensor(
            self._options.get(CONF_PUBLIC_SENSOR, DEFAULT_PUBLIC_SENSOR),
            DEFAULT_PUBLIC_SENSOR,
        )
        if was_public and not is_public:
            self.clear_public_sensor_states()
        self._cache_until = datetime.fromtimestamp(0, tz=UTC)

    def _load_persistent_cache_sync(self) -> dict[str, Any] | None:
        """Load snapshot cache from disk."""
        if not self._cache_file.is_file():
            return None
        try:
            payload = json.loads(self._cache_file.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as err:
            _LOGGER.debug("Failed to read persistent AURA cache: %s", err)
            return None
        if not isinstance(payload, dict):
            return None
        if not isinstance(payload.get("meta"), dict):
            return None
        if not isinstance(payload.get("entities"), list):
            return None
        return payload

    def _store_persistent_cache_sync(self, snapshot: dict[str, Any]) -> None:
        """Store snapshot cache to disk."""
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            encoded = json.dumps(
                snapshot,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            )
            tmp_path = self._cache_file.with_suffix(f"{self._cache_file.suffix}.tmp")
            tmp_path.write_text(encoded, encoding="utf-8")
            tmp_path.replace(self._cache_file)
        except (OSError, TypeError, ValueError) as err:
            _LOGGER.debug("Failed to store persistent AURA cache: %s", err)

    async def _async_try_load_persistent_cache(self) -> None:
        """Load persistent cache once to speed up cold start."""
        if self._persistent_cache_loaded:
            return
        self._persistent_cache_loaded = True
        snapshot = await self.hass.async_add_executor_job(self._load_persistent_cache_sync)
        if snapshot is None:
            return

        self._cache = snapshot
        ttl = int(self._options[CONF_REFRESH_SECONDS])
        now = datetime.now(tz=UTC)

        generated_at: datetime | None = None
        meta = snapshot.get("meta")
        if isinstance(meta, dict):
            generated_raw = meta.get("generated_at")
            if isinstance(generated_raw, str) and generated_raw.strip():
                generated_at = dt_util.parse_datetime(generated_raw)
                if generated_at is not None and generated_at.tzinfo is None:
                    generated_at = generated_at.replace(tzinfo=UTC)

        if generated_at is not None:
            cache_until = generated_at + timedelta(seconds=ttl)
        else:
            cache_until = datetime.fromtimestamp(0, tz=UTC)

        bootstrap_ttl = max(5, min(ttl, _PERSISTENT_CACHE_BOOTSTRAP_SECONDS))
        self._cache_until = (
            cache_until
            if cache_until > now
            else now + timedelta(seconds=bootstrap_ttl)
        )
        self._sync_public_sensor_states(snapshot)

    async def _async_store_persistent_cache(self, snapshot: dict[str, Any]) -> None:
        """Persist snapshot cache in background."""
        await self.hass.async_add_executor_job(
            self._store_persistent_cache_sync,
            snapshot,
        )

    async def async_get_snapshot(self, *, force_refresh: bool = False) -> dict[str, Any]:
        """Return cached snapshot or refresh it."""
        if not force_refresh:
            await self._async_try_load_persistent_cache()

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
            self._sync_public_sensor_states(snapshot)
            self.hass.async_create_task(self._async_store_persistent_cache(snapshot))
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
        algae_latitude = latitude
        algae_longitude = longitude
        if isinstance(jellyfish_data, dict):
            jellyfish_lat = _optional_float(jellyfish_data.get("lat"), 6)
            jellyfish_lon = _optional_float(jellyfish_data.get("lon"), 6)
            if jellyfish_lat is not None and jellyfish_lon is not None:
                algae_latitude = jellyfish_lat
                algae_longitude = jellyfish_lon
        (algae_tile_data, algae_tile_err), (smoke_tile_data, smoke_tile_err) = await asyncio.gather(
            self._async_fetch_algae_tile_data(
                latitude=algae_latitude,
                longitude=algae_longitude,
            ),
            self._async_fetch_smoke_tile_data(
                latitude=latitude,
                longitude=longitude,
            ),
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
            latitude=latitude,
            longitude=longitude,
            personas=self._options.get(CONF_PERSONAS, []),
            tracking_entities=self._options.get(CONF_TRACKING_ENTITIES, []),
            gdacs_events=gdacs_events,
            cap_data=cap_data,
            algae_tile_data=algae_tile_data,
            smoke_tile_data=smoke_tile_data,
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
            latitude=latitude,
            longitude=longitude,
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
                "debug": self._options[CONF_DEBUG],
                "public_sensor": self._options[CONF_PUBLIC_SENSOR],
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
                    "algae_tiles": "ok" if algae_tile_err is None else algae_tile_err,
                    "smoke_tiles": "ok" if smoke_tile_err is None else smoke_tile_err,
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
