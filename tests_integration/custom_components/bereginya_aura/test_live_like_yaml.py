"""Live-like hybrid YAML runtime regression tests for Beregynya AURA."""

from __future__ import annotations

import asyncio

import pytest

from custom_components.bereginya_aura.const import DOMAIN

from .common import async_setup_aura_runtime


pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("live_socket_enabled")]


LIVE_LIKE = {
    "source_mode": "hybrid",
    "refresh_seconds": 600,
    "forecast_days": 7,
    "timezones": "UTC+01,UTC+03,UTC-05",
    "daily_plan": True,
    "planner_mode": "normal",
    "tracking_entities": [
        {
            "id": "vem_main",
            "entity_id": "person.victoria_meshchryakovf",
            "uv_exposure_factor": 1.0,
        },
        {
            "id": "avm_main",
            "entity_id": "person.aleksandr_meshcheriakov",
            "uv_exposure_factor": 1.1,
        },
    ],
    "personas": [
        {
            "id": "vem",
            "name": "VEM",
            "person_entity_id": "person.victoria_meshchryakovf",
            "tracker_entity_id": "person.victoria_meshchryakovf",
            "skin_type": 2,
            "planner_mode": "normal",
            "uv_exposure_factor": 1.0,
        },
        {
            "id": "avm",
            "name": "AVM",
            "person_entity_id": "person.aleksandr_meshcheriakov",
            "tracker_entity_id": "person.aleksandr_meshcheriakov",
            "skin_type": 3,
            "planner_mode": "normal",
            "uv_exposure_factor": 1.1,
        },
    ],
    "sources": {
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
        "wave_period": "sensor.wave_period",
        "pollen_total": "sensor.pollen_total",
        "pollen_birch": "sensor.pollen_birch",
        "pollen_alder": "sensor.pollen_alder",
        "pollen_grass": "sensor.pollen_grass",
        "pollen_olive": "sensor.pollen_olive",
        "pollen_ragweed": "sensor.pollen_ragweed",
        "pollen_ambrosia": "sensor.pollen_ragweed",
        "pollen_mugwort": "sensor.pollen_mugwort",
        "aqi": "sensor.air_quality_european_aqi",
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
        "mosquito_index": "sensor.mosquito_index",
        "tick_risk": "sensor.tick_risk",
        "tick_index": "sensor.tick_index",
    },
}


async def test_live_like_yaml_profile(hass, enable_custom_integrations) -> None:
    """Reproduce the live hybrid YAML profile in a test runtime."""
    hass.states.async_set(
        "person.victoria_meshchryakovf",
        "home",
        {"latitude": 41.38, "longitude": 2.17},
    )
    hass.states.async_set(
        "person.aleksandr_meshcheriakov",
        "home",
        {"latitude": 41.38, "longitude": 2.17},
    )

    entry = await async_setup_aura_runtime(hass, data=LIVE_LIKE)
    try:
        provider = hass.data[DOMAIN]["provider"]
        snapshot = await provider.async_get_snapshot(force_refresh=True)
        assert snapshot["entities"]
        assert snapshot["meta"]["fetch"]["weather"] == "ok"
    finally:
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_stop(force=True)
        await asyncio.sleep(1)
        await hass.async_block_till_done()
