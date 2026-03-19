"""Internal API views for Beregynya AURA."""

from __future__ import annotations

from aiohttp import web
from aiohttp.web import Request, Response
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import API_ENDPOINT, DATA_PROVIDER, DOMAIN
from .provider import AuraSnapshotProvider


class BeregynyaAuraSnapshotView(HomeAssistantView):
    """Expose the Beregynya AURA snapshot payload."""

    url = API_ENDPOINT
    name = "api:bereginya_aura:snapshot"
    requires_auth = True

    async def get(self, request: Request) -> Response:
        """Handle GET requests."""
        hass: HomeAssistant = request.app["hass"]
        domain_data = hass.data.get(DOMAIN, {})
        provider: AuraSnapshotProvider | None = domain_data.get(DATA_PROVIDER)
        if provider is None:
            return self.json(
                {"error": "bereginya_aura_not_initialized"},
                status_code=web.HTTPServiceUnavailable.status_code,
            )

        force_refresh = request.query.get("force_refresh", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        snapshot = await provider.async_get_snapshot(force_refresh=force_refresh)
        return self.json(snapshot)
