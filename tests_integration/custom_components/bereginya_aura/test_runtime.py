"""Real Home Assistant runtime smoke tests for Beregynya AURA."""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("homeassistant")
pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.config_entries import SOURCE_IMPORT  # noqa: E402

from custom_components.bereginya_aura.const import (  # noqa: E402
    API_ENDPOINT,
    DOMAIN,
    FRONTEND_MODULE_URL,
    SERVICE_REFRESH_SNAPSHOT,
)

from .common import (  # noqa: E402
    async_setup_aura_from_yaml,
    async_setup_aura_runtime,
    aura_test_entry_data,
)


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("live_socket_enabled"),
]


async def test_runtime_registers_lovelace_resource_and_serves_frontend_bundle(
    hass,
    enable_custom_integrations,
    hass_client,
) -> None:
    """AURA should materialize a Lovelace resource and serve its JS bundle."""
    entry = await async_setup_aura_runtime(hass)
    client = None
    try:
        lovelace = hass.data["lovelace"]
        resources = lovelace["resources"].async_items()
        assert any(item["url"] == FRONTEND_MODULE_URL for item in resources)

        client = await hass_client()
        response = await client.get(FRONTEND_MODULE_URL)
        assert response.status == 200
        body = await response.text()
        assert 'type: "bereginya-aura"' in body
        assert "customElements.define(AURA_TAG_NAME, BeregynyaAuraCard);" in body
    finally:
        if client is not None:
            await client.close()
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_stop(force=True)
        await asyncio.sleep(1)
        await hass.async_block_till_done()


async def test_runtime_snapshot_api_returns_live_network_backed_payload(
    hass,
    enable_custom_integrations,
    hass_client,
) -> None:
    """AURA snapshot API should return a live payload built from real upstream APIs."""
    entry = await async_setup_aura_runtime(hass)
    client = None
    try:
        client = await hass_client()
        response = await client.get(API_ENDPOINT)
        assert response.status == 200
        payload = await response.json()

        assert payload["meta"]["source"] == "bereginya_aura_internal_api"
        assert payload["meta"]["fetch"]["weather"] == "ok"
        assert payload["meta"]["fetch"]["marine"] == "ok"
        assert payload["meta"]["fetch"]["air_quality"] == "ok"
        assert len(payload["forecast_daily"]) >= 2

        entity_ids = {item["entity_id"] for item in payload["entities"]}
        assert "sensor.uv_index" in entity_ids
        assert "sensor.beach_comfort_index" in entity_ids
        assert "sensor.air_quality_european_aqi" in entity_ids
    finally:
        if client is not None:
            await client.close()
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_stop(force=True)
        await asyncio.sleep(1)
        await hass.async_block_till_done()


async def test_runtime_public_sensor_mode_publishes_snapshot_entities(
    hass,
    enable_custom_integrations,
    hass_client,
) -> None:
    """AURA should publish public HA sensors after a real refresh cycle."""
    entry = await async_setup_aura_runtime(
        hass,
        data=aura_test_entry_data(public_sensor=True),
    )
    client = None
    try:
        await hass.services.async_call(DOMAIN, SERVICE_REFRESH_SNAPSHOT, {}, blocking=True)
        await hass.async_block_till_done()

        snapshot_state = hass.states.get(f"sensor.{DOMAIN}_snapshot")
        uv_state = hass.states.get(f"sensor.{DOMAIN}_uv_index")
        beach_state = hass.states.get(f"sensor.{DOMAIN}_beach_comfort_index")

        assert snapshot_state is not None
        assert int(snapshot_state.state) > 0
        assert uv_state is not None
        assert beach_state is not None

        client = await hass_client()
        response = await client.get(API_ENDPOINT)
        assert response.status == 200
        payload = await response.json()

        assert snapshot_state.attributes["metric_count"] == len(payload["entities"])
        assert snapshot_state.attributes["generated_at"] == payload["meta"]["generated_at"]
    finally:
        if client is not None:
            await client.close()
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_stop(force=True)
        await asyncio.sleep(1)
        await hass.async_block_till_done()


async def test_runtime_unload_removes_provider_and_service(
    hass,
    enable_custom_integrations,
    hass_client,
) -> None:
    """Unloading AURA should disable its runtime API/service state."""
    entry = await async_setup_aura_runtime(hass)
    client = None
    try:
        client = await hass_client()
        response = await client.get(API_ENDPOINT)
        assert response.status == 200

        assert hass.data[DOMAIN]["provider"] is not None
        assert hass.services.has_service(DOMAIN, SERVICE_REFRESH_SNAPSHOT)

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

        assert "provider" not in hass.data[DOMAIN]
        assert not hass.services.has_service(DOMAIN, SERVICE_REFRESH_SNAPSHOT)

        unloaded = await client.get(API_ENDPOINT)
        assert unloaded.status == 503
        payload = await unloaded.json()
        assert payload["error"] == "bereginya_aura_not_initialized"
    finally:
        if client is not None:
            await client.close()
        await hass.async_stop(force=True)
        await asyncio.sleep(1)
        await hass.async_block_till_done()


async def test_runtime_options_update_reloads_provider(
    hass,
    enable_custom_integrations,
) -> None:
    """Updating options should reload the entry and apply them immediately."""
    entry = await async_setup_aura_runtime(hass)
    try:
        provider = hass.data[DOMAIN]["provider"]
        assert provider.options["public_sensor"] is False

        hass.config_entries.async_update_entry(entry, options={"public_sensor": True})
        await hass.async_block_till_done()

        provider = hass.data[DOMAIN]["provider"]
        assert provider.options["public_sensor"] is True
    finally:
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_stop(force=True)
        await asyncio.sleep(1)
        await hass.async_block_till_done()


async def test_yaml_config_is_imported_into_single_config_entry(
    hass,
    enable_custom_integrations,
) -> None:
    """YAML setup should materialize a SOURCE_IMPORT config entry."""
    yaml_data = {
        **aura_test_entry_data(),
        "refresh_seconds": 601,
    }
    entry = await async_setup_aura_from_yaml(hass, data=yaml_data)
    try:
        assert entry.source == SOURCE_IMPORT
        assert entry.data["refresh_seconds"] == 601
        provider = hass.data[DOMAIN]["provider"]
        assert provider.options["refresh_seconds"] == 601
    finally:
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_stop(force=True)
        await asyncio.sleep(1)
        await hass.async_block_till_done()
