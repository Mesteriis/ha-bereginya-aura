"""Constants for the Beregynya AURA integration."""

DOMAIN = "bereginya_aura"
VERSION = "0.3.0"

API_ENDPOINT = "/api/bereginya_aura/v1/snapshot"
FRONTEND_STATIC_BASE = "/bereginya-aura"
FRONTEND_MODULE_URL = f"{FRONTEND_STATIC_BASE}/bereginya-aura-card.js?v={VERSION}"

DATA_FRONTEND_REGISTERED = "frontend_registered"
DATA_VIEW_REGISTERED = "view_registered"
DATA_PROVIDER = "provider"
DATA_OPTIONS = "options"

CONF_SOURCE_MODE = "source_mode"
CONF_REFRESH_SECONDS = "refresh_seconds"
CONF_FORECAST_DAYS = "forecast_days"
CONF_TIMEZONES = "timezones"
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
DEFAULT_FORECAST_DAYS = 7
DEFAULT_TIMEZONES = ""

SERVICE_REFRESH_SNAPSHOT = "refresh_snapshot"

INVALID_HA_STATES = {"unknown", "unavailable", "none", "None", ""}

SOURCE_KEY_ALIASES = {
    "weather_summary": "sensor.weather_summary",
    "weather_code": "sensor.weather_code",
    "precipitation_probability": "sensor.precipitation_probability",
    "precipitation": "sensor.precipitation",
    "uv_index": "sensor.uv_index",
    "rain_next_6h": "sensor.rain_next_6h",
    "wind_speed": "sensor.wind_speed",
    "pressure": "sensor.pressure",
    "humidity": "sensor.humidity",
    "sea_temperature": "sensor.sea_temperature_openmeteo",
    "sea_temperature_3h": "sensor.sea_temperature_openmeteo_3h",
    "sea_temperature_6h": "sensor.sea_temperature_openmeteo_6h",
    "wave_height": "sensor.wave_height",
    "wave_period": "sensor.wave_period",
    "pollen_total": "sensor.pollen_total",
    "pollen_birch": "sensor.pollen_birch",
    "pollen_alder": "sensor.pollen_alder",
    "pollen_grass": "sensor.pollen_grass",
    "pollen_olive": "sensor.pollen_olive",
    "pollen_ragweed": "sensor.pollen_ragweed",
    "pollen_ambrosia": "sensor.pollen_ambrosia",
    "pollen_mugwort": "sensor.pollen_mugwort",
    "ambrosia_risk": "sensor.ambrosia_risk",
    "allergy_index": "sensor.allergy_index",
    "asthma_risk": "sensor.asthma_risk",
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
    "jellyfish_risk": "sensor.jellyfish_risk",
    "jellyfish_official_risk": "sensor.jellyfish_official_risk",
    "jellyfish_official_status": "sensor.jellyfish_official_status",
    "jellyfish_species_count": "sensor.jellyfish_species_count",
    "jellyfish_last_update": "sensor.jellyfish_last_update",
    "jellyfish_icon_code": "sensor.jellyfish_icon_code",
    "jellyfish_nearest_beach": "sensor.jellyfish_nearest_beach",
    "jellyfish_nearest_beach_distance": "sensor.jellyfish_nearest_beach_distance",
    "beach_water_quality_official": "sensor.beach_water_quality_official",
    "beach_water_temperature_official": "sensor.beach_water_temperature_official",
    "tiger_mosquito_risk": "sensor.tiger_mosquito_risk",
    "tiger_mosquito_index": "sensor.tiger_mosquito_index",
    "mosquito_index": "sensor.mosquito_index",
    "tiger_mosquito_reports_30d": "sensor.tiger_mosquito_reports_30d",
    "tiger_mosquito_reports_180d": "sensor.tiger_mosquito_reports_180d",
    "tiger_mosquito_high_confidence": "sensor.tiger_mosquito_high_confidence",
    "tiger_mosquito_confidence_avg": "sensor.tiger_mosquito_confidence_avg",
    "tiger_mosquito_last_report": "sensor.tiger_mosquito_last_report",
    "tiger_mosquito_icon_url": "sensor.tiger_mosquito_icon_url",
    "tick_risk": "sensor.tick_risk",
    "tick_index": "sensor.tick_index",
    "tick_reports_30d": "sensor.tick_reports_30d",
    "tick_reports_180d": "sensor.tick_reports_180d",
    "tick_last_report": "sensor.tick_last_report",
    "tick_source": "sensor.tick_source",
    "tick_icon_url": "sensor.tick_icon_url",
    "earthquake_risk": "sensor.earthquake_risk",
    "earthquake_index": "sensor.earthquake_index",
    "earthquake_events_24h": "sensor.earthquake_events_24h",
    "earthquake_events_7d": "sensor.earthquake_events_7d",
    "earthquake_max_magnitude_7d": "sensor.earthquake_max_magnitude_7d",
    "earthquake_nearest_distance_km": "sensor.earthquake_nearest_distance_km",
    "earthquake_nearest_magnitude": "sensor.earthquake_nearest_magnitude",
    "earthquake_latest_time": "sensor.earthquake_latest_time",
    "earthquake_latest_place": "sensor.earthquake_latest_place",
    "earthquake_tsunami_events_24h": "sensor.earthquake_tsunami_events_24h",
    "earthquake_event_url": "sensor.earthquake_event_url",
    "earthquake_source": "sensor.earthquake_source",
    "wildfire_risk": "sensor.wildfire_risk",
    "wildfire_index": "sensor.wildfire_index",
    "wildfire_active_events_global": "sensor.wildfire_active_events_global",
    "wildfire_high_alert_events_global": "sensor.wildfire_high_alert_events_global",
    "wildfire_max_alert_level": "sensor.wildfire_max_alert_level",
    "wildfire_nearest_distance_km": "sensor.wildfire_nearest_distance_km",
    "wildfire_nearest_country": "sensor.wildfire_nearest_country",
    "wildfire_nearest_title": "sensor.wildfire_nearest_title",
    "wildfire_nearest_link": "sensor.wildfire_nearest_link",
    "wildfire_icon_url": "sensor.wildfire_icon_url",
    "wildfire_source": "sensor.wildfire_source",
    "hazard_active_events_global": "sensor.hazard_active_events_global",
    "hazard_high_alert_events_global": "sensor.hazard_high_alert_events_global",
    "hazard_top_event_type": "sensor.hazard_top_event_type",
    "hazard_top_event_alert": "sensor.hazard_top_event_alert",
    "hazard_top_event_title": "sensor.hazard_top_event_title",
    "hazard_top_event_country": "sensor.hazard_top_event_country",
    "hazard_top_event_distance_km": "sensor.hazard_top_event_distance_km",
    "hazard_top_event_icon_url": "sensor.hazard_top_event_icon_url",
    "hazard_last_update": "sensor.hazard_last_update",
    "hazard_source": "sensor.hazard_source",
}
