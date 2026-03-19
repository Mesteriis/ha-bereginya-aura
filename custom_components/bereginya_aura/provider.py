"""Data provider for Beregynya AURA."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientError
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import (
    CONF_FORECAST_DAYS,
    CONF_REFRESH_SECONDS,
    CONF_SOURCE_MODE,
    CONF_SOURCES,
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


def _coerce_state_value(raw_state: str, template_value: Any) -> Any:
    """Coerce HA state string to shape of template value."""
    if isinstance(template_value, bool):
        return raw_state.lower() in {"1", "true", "on", "yes"}
    if isinstance(template_value, int):
        return _safe_int(raw_state, template_value)
    if isinstance(template_value, float):
        return round(_safe_float(raw_state, template_value), 2)
    return raw_state


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
                    "temperature_2m,precipitation_probability,precipitation,"
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
        (weather_data, weather_err), (marine_data, marine_err), (air_data, air_err) = (
            await asyncio.gather(weather_task, marine_task, air_task)
        )

        metrics = self._build_internal_metrics(
            latitude=latitude,
            longitude=longitude,
            weather_data=weather_data,
            marine_data=marine_data,
            air_data=air_data,
        )
        forecast_daily = self._build_forecast_daily(
            forecast_days=forecast_days,
            weather_data=weather_data,
            marine_data=marine_data,
            air_data=air_data,
        )
        overrides = self._apply_ha_sources(metrics)

        return {
            "meta": {
                "source": "bereginya_aura_internal_api",
                "source_mode": self._options[CONF_SOURCE_MODE],
                "refresh_seconds": self._options[CONF_REFRESH_SECONDS],
                "forecast_days": forecast_days,
                "generated_at": datetime.now(tz=UTC).isoformat(),
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
                },
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

    def _select_hour_index(self, hourly: dict[str, Any]) -> int:
        """Pick index matching current local time or fallback to 0."""
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
        """Build metrics from remote APIs, fallbacking to deterministic defaults."""
        lat = abs(latitude)
        lon = abs(longitude)

        fallback_temp = round(15 + (lat % 8) * 0.9 + (lon % 3) * 0.5, 1)
        fallback_rain = int((lat * 3 + lon) % 45)
        fallback_uv = round(((lat + lon) % 10) * 0.7, 1)
        fallback_wind = int(6 + ((lat + lon) % 25))
        fallback_pressure = int(1008 + (lat % 5) + (lon % 4))
        fallback_humidity = int(45 + ((lat + lon) % 35))
        fallback_sea = round(12.5 + (lat % 8) * 0.45 + (lon % 4) * 0.2, 1)
        fallback_aqi = int(20 + ((lat * 2 + lon) % 40))
        fallback_pm25 = round(5 + ((lat + lon) % 20), 1)
        fallback_pm10 = round(fallback_pm25 + 8.0, 1)
        fallback_ozone = round(35 + ((lat * 1.2 + lon * 0.8) % 60), 1)
        fallback_no2 = round(8 + ((lat + lon) % 16), 1)
        fallback_so2 = round(1 + ((lat + lon * 0.5) % 4), 1)
        fallback_co = int(140 + ((lat * 3 + lon * 2) % 180))
        fallback_dust = round(2 + ((lat + lon) % 10), 1)
        fallback_weather_code = 3

        weather_hourly = weather_data.get("hourly", {}) if isinstance(weather_data, dict) else {}
        marine_hourly = marine_data.get("hourly", {}) if isinstance(marine_data, dict) else {}
        air_hourly = air_data.get("hourly", {}) if isinstance(air_data, dict) else {}

        weather_idx = self._select_hour_index(weather_hourly)
        marine_idx = self._select_hour_index(marine_hourly)
        air_idx = self._select_hour_index(air_hourly)

        temperature = round(
            _safe_float(_hourly_value(weather_hourly, "temperature_2m", weather_idx, fallback_temp), fallback_temp), 1
        )
        precipitation_probability = _safe_int(
            _hourly_value(
                weather_hourly, "precipitation_probability", weather_idx, fallback_rain
            ),
            fallback_rain,
        )
        weather_rain = weather_hourly.get("precipitation_probability", [])
        if isinstance(weather_rain, list) and weather_rain:
            rain_window = weather_rain[weather_idx : weather_idx + 6]
            rain_window_values = [
                _safe_float(value, 0.0) for value in rain_window if value is not None
            ]
            rain_next_6h = (
                int(round(max(rain_window_values)))
                if rain_window_values
                else precipitation_probability
            )
        else:
            rain_next_6h = precipitation_probability
        precipitation = round(
            _safe_float(
                _hourly_value(weather_hourly, "precipitation", weather_idx, fallback_rain / 30),
                fallback_rain / 30,
            ),
            1,
        )
        weather_code = _safe_int(
            _hourly_value(weather_hourly, "weather_code", weather_idx, fallback_weather_code),
            fallback_weather_code,
        )
        uv_index = round(
            _safe_float(_hourly_value(weather_hourly, "uv_index", weather_idx, fallback_uv), fallback_uv), 1
        )
        wind_speed = round(
            _safe_float(
                _hourly_value(weather_hourly, "wind_speed_10m", weather_idx, fallback_wind), fallback_wind
            ),
            1,
        )
        pressure = _safe_int(
            _hourly_value(weather_hourly, "surface_pressure", weather_idx, fallback_pressure),
            fallback_pressure,
        )
        humidity = _safe_int(
            _hourly_value(weather_hourly, "relative_humidity_2m", weather_idx, fallback_humidity),
            fallback_humidity,
        )

        sea_temperature = round(
            _safe_float(
                _hourly_value(marine_hourly, "sea_surface_temperature", marine_idx, fallback_sea),
                fallback_sea,
            ),
            1,
        )
        sea_temperature_3h = round(
            _safe_float(
                _hourly_value(marine_hourly, "sea_surface_temperature", marine_idx + 3, sea_temperature - 0.1),
                sea_temperature - 0.1,
            ),
            1,
        )
        sea_temperature_6h = round(
            _safe_float(
                _hourly_value(marine_hourly, "sea_surface_temperature", marine_idx + 6, sea_temperature - 0.2),
                sea_temperature - 0.2,
            ),
            1,
        )
        wave_height = round(
            _safe_float(_hourly_value(marine_hourly, "wave_height", marine_idx, 0.5), 0.5), 2
        )
        wave_period = round(
            _safe_float(_hourly_value(marine_hourly, "wave_period", marine_idx, 4.0), 4.0), 1
        )

        aqi = _safe_int(_hourly_value(air_hourly, "european_aqi", air_idx, fallback_aqi), fallback_aqi)
        pm25 = round(_safe_float(_hourly_value(air_hourly, "pm2_5", air_idx, fallback_pm25), fallback_pm25), 1)
        pm10 = round(_safe_float(_hourly_value(air_hourly, "pm10", air_idx, fallback_pm10), fallback_pm10), 1)
        ozone = round(_safe_float(_hourly_value(air_hourly, "ozone", air_idx, fallback_ozone), fallback_ozone), 1)
        no2 = round(
            _safe_float(_hourly_value(air_hourly, "nitrogen_dioxide", air_idx, fallback_no2), fallback_no2), 1
        )
        so2 = round(
            _safe_float(_hourly_value(air_hourly, "sulphur_dioxide", air_idx, fallback_so2), fallback_so2), 1
        )
        co = _safe_int(
            _hourly_value(air_hourly, "carbon_monoxide", air_idx, fallback_co), fallback_co
        )

        pollen_grass = _safe_int(
            _hourly_value(air_hourly, "grass_pollen", air_idx, int((lat + lon) % 10)),
            int((lat + lon) % 10),
        )
        pollen_birch = _safe_int(
            _hourly_value(air_hourly, "birch_pollen", air_idx, int((lat * 2) % 20)),
            int((lat * 2) % 20),
        )
        pollen_alder = _safe_int(
            _hourly_value(air_hourly, "alder_pollen", air_idx, int((lon * 1.3) % 12)),
            int((lon * 1.3) % 12),
        )
        pollen_olive = _safe_int(
            _hourly_value(air_hourly, "olive_pollen", air_idx, int((lat * lon) % 8)),
            int((lat * lon) % 8),
        )
        pollen_ragweed = _safe_int(
            _hourly_value(air_hourly, "ragweed_pollen", air_idx, int((lat + lon * 1.7) % 6)),
            int((lat + lon * 1.7) % 6),
        )
        pollen_mugwort = _safe_int(
            _hourly_value(air_hourly, "mugwort_pollen", air_idx, int((lat * 1.1 + lon * 0.9) % 6)),
            int((lat * 1.1 + lon * 0.9) % 6),
        )
        pollen_total = (
            pollen_grass
            + pollen_birch
            + pollen_alder
            + pollen_olive
            + pollen_ragweed
            + pollen_mugwort
        )
        ambrosia_risk = "low"
        if pollen_ragweed > 50:
            ambrosia_risk = "very_high"
        elif pollen_ragweed > 20:
            ambrosia_risk = "high"
        elif pollen_ragweed > 5:
            ambrosia_risk = "moderate"

        dust_now = round(
            _safe_float(_hourly_value(air_hourly, "dust", air_idx, fallback_dust), fallback_dust), 1
        )
        dust_6h = round(
            _safe_float(_hourly_value(air_hourly, "dust", air_idx + 6, dust_now), dust_now), 1
        )
        dust_level = _dust_level(dust_now)
        allergy_index = _allergy_index(float(pollen_total), float(dust_now), float(aqi))
        asthma_risk = _asthma_risk(float(aqi), float(pm25), float(dust_now), float(pollen_total))

        beach_flag = "green"
        if wave_height > 2.0 or wind_speed > 40:
            beach_flag = "red"
        elif wave_height > 1.2 or wind_speed > 25:
            beach_flag = "yellow"

        beach_danger_index = "Low"
        if beach_flag == "red" or uv_index > 10:
            beach_danger_index = "High"
        elif beach_flag == "yellow" or uv_index > 8:
            beach_danger_index = "Medium"

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

        beach_comfort = 10
        if beach_flag == "red":
            beach_comfort -= 5
        elif beach_flag == "yellow":
            beach_comfort -= 2
        if sea_temperature < 18:
            beach_comfort -= 2
        elif sea_temperature < 20:
            beach_comfort -= 1
        elif sea_temperature >= 24:
            beach_comfort += 1
        if uv_index > 10:
            beach_comfort -= 2
        elif uv_index > 8:
            beach_comfort -= 1
        if beach_crowding == "very_crowded":
            beach_comfort -= 1
        beach_comfort = max(0, min(10, beach_comfort))

        beach_recommendation = "Not ideal"
        if beach_comfort >= 7 and beach_flag == "green" and precipitation_probability < 20:
            beach_recommendation = "Recommended"

        weather_summary = _weather_summary(temperature, precipitation_probability)

        return [
            {
                "entity_id": "sensor.weather_summary",
                "name": "Weather summary",
                "value": weather_summary,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.weather_code",
                "name": "Weather code",
                "value": weather_code,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.precipitation_probability",
                "name": "Precipitation probability",
                "value": precipitation_probability,
                "unit": "%",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.precipitation",
                "name": "Precipitation",
                "value": precipitation,
                "unit": "mm",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.uv_index",
                "name": "UV index",
                "value": uv_index,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.rain_next_6h",
                "name": "Rain probability next 6h",
                "value": rain_next_6h,
                "unit": "%",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.wind_speed",
                "name": "Wind speed",
                "value": wind_speed,
                "unit": "km/h",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.pressure",
                "name": "Pressure",
                "value": pressure,
                "unit": "hPa",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.humidity",
                "name": "Humidity",
                "value": humidity,
                "unit": "%",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.sea_temperature_openmeteo",
                "name": "Sea temperature",
                "value": sea_temperature,
                "unit": "degC",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.sea_temperature_openmeteo_3h",
                "name": "Sea temperature +3h",
                "value": sea_temperature_3h,
                "unit": "degC",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.sea_temperature_openmeteo_6h",
                "name": "Sea temperature +6h",
                "value": sea_temperature_6h,
                "unit": "degC",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.wave_height",
                "name": "Wave height",
                "value": wave_height,
                "unit": "m",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.wave_period",
                "name": "Wave period",
                "value": wave_period,
                "unit": "s",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.pollen_total",
                "name": "Pollen total",
                "value": pollen_total,
                "unit": "grains/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.pollen_birch",
                "name": "Pollen birch",
                "value": pollen_birch,
                "unit": "grains/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.pollen_alder",
                "name": "Pollen alder",
                "value": pollen_alder,
                "unit": "grains/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.pollen_grass",
                "name": "Pollen grass",
                "value": pollen_grass,
                "unit": "grains/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.pollen_olive",
                "name": "Pollen olive",
                "value": pollen_olive,
                "unit": "grains/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.pollen_ragweed",
                "name": "Pollen ragweed",
                "value": pollen_ragweed,
                "unit": "grains/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.pollen_ambrosia",
                "name": "Pollen ambrosia",
                "value": pollen_ragweed,
                "unit": "grains/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.ambrosia_risk",
                "name": "Ambrosia risk",
                "value": ambrosia_risk,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.allergy_index",
                "name": "Allergy index",
                "value": allergy_index,
                "unit": "/100",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.asthma_risk",
                "name": "Asthma risk",
                "value": asthma_risk,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.pollen_mugwort",
                "name": "Pollen mugwort",
                "value": pollen_mugwort,
                "unit": "grains/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.air_quality_european_aqi",
                "name": "European AQI",
                "value": aqi,
                "unit": "AQI",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.air_quality_pm25",
                "name": "PM2.5",
                "value": pm25,
                "unit": "ug/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.air_quality_pm10",
                "name": "PM10",
                "value": pm10,
                "unit": "ug/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.air_quality_ozone",
                "name": "Ozone (O3)",
                "value": ozone,
                "unit": "ug/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.air_quality_no2",
                "name": "Nitrogen dioxide",
                "value": no2,
                "unit": "ug/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.air_quality_so2",
                "name": "Sulfur dioxide",
                "value": so2,
                "unit": "ug/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.air_quality_co",
                "name": "Carbon monoxide",
                "value": co,
                "unit": "ug/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.waqi_barcelona",
                "name": "WAQI proxy",
                "value": aqi + 12,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.saharan_dust_level",
                "name": "Saharan dust level",
                "value": dust_level,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.saharan_dust_forecast_6h",
                "name": "Saharan dust forecast +6h",
                "value": dust_6h,
                "unit": "ug/m3",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.beach_flag_calculated",
                "name": "Beach flag (calculated)",
                "value": beach_flag,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.beach_danger_index",
                "name": "Beach danger index",
                "value": beach_danger_index,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.beach_crowding_estimate",
                "name": "Beach crowding estimate",
                "value": beach_crowding,
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.beach_comfort_index",
                "name": "Beach comfort index",
                "value": beach_comfort,
                "unit": "/10",
                "source": "internal_api",
            },
            {
                "entity_id": "sensor.beach_recommendation",
                "name": "Beach recommendation",
                "value": beach_recommendation,
                "source": "internal_api",
            },
        ]

    def _build_forecast_daily(
        self,
        *,
        forecast_days: int,
        weather_data: dict[str, Any] | None,
        marine_data: dict[str, Any] | None,
        air_data: dict[str, Any] | None,
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
                }
            )

        return result

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
