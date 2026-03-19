"""Constants for the Beregynya AURA integration."""

DOMAIN = "bereginya_aura"
VERSION = "0.5.0"

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
CONF_PERSONAS = "personas"
CONF_DAILY_PLAN = "daily_plan"
CONF_DALY_PLAN = "daly_plan"
CONF_PLANNER_MODE = "planner_mode"
CONF_TRACKING_ENTITIES = "tracking_entities"
CONF_UV_TRACKING_ENTITIES = "uv_tracking_entities"

PLANNER_MODE_NORMAL = "normal"
PLANNER_MODE_CHILD = "child"
PLANNER_MODE_ELDERLY = "elderly"
PLANNER_MODE_SPORT = "sport"
PLANNER_MODE_BEACH_DAY = "beach_day"
SUPPORTED_PLANNER_MODES = {
    PLANNER_MODE_NORMAL,
    PLANNER_MODE_CHILD,
    PLANNER_MODE_ELDERLY,
    PLANNER_MODE_SPORT,
    PLANNER_MODE_BEACH_DAY,
}

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
DEFAULT_DAILY_PLAN = True
DEFAULT_PLANNER_MODE = PLANNER_MODE_NORMAL
DEFAULT_TRACKING_ENTITIES: list[dict[str, object]] = []

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
    "rip_current_risk": "sensor.rip_current_risk",
    "rip_current_index": "sensor.rip_current_index",
    "heat_stress_risk": "sensor.heat_stress_risk",
    "heat_stress_index": "sensor.heat_stress_index",
    "heat_index_c": "sensor.heat_index_c",
    "wet_bulb_c": "sensor.wet_bulb_c",
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
    "daily_plan_status": "sensor.aura_daily_plan_status",
    "planner_mode": "sensor.aura_planner_mode_default",
    "planner_mode_default": "sensor.aura_planner_mode_default",
    "now_vs_3h_outdoor": "sensor.aura_now_vs_3h_outdoor",
    "now_vs_3h_beach": "sensor.aura_now_vs_3h_beach",
    "now_vs_3h_summary": "sensor.aura_now_vs_3h_summary",
    "beach_pack_trigger": "sensor.aura_beach_pack_trigger",
    "beach_pack_list": "sensor.aura_beach_pack_list",
    "beach_notification_key": "sensor.aura_beach_notification_key",
    "beach_notification_state": "sensor.aura_beach_notification_state",
    "uv_dose_sed_1h": "sensor.uv_dose_sed_1h",
    "uv_dose_sed_today_est": "sensor.uv_dose_sed_today_est",
    "uv_dose_status": "sensor.uv_dose_status",
    "wbgt_c": "sensor.wbgt_c",
    "dehydration_index": "sensor.dehydration_index",
    "dehydration_risk": "sensor.dehydration_risk",
    "thunderstorm_risk": "sensor.thunderstorm_risk",
    "thunderstorm_index": "sensor.thunderstorm_index",
    "thunderstorm_cape": "sensor.thunderstorm_cape",
    "thunderstorm_nowcast_3h": "sensor.thunderstorm_nowcast_3h",
    "tide_level_m": "sensor.tide_level_m",
    "tide_trend_3h": "sensor.tide_trend_3h",
    "tide_range_24h_m": "sensor.tide_range_24h_m",
    "ocean_current_speed": "sensor.ocean_current_speed",
    "ocean_current_direction": "sensor.ocean_current_direction",
    "current_risk": "sensor.current_risk",
    "algae_bloom_risk": "sensor.algae_bloom_risk",
    "algae_bloom_index": "sensor.algae_bloom_index",
    "algae_bloom_signal": "sensor.algae_bloom_signal",
    "algae_source": "sensor.algae_source",
    "smoke_transport_risk": "sensor.smoke_transport_risk",
    "smoke_transport_index": "sensor.smoke_transport_index",
    "smoke_transport_signal": "sensor.smoke_transport_signal",
    "smoke_source": "sensor.smoke_source",
    "cap_alert_risk": "sensor.cap_alert_risk",
    "cap_alert_index": "sensor.cap_alert_index",
    "cap_alerts_active": "sensor.cap_alerts_active",
    "cap_highest_severity": "sensor.cap_highest_severity",
    "cap_top_event": "sensor.cap_top_event",
    "cap_top_area": "sensor.cap_top_area",
    "cap_top_expires": "sensor.cap_top_expires",
    "cap_source": "sensor.cap_source",
    "bite_index": "sensor.bite_index",
    "bite_risk": "sensor.bite_risk",
    "bite_outlook_3d": "sensor.bite_outlook_3d",
}
