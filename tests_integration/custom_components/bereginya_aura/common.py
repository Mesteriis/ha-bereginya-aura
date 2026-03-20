"""Shared helpers for Beregynya AURA integration runtime tests."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bereginya_aura.const import DOMAIN


def aura_test_entry_data(*, public_sensor: bool = False) -> dict[str, Any]:
    """Return deterministic config entry data for AURA runtime tests."""
    return {
        "source_mode": "internal",
        "refresh_seconds": 900,
        "forecast_days": 2,
        "timezones": "UTC+01,UTC+03,UTC-05",
        "debug": False,
        "public_sensor": public_sensor,
        "daily_plan": True,
        "planner_mode": "normal",
        "personas": [
            {
                "id": "vem",
                "name": "VEM",
                "skin_type": 2,
                "planner_mode": "normal",
            },
            {
                "id": "avm",
                "name": "AVM",
                "skin_type": 3,
                "planner_mode": "sport",
            },
        ],
    }


async def async_setup_aura_runtime(
    hass,
    *,
    data: dict[str, Any] | None = None,
) -> MockConfigEntry:
    """Set up a real Home Assistant runtime for AURA smoke tests."""
    await async_bootstrap_aura_runtime(hass)

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Beregynya AURA",
        data=data or aura_test_entry_data(),
        version=1,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def async_bootstrap_aura_runtime(hass) -> None:
    """Prepare core HA dependencies required by the AURA config entry."""
    hass.config.latitude = 41.3851
    hass.config.longitude = 2.1734
    hass.config.elevation = 12
    hass.config.time_zone = "Europe/Madrid"

    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(hass, "frontend", {})
    assert await async_setup_component(hass, "lovelace", {"lovelace": {"mode": "storage"}})
    await hass.async_block_till_done()


async def async_setup_aura_from_yaml(
    hass,
    *,
    data: dict[str, Any] | None = None,
):
    """Trigger YAML import/setup path and return the created config entry."""
    await async_bootstrap_aura_runtime(hass)
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: data or aura_test_entry_data()})
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.source == SOURCE_IMPORT
    return entry
