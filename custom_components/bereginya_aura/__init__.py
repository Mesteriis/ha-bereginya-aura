"""Beregynya AURA integration setup."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from .api import BeregynyaAuraSnapshotView
from .const import (
    CONF_REFRESH_SECONDS,
    DATA_OPTIONS,
    DATA_FRONTEND_REGISTERED,
    DATA_FRONTEND_REGISTRATION,
    DATA_PROVIDER,
    DATA_REFRESH_UNSUB,
    DATA_VIEW_REGISTERED,
    DOMAIN,
    SERVICE_REFRESH_SNAPSHOT,
)
from .frontend_registry import AuraFrontendRegistration
from .provider import AuraSnapshotProvider, normalize_options

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Beregynya AURA from YAML via config-entry import/update."""
    hass.data.setdefault(DOMAIN, {})
    await _async_handle_yaml_import(hass, config)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Beregynya AURA from a config entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    options = normalize_options({**entry.data, **entry.options})
    provider: AuraSnapshotProvider | None = domain_data.get(DATA_PROVIDER)
    if provider is None:
        provider = AuraSnapshotProvider(hass, options)
        domain_data[DATA_PROVIDER] = provider
    else:
        provider.update_options(options)
    domain_data[DATA_OPTIONS] = provider.options

    if not domain_data.get(DATA_VIEW_REGISTERED):
        hass.http.register_view(BeregynyaAuraSnapshotView)
        domain_data[DATA_VIEW_REGISTERED] = True

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_SNAPSHOT):
        async def _handle_refresh(call: ServiceCall) -> None:
            await _async_handle_refresh_snapshot(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_SNAPSHOT,
            _handle_refresh,
        )

    await _async_setup_frontend(hass)
    _async_setup_refresh_loop(hass)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Beregynya AURA config entry."""
    domain_data = hass.data.get(DOMAIN, {})
    provider: AuraSnapshotProvider | None = domain_data.get(DATA_PROVIDER)
    if provider is not None:
        provider.clear_public_sensor_states()
        domain_data.pop(DATA_PROVIDER, None)
    domain_data.pop(DATA_OPTIONS, None)
    registration: AuraFrontendRegistration | None = domain_data.get(DATA_FRONTEND_REGISTRATION)
    if registration is not None:
        registration.async_stop()
    refresh_unsub = domain_data.get(DATA_REFRESH_UNSUB)
    if callable(refresh_unsub):
        refresh_unsub()
        domain_data.pop(DATA_REFRESH_UNSUB, None)
    if hass.services.has_service(DOMAIN, SERVICE_REFRESH_SNAPSHOT):
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH_SNAPSHOT)
    return True


async def _async_setup_frontend(hass: HomeAssistant) -> None:
    """Register JS resources for the Lovelace card."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    registration: AuraFrontendRegistration | None = domain_data.get(DATA_FRONTEND_REGISTRATION)
    if registration is None:
        registration = AuraFrontendRegistration(hass)
        domain_data[DATA_FRONTEND_REGISTRATION] = registration
    await registration.async_register()
    domain_data[DATA_FRONTEND_REGISTERED] = True


def _extract_yaml_options(config: ConfigType) -> dict[str, Any]:
    """Extract and normalize YAML options."""
    raw = config.get(DOMAIN, {})
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    return normalize_options(raw)


async def _async_handle_yaml_import(hass: HomeAssistant, config: ConfigType) -> None:
    """Import YAML config into the single config entry or update the imported entry."""
    if DOMAIN not in config:
        return

    options = _extract_yaml_options(config)
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=options,
            )
        )
        return

    entry = entries[0]
    if entry.source != SOURCE_IMPORT:
        return
    if dict(entry.data) == options:
        return

    hass.config_entries.async_update_entry(entry, data=options)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_handle_refresh_snapshot(hass: HomeAssistant, _call: ServiceCall) -> None:
    """Force refresh AURA snapshot cache."""
    provider: AuraSnapshotProvider | None = hass.data.get(DOMAIN, {}).get(DATA_PROVIDER)
    if provider is None:
        return
    await provider.async_get_snapshot(force_refresh=True)


def _async_setup_refresh_loop(hass: HomeAssistant) -> None:
    """Warm and refresh the snapshot cache in background."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    provider: AuraSnapshotProvider | None = domain_data.get(DATA_PROVIDER)
    if provider is None:
        return

    existing_unsub = domain_data.get(DATA_REFRESH_UNSUB)
    if callable(existing_unsub):
        existing_unsub()

    interval_seconds = int(provider.options.get(CONF_REFRESH_SECONDS, 900))
    interval = timedelta(seconds=max(60, interval_seconds))

    async def _async_refresh(_now=None) -> None:
        try:
            await provider.async_get_snapshot(force_refresh=_now is not None)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("AURA background snapshot refresh failed: %s", err)

    domain_data[DATA_REFRESH_UNSUB] = async_track_time_interval(
        hass,
        _async_refresh,
        interval,
        cancel_on_shutdown=True,
    )
    hass.async_create_task(_async_refresh())
