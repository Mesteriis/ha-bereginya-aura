"""External-domain metric builders for Beregynya AURA."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.util import dt as dt_util

from .constants import *  # noqa: F403
from .shared import *  # noqa: F403


class AuraExternalMetricsMixin:
    def _build_tick_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        tick_data: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """Build tick metrics from iNaturalist observations + weather suitability."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        temperature = _optional_float(values.get("sensor.apparent_temperature"))
        if temperature is None:
            temperature = _optional_float(values.get("sensor.sea_temperature_openmeteo"))
        humidity = _optional_float(values.get("sensor.humidity"))
        rain_next_6h = _optional_float(values.get("sensor.rain_next_6h"))
        wind_speed_ms = _optional_float(values.get("sensor.wind_speed"))
        wind_speed = _ms_to_kmh(wind_speed_ms)

        weather_index: int | None = None
        if (
            temperature is not None
            and humidity is not None
            and rain_next_6h is not None
            and wind_speed is not None
        ):
            weather_index = _tick_index_from_weather(
                temperature=temperature,
                humidity=humidity,
                rain_prob_next_6h=rain_next_6h,
                wind_speed=wind_speed,
            )

        count_30d = 0
        count_180d = 0
        latest_report = "unknown"
        latest_days_ago = 999
        research_pct = 0
        source = "internal_model"
        taxon_label = "Ixodida"
        icon_url = None

        if isinstance(tick_data, dict):
            source = "inaturalist_api"
            count_30d = _safe_int(tick_data.get("count_30d"), 0)
            count_180d = _safe_int(tick_data.get("count_180d"), 0)
            latest_report = str(tick_data.get("latest_observed_at") or "unknown")
            latest_days_ago = _safe_int(tick_data.get("latest_days_ago"), 999)
            research_pct = _safe_int(tick_data.get("research_pct"), 0)
            icon_url = tick_data.get("icon_url")
            taxon_name = tick_data.get("taxon_name")
            common_name = tick_data.get("common_name")
            if isinstance(common_name, str) and common_name.strip():
                taxon_label = common_name
            elif isinstance(taxon_name, str) and taxon_name.strip():
                taxon_label = taxon_name

        obs_boost = min(count_30d * 5, 45) + min(count_180d, 25)
        quality_boost = int(round((research_pct - 45) / 6))
        if weather_index is None and source != "inaturalist_api":
            tick_index: int | None = None
        else:
            base = weather_index if weather_index is not None else 20
            tick_index = base + obs_boost + quality_boost

        if tick_index is not None:
            if latest_days_ago > 120:
                tick_index = min(tick_index, 25)
            elif latest_days_ago > 60:
                tick_index = min(tick_index, 40)
            elif latest_days_ago > 30:
                tick_index = min(tick_index, 55)
            tick_index = max(0, min(100, tick_index))
        tick_risk = _tick_risk_from_index(tick_index) if tick_index is not None else "unavailable"

        if source == "internal_model" and tick_index is None:
            source = "unavailable"

        return (
            [
                {
                    "entity_id": "sensor.tick_risk",
                    "name": "Tick risk",
                    "value": tick_risk,
                    "source": source,
                    "icon": "mdi:bug-outline",
                },
                {
                    "entity_id": "sensor.tick_index",
                    "name": "Tick index",
                    "value": tick_index if tick_index is not None else "unavailable",
                    "unit": "/100",
                    "source": source,
                    "icon": "mdi:chart-line",
                },
                {
                    "entity_id": "sensor.tick_reports_30d",
                    "name": "Tick reports 30d",
                    "value": count_30d,
                    "source": source,
                    "icon": "mdi:calendar-month",
                },
                {
                    "entity_id": "sensor.tick_reports_180d",
                    "name": "Tick reports 180d",
                    "value": count_180d,
                    "source": source,
                    "icon": "mdi:calendar-range",
                },
                {
                    "entity_id": "sensor.tick_last_report",
                    "name": "Tick last report",
                    "value": latest_report,
                    "source": source,
                    "icon": "mdi:clock-outline",
                },
                {
                    "entity_id": "sensor.tick_source",
                    "name": "Tick source",
                    "value": taxon_label,
                    "source": source,
                    "icon": "mdi:database-search-outline",
                },
                {
                    "entity_id": "sensor.tick_icon_url",
                    "name": "Tick icon URL",
                    "value": icon_url if isinstance(icon_url, str) and icon_url else "unavailable",
                    "source": source,
                    "icon": "mdi:image-outline",
                },
            ],
            tick_index,
        )

    def _build_jellyfish_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        jellyfish_data: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], str]:
        """Build jellyfish-related metrics with official + model estimate."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        sea_temp = _optional_float(values.get("sensor.sea_temperature_openmeteo"))
        wave_height = _optional_float(values.get("sensor.wave_height"))
        wind_speed_ms = _optional_float(values.get("sensor.wind_speed"))
        wind_speed = _ms_to_kmh(wind_speed_ms)
        estimated_risk = (
            _jellyfish_risk_from_weather(sea_temp, wave_height, wind_speed)
            if sea_temp is not None and wave_height is not None and wind_speed is not None
            else "unavailable"
        )

        official_status = None
        official_tag = None
        official_species_count = 0
        official_last_update = "unknown"
        nearest_beach = "unknown"
        nearest_dist_km: float | None = None
        water_quality = "unknown"
        water_temp_official: float | None = None
        off_season = False
        source = "internal_model"
        icon_code = None

        if isinstance(jellyfish_data, dict):
            source = "platgescat_api"
            official_status = jellyfish_data.get("status_label") or jellyfish_data.get(
                "front_medusa_label"
            )
            official_tag = jellyfish_data.get("status_tag") or jellyfish_data.get(
                "front_medusa_tag"
            )
            species = jellyfish_data.get("species_list")
            if isinstance(species, list):
                official_species_count = len(species)
            official_last_update = str(jellyfish_data.get("last_update") or "unknown")
            nearest_beach = str(jellyfish_data.get("beach_name") or "unknown")
            nearest_dist_km = _optional_float(jellyfish_data.get("distance_km"), 2)
            icon_code = jellyfish_data.get("status_icon")
            water_quality = str(
                jellyfish_data.get("water_quality")
                or jellyfish_data.get("front_water_quality_tag")
                or "unknown"
            )
            water_temp_official = _optional_float(
                jellyfish_data.get("water_temp_c", jellyfish_data.get("front_water_temp")),
                1,
            )
            off_season = bool(jellyfish_data.get("off_season"))

        official_risk = _normalize_jellyfish_risk(
            status_label=official_status if isinstance(official_status, str) else None,
            status_tag=official_tag if isinstance(official_tag, str) else None,
            off_season=off_season,
        )
        combined_risk = official_risk if official_risk not in {"unknown", ""} else estimated_risk

        return (
            [
                {
                    "entity_id": "sensor.jellyfish_risk",
                    "name": "Jellyfish risk",
                    "value": combined_risk,
                    "source": source,
                    "icon": "mdi:jellyfish",
                },
                {
                    "entity_id": "sensor.jellyfish_official_risk",
                    "name": "Jellyfish official risk",
                    "value": official_risk,
                    "source": source,
                    "icon": "mdi:shield-wave",
                },
                {
                    "entity_id": "sensor.jellyfish_official_status",
                    "name": "Jellyfish official status",
                    "value": official_status or "unknown",
                    "source": source,
                    "icon": "mdi:information-outline",
                },
                {
                    "entity_id": "sensor.jellyfish_species_count",
                    "name": "Jellyfish species count",
                    "value": official_species_count,
                    "source": source,
                    "icon": "mdi:fishbowl-outline",
                },
                {
                    "entity_id": "sensor.jellyfish_last_update",
                    "name": "Jellyfish last update",
                    "value": official_last_update,
                    "source": source,
                    "icon": "mdi:clock-outline",
                },
                {
                    "entity_id": "sensor.jellyfish_nearest_beach",
                    "name": "Nearest beach (PlatgesCat)",
                    "value": nearest_beach,
                    "source": source,
                    "icon": "mdi:beach",
                },
                {
                    "entity_id": "sensor.jellyfish_nearest_beach_distance",
                    "name": "Nearest beach distance",
                    "value": nearest_dist_km if nearest_dist_km is not None else "unavailable",
                    "unit": "km",
                    "source": source,
                    "icon": "mdi:map-marker-distance",
                },
                {
                    "entity_id": "sensor.beach_water_quality_official",
                    "name": "Beach water quality (official)",
                    "value": water_quality,
                    "source": source,
                    "icon": "mdi:water-check",
                },
                {
                    "entity_id": "sensor.beach_water_temperature_official",
                    "name": "Beach water temperature (official)",
                    "value": (
                        water_temp_official
                        if water_temp_official is not None
                        else "unavailable"
                    ),
                    "unit": "degC",
                    "source": source,
                    "icon": "mdi:coolant-temperature",
                },
                {
                    "entity_id": "sensor.jellyfish_icon_code",
                    "name": "Jellyfish icon code",
                    "value": icon_code if isinstance(icon_code, str) and icon_code else "unknown",
                    "source": source,
                    "icon": "mdi:image-outline",
                },
            ],
            combined_risk,
        )

    def _build_tiger_mosquito_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        mosquito_data: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """Build tiger-mosquito metrics with observations + weather."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        humidity = _optional_float(values.get("sensor.humidity"))
        rain_next_6h = _optional_float(values.get("sensor.rain_next_6h"))
        wind_speed_ms = _optional_float(values.get("sensor.wind_speed"))
        wind_speed = _ms_to_kmh(wind_speed_ms)

        weather_index: int | None = None
        if humidity is not None and rain_next_6h is not None and wind_speed is not None:
            weather_index = _mosquito_index_from_weather(humidity, rain_next_6h, wind_speed)
        count_30d = 0
        count_180d = 0
        high_conf_pct = 0
        confidence_avg_pct = 0
        latest_report = "unknown"
        latest_days_ago = 999
        source = "internal_model"
        icon_url = None

        if isinstance(mosquito_data, dict):
            source = "mosquito_alert_api"
            count_30d = _safe_int(mosquito_data.get("count_30d"), 0)
            count_180d = _safe_int(mosquito_data.get("count_180d"), 0)
            high_conf_pct = _safe_int(mosquito_data.get("high_confidence_pct"), 0)
            confidence_avg_pct = _safe_int(mosquito_data.get("confidence_avg_pct"), 0)
            latest_report = str(mosquito_data.get("latest_received_at") or "unknown")
            latest_days_ago = _safe_int(mosquito_data.get("latest_days_ago"), 999)
            icon_url = mosquito_data.get("icon_url")

        observation_boost = min(count_30d * 4, 42) + min(count_180d, 30)
        confidence_adjustment = int(round((high_conf_pct - 50) / 5))
        if weather_index is None and source != "mosquito_alert_api":
            mosquito_index: int | None = None
        else:
            base = weather_index if weather_index is not None else 20
            mosquito_index = base + observation_boost + confidence_adjustment
            if latest_days_ago > 120:
                mosquito_index = min(mosquito_index, 30)
            elif latest_days_ago > 60:
                mosquito_index = min(mosquito_index, 45)
            elif latest_days_ago > 30:
                mosquito_index = min(mosquito_index, 60)
            mosquito_index = max(0, min(100, mosquito_index))
        mosquito_risk = (
            _mosquito_risk_from_index(mosquito_index)
            if mosquito_index is not None
            else "unavailable"
        )

        if source == "internal_model" and mosquito_index is None:
            source = "unavailable"

        return (
            [
                {
                    "entity_id": "sensor.tiger_mosquito_risk",
                    "name": "Tiger mosquito risk",
                    "value": mosquito_risk,
                    "source": source,
                    "icon": "mdi:mosquito",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_index",
                    "name": "Tiger mosquito index",
                    "value": mosquito_index if mosquito_index is not None else "unavailable",
                    "unit": "/100",
                    "source": source,
                    "icon": "mdi:chart-bell-curve-cumulative",
                },
                {
                    "entity_id": "sensor.mosquito_index",
                    "name": "Mosquito index",
                    "value": mosquito_index if mosquito_index is not None else "unavailable",
                    "unit": "/100",
                    "source": source,
                    "icon": "mdi:chart-bell-curve-cumulative",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_reports_30d",
                    "name": "Tiger mosquito reports 30d",
                    "value": count_30d,
                    "source": source,
                    "icon": "mdi:calendar-month",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_reports_180d",
                    "name": "Tiger mosquito reports 180d",
                    "value": count_180d,
                    "source": source,
                    "icon": "mdi:calendar-range",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_high_confidence",
                    "name": "Tiger mosquito high confidence",
                    "value": high_conf_pct,
                    "unit": "%",
                    "source": source,
                    "icon": "mdi:certificate-outline",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_confidence_avg",
                    "name": "Tiger mosquito confidence avg",
                    "value": confidence_avg_pct,
                    "unit": "%",
                    "source": source,
                    "icon": "mdi:percent-outline",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_last_report",
                    "name": "Tiger mosquito last report",
                    "value": latest_report,
                    "source": source,
                    "icon": "mdi:clock-outline",
                },
                {
                    "entity_id": "sensor.tiger_mosquito_icon_url",
                    "name": "Tiger mosquito icon URL",
                    "value": icon_url if isinstance(icon_url, str) and icon_url else "unavailable",
                    "source": source,
                    "icon": "mdi:image-outline",
                },
            ],
            mosquito_index,
        )

    def _build_earthquake_metrics(
        self,
        *,
        earthquake_data: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Build earthquake metrics from USGS observations near home point."""
        source = "usgs_api" if isinstance(earthquake_data, dict) else "unavailable"

        count_24h: Any = "unavailable"
        count_7d: Any = "unavailable"
        max_mag_7d: Any = "unavailable"
        nearest_distance_km: Any = "unavailable"
        nearest_magnitude: Any = "unavailable"
        latest_time: Any = "unavailable"
        latest_place: Any = "unavailable"
        tsunami_24h: Any = "unavailable"
        event_url: Any = "unavailable"
        eq_index: Any = "unavailable"
        eq_risk: Any = "unavailable"

        if isinstance(earthquake_data, dict):
            count_24h = _safe_int(earthquake_data.get("count_24h"), 0)
            count_7d = _safe_int(earthquake_data.get("count_7d"), 0)
            max_mag = _optional_float(earthquake_data.get("max_mag_7d"), 1)
            nearest_dist = _optional_float(earthquake_data.get("nearest_distance_km"), 1)
            nearest_mag = _optional_float(earthquake_data.get("nearest_magnitude"), 1)
            latest_time = str(earthquake_data.get("latest_time") or "unknown")
            latest_place = str(earthquake_data.get("latest_place") or "unknown")
            tsunami_24h = _safe_int(earthquake_data.get("tsunami_events_24h"), 0)
            event_url = str(earthquake_data.get("nearest_event_url") or "unavailable")

            score = min(count_7d * 3, 30)
            if max_mag is not None:
                max_mag_7d = max_mag
                if max_mag >= 7.0:
                    score += 45
                elif max_mag >= 6.0:
                    score += 35
                elif max_mag >= 5.0:
                    score += 25
                elif max_mag >= 4.0:
                    score += 15
                elif max_mag >= 3.0:
                    score += 8

            if nearest_dist is not None:
                nearest_distance_km = nearest_dist
                nearest_magnitude = nearest_mag if nearest_mag is not None else "unavailable"
                if nearest_dist <= 100:
                    score += 30
                elif nearest_dist <= 300:
                    score += 20
                elif nearest_dist <= 700:
                    score += 10

            score += min(tsunami_24h * 12, 24)
            eq_index = max(0, min(100, score))
            eq_risk = _risk_from_index(eq_index)

        return [
            {
                "entity_id": "sensor.earthquake_risk",
                "name": "Earthquake risk",
                "value": eq_risk,
                "source": source,
                "icon": "mdi:pulse",
            },
            {
                "entity_id": "sensor.earthquake_index",
                "name": "Earthquake index",
                "value": eq_index,
                "unit": "/100",
                "source": source,
                "icon": "mdi:chart-line",
            },
            {
                "entity_id": "sensor.earthquake_events_24h",
                "name": "Earthquakes 24h",
                "value": count_24h,
                "source": source,
                "icon": "mdi:clock-alert-outline",
            },
            {
                "entity_id": "sensor.earthquake_events_7d",
                "name": "Earthquakes 7d",
                "value": count_7d,
                "source": source,
                "icon": "mdi:calendar-week",
            },
            {
                "entity_id": "sensor.earthquake_max_magnitude_7d",
                "name": "Earthquake max magnitude 7d",
                "value": max_mag_7d,
                "unit": "M",
                "source": source,
                "icon": "mdi:magnitude",
            },
            {
                "entity_id": "sensor.earthquake_nearest_distance_km",
                "name": "Nearest earthquake distance",
                "value": nearest_distance_km,
                "unit": "km",
                "source": source,
                "icon": "mdi:map-marker-distance",
            },
            {
                "entity_id": "sensor.earthquake_nearest_magnitude",
                "name": "Nearest earthquake magnitude",
                "value": nearest_magnitude,
                "unit": "M",
                "source": source,
                "icon": "mdi:chart-bubble",
            },
            {
                "entity_id": "sensor.earthquake_latest_time",
                "name": "Latest earthquake time",
                "value": latest_time,
                "source": source,
                "icon": "mdi:clock-outline",
            },
            {
                "entity_id": "sensor.earthquake_latest_place",
                "name": "Latest earthquake place",
                "value": latest_place,
                "source": source,
                "icon": "mdi:map-marker",
            },
            {
                "entity_id": "sensor.earthquake_tsunami_events_24h",
                "name": "Tsunami-flagged earthquakes 24h",
                "value": tsunami_24h,
                "source": source,
                "icon": "mdi:waves-arrow-up",
            },
            {
                "entity_id": "sensor.earthquake_event_url",
                "name": "Nearest earthquake event URL",
                "value": event_url,
                "source": source,
                "icon": "mdi:link-variant",
            },
            {
                "entity_id": "sensor.earthquake_source",
                "name": "Earthquake source",
                "value": source,
                "source": source,
                "icon": "mdi:database-search-outline",
            },
        ]

    def _build_wildfire_metrics(
        self,
        *,
        latitude: float,
        longitude: float,
        gdacs_events: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        """Build wildfire metrics from GDACS current wildfire events."""
        source = "gdacs_rss" if isinstance(gdacs_events, list) else "unavailable"

        wildfire_risk: Any = "unavailable"
        wildfire_index: Any = "unavailable"
        active_events: Any = "unavailable"
        high_alert_events: Any = "unavailable"
        max_alert_level: Any = "unavailable"
        nearest_distance_km: Any = "unavailable"
        nearest_country: Any = "unavailable"
        nearest_title: Any = "unavailable"
        nearest_link: Any = "unavailable"
        nearest_icon_url: Any = "unavailable"

        if isinstance(gdacs_events, list):
            wildfire_events = [
                event
                for event in gdacs_events
                if event.get("is_current") is True and event.get("event_type") == "WF"
            ]
            active_events = len(wildfire_events)
            high_alert_events = sum(
                1
                for event in wildfire_events
                if str(event.get("alert_level") or "").lower() in {"orange", "red"}
            )

            if wildfire_events:
                max_alert_rank = max(
                    _alert_level_rank(str(event.get("alert_level"))) for event in wildfire_events
                )
                if max_alert_rank >= 4:
                    max_alert_level = "red"
                elif max_alert_rank >= 3:
                    max_alert_level = "orange"
                elif max_alert_rank >= 2:
                    max_alert_level = "green"
                else:
                    max_alert_level = "unknown"

                nearest_event: dict[str, Any] | None = None
                nearest_dist = 100_000.0
                for event in wildfire_events:
                    ev_lat = _optional_float(event.get("latitude"))
                    ev_lon = _optional_float(event.get("longitude"))
                    if ev_lat is None or ev_lon is None:
                        continue
                    dist = _haversine_km(latitude, longitude, ev_lat, ev_lon)
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_event = event

                score = min(active_events * 2, 26) + min(high_alert_events * 12, 32)
                score += _alert_level_rank(str(max_alert_level)) * 8

                if nearest_event is not None:
                    nearest_distance_km = round(nearest_dist, 1)
                    nearest_country = str(nearest_event.get("country") or "unknown")
                    nearest_title = str(nearest_event.get("title") or "unknown")
                    nearest_link = str(nearest_event.get("link") or "unavailable")
                    nearest_icon_url = str(nearest_event.get("icon_url") or "unavailable")
                    if nearest_dist <= 500:
                        score += 30
                    elif nearest_dist <= 1500:
                        score += 20
                    elif nearest_dist <= 3500:
                        score += 10

                wildfire_index = max(0, min(100, score))
                wildfire_risk = _risk_from_index(wildfire_index)
            else:
                wildfire_index = 0
                wildfire_risk = "very_low"
                max_alert_level = "none"

        return [
            {
                "entity_id": "sensor.wildfire_risk",
                "name": "Wildfire risk",
                "value": wildfire_risk,
                "source": source,
                "icon": "mdi:fire-alert",
            },
            {
                "entity_id": "sensor.wildfire_index",
                "name": "Wildfire index",
                "value": wildfire_index,
                "unit": "/100",
                "source": source,
                "icon": "mdi:chart-line",
            },
            {
                "entity_id": "sensor.wildfire_active_events_global",
                "name": "Wildfire active events (global)",
                "value": active_events,
                "source": source,
                "icon": "mdi:fire",
            },
            {
                "entity_id": "sensor.wildfire_high_alert_events_global",
                "name": "Wildfire high-alert events (global)",
                "value": high_alert_events,
                "source": source,
                "icon": "mdi:alert-octagon",
            },
            {
                "entity_id": "sensor.wildfire_max_alert_level",
                "name": "Wildfire max alert level",
                "value": max_alert_level,
                "source": source,
                "icon": "mdi:alarm-light-outline",
            },
            {
                "entity_id": "sensor.wildfire_nearest_distance_km",
                "name": "Nearest wildfire distance",
                "value": nearest_distance_km,
                "unit": "km",
                "source": source,
                "icon": "mdi:map-marker-distance",
            },
            {
                "entity_id": "sensor.wildfire_nearest_country",
                "name": "Nearest wildfire country",
                "value": nearest_country,
                "source": source,
                "icon": "mdi:flag-outline",
            },
            {
                "entity_id": "sensor.wildfire_nearest_title",
                "name": "Nearest wildfire title",
                "value": nearest_title,
                "source": source,
                "icon": "mdi:text-box-outline",
            },
            {
                "entity_id": "sensor.wildfire_nearest_link",
                "name": "Nearest wildfire report URL",
                "value": nearest_link,
                "source": source,
                "icon": "mdi:link-variant",
            },
            {
                "entity_id": "sensor.wildfire_icon_url",
                "name": "Nearest wildfire icon URL",
                "value": nearest_icon_url,
                "source": source,
                "icon": "mdi:image-outline",
            },
            {
                "entity_id": "sensor.wildfire_source",
                "name": "Wildfire source",
                "value": source,
                "source": source,
                "icon": "mdi:database-search-outline",
            },
        ]

    def _build_hazard_metrics(
        self,
        *,
        latitude: float,
        longitude: float,
        gdacs_events: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        """Build multi-hazard summary metrics from GDACS current events."""
        source = "gdacs_rss" if isinstance(gdacs_events, list) else "unavailable"

        active_total: Any = "unavailable"
        high_alert_total: Any = "unavailable"
        top_event_type: Any = "unavailable"
        top_event_alert: Any = "unavailable"
        top_event_title: Any = "unavailable"
        top_event_country: Any = "unavailable"
        top_event_distance_km: Any = "unavailable"
        top_event_icon_url: Any = "unavailable"
        last_update: Any = "unavailable"

        if isinstance(gdacs_events, list):
            current_events = [event for event in gdacs_events if event.get("is_current") is True]
            active_total = len(current_events)
            high_alert_total = sum(
                1
                for event in current_events
                if str(event.get("alert_level") or "").lower() in {"orange", "red"}
            )

            if current_events:
                latest_ts = max(
                    _safe_int(event.get("published_ts"), 0) for event in current_events
                )
                if latest_ts > 0:
                    last_update = datetime.fromtimestamp(latest_ts, tz=UTC).isoformat()
                else:
                    last_update = "unknown"

                top_event: dict[str, Any] | None = None
                top_key = (-1, -100_000.0, -1)
                for event in current_events:
                    event_alert = str(event.get("alert_level") or "unknown")
                    rank = _alert_level_rank(event_alert)
                    ev_lat = _optional_float(event.get("latitude"))
                    ev_lon = _optional_float(event.get("longitude"))
                    dist = None
                    if ev_lat is not None and ev_lon is not None:
                        dist = _haversine_km(latitude, longitude, ev_lat, ev_lon)
                    dist_key = -(dist if dist is not None else 100_000.0)
                    pub_ts = _safe_int(event.get("published_ts"), 0)
                    key = (rank, dist_key, pub_ts)
                    if key > top_key:
                        top_key = key
                        top_event = event

                if top_event is not None:
                    top_event_type = str(top_event.get("event_type") or "unknown")
                    top_event_alert = str(top_event.get("alert_level") or "unknown")
                    top_event_title = str(top_event.get("title") or "unknown")
                    top_event_country = str(top_event.get("country") or "unknown")
                    top_event_icon_url = str(top_event.get("icon_url") or "unavailable")
                    ev_lat = _optional_float(top_event.get("latitude"))
                    ev_lon = _optional_float(top_event.get("longitude"))
                    if ev_lat is not None and ev_lon is not None:
                        top_event_distance_km = round(
                            _haversine_km(latitude, longitude, ev_lat, ev_lon),
                            1,
                        )
            else:
                active_total = 0
                high_alert_total = 0
                top_event_type = "none"
                top_event_alert = "none"
                top_event_title = "none"
                top_event_country = "none"
                top_event_distance_km = "unavailable"
                top_event_icon_url = "unavailable"
                last_update = "unknown"

        return [
            {
                "entity_id": "sensor.hazard_active_events_global",
                "name": "Hazard active events (global)",
                "value": active_total,
                "source": source,
                "icon": "mdi:alert-circle-outline",
            },
            {
                "entity_id": "sensor.hazard_high_alert_events_global",
                "name": "Hazard high-alert events (global)",
                "value": high_alert_total,
                "source": source,
                "icon": "mdi:alert-octagon-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_type",
                "name": "Top hazard event type",
                "value": top_event_type,
                "source": source,
                "icon": "mdi:shape-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_alert",
                "name": "Top hazard event alert",
                "value": top_event_alert,
                "source": source,
                "icon": "mdi:alarm-light-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_title",
                "name": "Top hazard event title",
                "value": top_event_title,
                "source": source,
                "icon": "mdi:text-box-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_country",
                "name": "Top hazard event country",
                "value": top_event_country,
                "source": source,
                "icon": "mdi:flag-outline",
            },
            {
                "entity_id": "sensor.hazard_top_event_distance_km",
                "name": "Top hazard event distance",
                "value": top_event_distance_km,
                "unit": "km",
                "source": source,
                "icon": "mdi:map-marker-distance",
            },
            {
                "entity_id": "sensor.hazard_top_event_icon_url",
                "name": "Top hazard event icon URL",
                "value": top_event_icon_url,
                "source": source,
                "icon": "mdi:image-outline",
            },
            {
                "entity_id": "sensor.hazard_last_update",
                "name": "Hazard feed last update",
                "value": last_update,
                "source": source,
                "icon": "mdi:clock-outline",
            },
            {
                "entity_id": "sensor.hazard_source",
                "name": "Hazard source",
                "value": source,
                "source": source,
                "icon": "mdi:database-search-outline",
            },
        ]

