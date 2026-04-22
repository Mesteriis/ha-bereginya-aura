"""Beregynya AURA integration setup."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .api import BeregynyaAuraSnapshotView
from .const import (
    DATA_OPTIONS,
    DATA_FRONTEND_REGISTERED,
    DATA_PROVIDER,
    DATA_VIEW_REGISTERED,
    DOMAIN,
    FRONTEND_MODULE_URL,
    FRONTEND_STATIC_BASE,
    SERVICE_REFRESH_SNAPSHOT,
)
from .provider import AuraSnapshotProvider, normalize_options


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Beregynya AURA from YAML."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    options = _extract_yaml_options(config)
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
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Beregynya AURA config entry."""
    return True


async def _async_setup_frontend(hass: HomeAssistant) -> None:
    """Register JS resources for the Lovelace card."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(DATA_FRONTEND_REGISTERED):
        return

    frontend_dir = Path(__file__).resolve().parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_STATIC_BASE, str(frontend_dir), True)]
    )
    add_extra_js_url(hass, FRONTEND_MODULE_URL)
    domain_data[DATA_FRONTEND_REGISTERED] = True


def _extract_yaml_options(config: ConfigType) -> dict[str, Any]:
    """Extract and normalize YAML options."""
    raw = config.get(DOMAIN, {})
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    return normalize_options(raw)


async def _async_handle_refresh_snapshot(hass: HomeAssistant, _call: ServiceCall) -> None:
    """Force refresh AURA snapshot cache."""
    provider: AuraSnapshotProvider | None = hass.data.get(DOMAIN, {}).get(DATA_PROVIDER)
    if provider is None:
        return
    await provider.async_get_snapshot(force_refresh=True)
