"""Constants for the Beregynya AURA integration."""

DOMAIN = "bereginya_aura"
VERSION = "0.1.0"

API_ENDPOINT = "/api/bereginya_aura/v1/snapshot"
FRONTEND_STATIC_BASE = "/bereginya-aura"
FRONTEND_MODULE_URL = f"{FRONTEND_STATIC_BASE}/bereginya-aura-card.js?v={VERSION}"

DATA_FRONTEND_REGISTERED = "frontend_registered"
DATA_VIEW_REGISTERED = "view_registered"
DATA_PROVIDER = "provider"
DATA_OPTIONS = "options"

CONF_SOURCE_MODE = "source_mode"
CONF_REFRESH_SECONDS = "refresh_seconds"
CONF_SOURCES = "sources"

SOURCE_MODE_INTERNAL = "internal"
SOURCE_MODE_HYBRID = "hybrid"
SOURCE_MODE_HA_ONLY = "ha_only"
SUPPORTED_SOURCE_MODES = {
    SOURCE_MODE_INTERNAL,
    SOURCE_MODE_HYBRID,
    SOURCE_MODE_HA_ONLY,
}

DEFAULT_SOURCE_MODE = SOURCE_MODE_INTERNAL
DEFAULT_REFRESH_SECONDS = 900

SERVICE_REFRESH_SNAPSHOT = "refresh_snapshot"

INVALID_HA_STATES = {"unknown", "unavailable", "none", "None", ""}

SOURCE_KEY_ALIASES = {
    "weather_summary": "sensor.weather_summary",
    "weather_code": "sensor.weather_code",
    "precipitation_probability": "sensor.precipitation_probability",
    "precipitation": "sensor.precipitation",
    "uv_index": "sensor.uv_index",
    "wind_speed": "sensor.wind_speed",
    "pressure": "sensor.pressure",
    "humidity": "sensor.humidity",
    "sea_temperature": "sensor.sea_temperature_openmeteo",
    "sea_temperature_3h": "sensor.sea_temperature_openmeteo_3h",
    "sea_temperature_6h": "sensor.sea_temperature_openmeteo_6h",
    "wave_height": "sensor.wave_height",
    "pollen_total": "sensor.pollen_total",
    "pollen_birch": "sensor.pollen_birch",
    "pollen_alder": "sensor.pollen_alder",
    "pollen_grass": "sensor.pollen_grass",
    "pollen_olive": "sensor.pollen_olive",
    "pollen_ragweed": "sensor.pollen_ragweed",
    "pollen_mugwort": "sensor.pollen_mugwort",
    "aqi": "sensor.air_quality_european_aqi",
    "air_quality_european_aqi": "sensor.air_quality_european_aqi",
    "pm25": "sensor.air_quality_pm25",
    "pm10": "sensor.air_quality_pm10",
    "ozone": "sensor.air_quality_ozone",
    "no2": "sensor.air_quality_no2",
    "so2": "sensor.air_quality_so2",
    "co": "sensor.air_quality_co",
    "waqi": "sensor.waqi_barcelona",
    "saharan_dust_level": "sensor.saharan_dust_level",
    "saharan_dust_forecast_6h": "sensor.saharan_dust_forecast_6h",
    "beach_comfort_index": "sensor.beach_comfort_index",
    "beach_danger_index": "sensor.beach_danger_index",
    "beach_flag_calculated": "sensor.beach_flag_calculated",
    "beach_crowding_estimate": "sensor.beach_crowding_estimate",
    "beach_recommendation": "sensor.beach_recommendation",
}
