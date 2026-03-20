"""Frontend resource registration for Beregynya AURA."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later

from .const import (
    FRONTEND_DIR,
    FRONTEND_MODULE_PATH,
    FRONTEND_MODULE_URL,
    FRONTEND_STATIC_BASE,
)

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.components.lovelace.const import LOVELACE_DATA as _LOVELACE_DATA_KEY
except ImportError:
    _LOVELACE_DATA_KEY = None


class AuraFrontendRegistration:
    """Register AURA frontend resources for Lovelace runtime and editor."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._lovelace = None
        self._retry_unsub = None
        self._static_ready = False
        self._extra_js_ready = False

    async def async_register(self) -> None:
        """Expose the JS bundle and register a Lovelace resource when available."""
        await self._async_register_static_path()
        if not self._extra_js_ready:
            add_extra_js_url(self.hass, FRONTEND_MODULE_URL)
            self._extra_js_ready = True
        await self._async_register_lovelace_resource()

    @callback
    def async_stop(self) -> None:
        """Cancel pending retry callbacks."""
        if self._retry_unsub is not None:
            self._retry_unsub()
            self._retry_unsub = None

    async def _async_register_static_path(self) -> None:
        """Serve the bundled frontend assets under a stable URL."""
        if self._static_ready:
            return

        frontend_dir = Path(__file__).resolve().parent / FRONTEND_DIR
        if not frontend_dir.exists():
            _LOGGER.debug("AURA frontend directory does not exist: %s", frontend_dir)
            return

        try:
            register_many = getattr(self.hass.http, "async_register_static_paths", None)
            if callable(register_many):
                from homeassistant.components.http import StaticPathConfig

                await register_many(
                    [StaticPathConfig(FRONTEND_STATIC_BASE, str(frontend_dir), cache_headers=False)]
                )
            else:
                self.hass.http.register_static_path(
                    FRONTEND_STATIC_BASE,
                    str(frontend_dir),
                    cache_headers=False,
                )
        except RuntimeError:
            _LOGGER.debug("AURA static path already registered: %s", FRONTEND_STATIC_BASE)

        self._static_ready = True

    async def _async_register_lovelace_resource(self) -> bool:
        """Ensure the AURA bundle exists in Lovelace resources on storage dashboards."""
        if self._resolve_lovelace() is None:
            self._async_schedule_retry()
            return False

        if self._lovelace_mode() != "storage":
            self.async_stop()
            return False

        resources = self._lovelace_value("resources")
        if resources is None:
            self._async_schedule_retry()
            return False

        ready = await self._async_ensure_resource(resources)
        if ready:
            self.async_stop()
            return True

        self._async_schedule_retry()
        return False

    async def _async_ensure_resource(self, resources: Any) -> bool:
        """Create or update the Lovelace module resource for AURA."""
        if getattr(resources, "loaded", None) is False and hasattr(resources, "async_get_info"):
            try:
                await resources.async_get_info()
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Failed to load Lovelace resources before AURA registration: %s", err)

        try:
            existing = list(resources.async_items())
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Failed to enumerate Lovelace resources for AURA: %s", err)
            return False

        for resource in existing:
            if str(resource.get("url", "")) == FRONTEND_MODULE_URL:
                return True

        for resource in existing:
            resource_url = str(resource.get("url", ""))
            if resource_url.split("?", maxsplit=1)[0] != FRONTEND_MODULE_PATH:
                continue
            update_item = getattr(resources, "async_update_item", None)
            if not callable(update_item):
                break
            try:
                await update_item(
                    resource.get("id"),
                    {
                        "url": FRONTEND_MODULE_URL,
                        "res_type": resource.get("res_type", resource.get("type", "module")),
                    },
                )
                return True
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug(
                    "Failed to update AURA Lovelace resource %s -> %s: %s",
                    resource_url,
                    FRONTEND_MODULE_URL,
                    err,
                )
                break

        try:
            await resources.async_create_item({"res_type": "module", "url": FRONTEND_MODULE_URL})
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Could not auto-register AURA Lovelace resource %s: %s",
                FRONTEND_MODULE_URL,
                err,
            )
            return False
        return True

    def _lovelace_mode(self) -> str | None:
        """Return Lovelace storage mode across old and new HA APIs."""
        return self._lovelace_value("resource_mode") or self._lovelace_value("mode")

    def _lovelace_value(self, key: str) -> Any:
        """Read a Lovelace runtime field from either a dict or object."""
        if self._lovelace is None:
            return None
        if isinstance(self._lovelace, dict):
            return self._lovelace.get(key)
        return getattr(self._lovelace, key, None)

    def _resolve_lovelace(self) -> Any:
        """Resolve Lovelace runtime from old or new HA storage."""
        self._lovelace = self.hass.data.get("lovelace")
        if self._lovelace is None and _LOVELACE_DATA_KEY is not None:
            self._lovelace = self.hass.data.get(_LOVELACE_DATA_KEY)
        return self._lovelace

    @callback
    def _async_schedule_retry(self) -> None:
        """Retry Lovelace registration on cold start until runtime is ready."""
        if self._retry_unsub is not None:
            return

        @callback
        async def _retry(_: Any) -> None:
            self._retry_unsub = None
            await self._async_register_lovelace_resource()

        self._retry_unsub = async_call_later(self.hass, 5, _retry)
