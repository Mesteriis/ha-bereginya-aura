"""Config flow for Beregynya AURA."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_DAILY_PLAN,
    CONF_DEBUG,
    CONF_FORECAST_DAYS,
    CONF_PLANNER_MODE,
    CONF_PUBLIC_SENSOR,
    CONF_REFRESH_SECONDS,
    CONF_SOURCE_MODE,
    CONF_TIMEZONES,
    DEFAULT_DAILY_PLAN,
    DEFAULT_DEBUG,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_PLANNER_MODE,
    DEFAULT_PUBLIC_SENSOR,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_SOURCE_MODE,
    DEFAULT_TIMEZONES,
    DOMAIN,
    SUPPORTED_PLANNER_MODES,
    SUPPORTED_SOURCE_MODES,
)
from .provider import normalize_options


def _build_core_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the core AURA configuration schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_SOURCE_MODE,
                default=defaults.get(CONF_SOURCE_MODE, DEFAULT_SOURCE_MODE),
            ): vol.In(sorted(SUPPORTED_SOURCE_MODES)),
            vol.Required(
                CONF_REFRESH_SECONDS,
                default=int(defaults.get(CONF_REFRESH_SECONDS, DEFAULT_REFRESH_SECONDS)),
            ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86_400)),
            vol.Required(
                CONF_FORECAST_DAYS,
                default=int(defaults.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
            vol.Required(
                CONF_TIMEZONES,
                default=str(defaults.get(CONF_TIMEZONES, DEFAULT_TIMEZONES)),
            ): str,
            vol.Required(
                CONF_DAILY_PLAN,
                default=bool(defaults.get(CONF_DAILY_PLAN, DEFAULT_DAILY_PLAN)),
            ): bool,
            vol.Required(
                CONF_PLANNER_MODE,
                default=str(defaults.get(CONF_PLANNER_MODE, DEFAULT_PLANNER_MODE)),
            ): vol.In(sorted(SUPPORTED_PLANNER_MODES)),
            vol.Required(
                CONF_DEBUG,
                default=bool(defaults.get(CONF_DEBUG, DEFAULT_DEBUG)),
            ): bool,
            vol.Required(
                CONF_PUBLIC_SENSOR,
                default=bool(defaults.get(CONF_PUBLIC_SENSOR, DEFAULT_PUBLIC_SENSOR)),
            ): bool,
        }
    )


class AuraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Beregynya AURA."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle initial UI setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            normalized = normalize_options(user_input)
            return self.async_create_entry(
                title="Beregynya AURA",
                data=normalized,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_core_schema({}),
        )

    async def async_step_import(self, import_config: dict[str, Any]):
        """Handle YAML import."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        normalized = normalize_options(import_config)
        return self.async_create_entry(
            title="Beregynya AURA",
            data=normalized,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the AURA options flow."""
        return AuraOptionsFlow(config_entry)


class AuraOptionsFlow(config_entries.OptionsFlow):
    """Manage Beregynya AURA options."""

    def __init__(self, entry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage integration options."""
        current = normalize_options({**self._entry.data, **self._entry.options})

        if user_input is not None:
            updated = {
                **current,
                **user_input,
            }
            return self.async_create_entry(
                title="",
                data=normalize_options(updated),
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_build_core_schema(current),
        )
