"""Static constants for Beregynya AURA snapshot assembly."""

from __future__ import annotations

import logging
import re

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
_ECMWF_CAMS_WMS = "https://eccharts.ecmwf.int/wms/"
_CMEMS_WMTS = "https://wmts.marine.copernicus.eu/teroWmts"
_CMEMS_ALGAE_LAYER = (
    "OCEANCOLOUR_GLO_BGC_L4_MY_009_108/"
    "c3s_obs-oc_glo_bgc-plankton_my_l4-multi-4km_P1M_202207/CHL"
)
_CMEMS_ALGAE_STYLE = "cmap:algae"
_UTC_TOKEN_PATTERN = re.compile(r"^UTC([+-])(\d{1,2})$")
_PUBLIC_SENSOR_ID_PATTERN = re.compile(r"[^a-z0-9_]+")
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
    "sensor.astro_solar_elevation": "1f31e",
    "sensor.astro_uv_index_now": "1f31e",
    "sensor.astro_uv_index_3h_max": "1f31e",
    "sensor.astro_uv_risk_3h": "1f6a8",
    "sensor.astro_uv_now_vs_3h": "23f3",
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
    "sensor.algae_chlorophyll_mg_m3": "1f9ab",
    "sensor.algae_source": "1f9ab",
    "sensor.smoke_transport_risk": "1f32b_fe0f",
    "sensor.smoke_transport_index": "1f32b_fe0f",
    "sensor.smoke_transport_signal": "1f32b_fe0f",
    "sensor.smoke_cams_bbaod550": "1f32b_fe0f",
    "sensor.smoke_cams_pm25": "1f32b_fe0f",
    "sensor.smoke_cams_fire_frp": "1f525",
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
_CAMS_VALUE_PATTERN = re.compile(
    r"^Value:\s*([-+]?\d+(?:\.\d+)?)\s*(.*)$",
    re.MULTILINE,
)
_PERSISTENT_CACHE_BOOTSTRAP_SECONDS = 60

_LOGGER = logging.getLogger(__name__)

__all__ = [name for name in globals() if not name.startswith("__")]
