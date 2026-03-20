"""Persona, exposure and planner metric builders for Beregynya AURA."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util

from ..const import (
    CONF_PERSONAS,
    CONF_TRACKING_ENTITIES,
    DEFAULT_PLANNER_MODE,
)
from .constants import *  # noqa: F403
from .options import _clamp_float, _normalize_planner_mode, _normalize_tracking_id
from .shared import *  # noqa: F403


class AuraPersonaMetricsMixin:
    def _build_exposure_and_persona_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        personas: Any,
    ) -> list[dict[str, Any]]:
        """Build rip-current/heat metrics and persona-specific exposure sensors."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}

        wave_height = _optional_float(values.get("sensor.wave_height"))
        wave_period = _optional_float(values.get("sensor.wave_period"))
        wind_speed_ms = _optional_float(values.get("sensor.wind_speed"))
        wind_speed = _ms_to_kmh(wind_speed_ms)
        rain_prob = _optional_float(values.get("sensor.precipitation_probability"))
        if rain_prob is None:
            rain_prob = _optional_float(values.get("sensor.rain_next_6h"))
        apparent_temperature = _optional_float(values.get("sensor.apparent_temperature"))
        humidity = _optional_float(values.get("sensor.humidity"))
        uv_index = _optional_float(values.get("sensor.uv_index"))

        rip_index: int | None = None
        rip_risk = "unavailable"
        if (
            wave_height is not None
            and wave_period is not None
            and wind_speed is not None
            and rain_prob is not None
        ):
            rip_index = _rip_current_index(
                wave_height_m=wave_height,
                wave_period_s=wave_period,
                wind_speed_kmh=wind_speed,
                rain_probability_pct=rain_prob,
            )
            rip_risk = _risk_from_index(rip_index)

        heat_index_c: float | None = None
        wet_bulb_c: float | None = None
        heat_stress_index: int | None = None
        heat_stress_risk = "unavailable"
        if apparent_temperature is not None and humidity is not None:
            heat_index_c = _heat_index_c(apparent_temperature, humidity)
            wet_bulb_c = _wet_bulb_c(apparent_temperature, humidity)
            score = 0.0
            if heat_index_c >= 54:
                score = 100
            elif heat_index_c >= 41:
                score = 82 + (heat_index_c - 41) * 1.4
            elif heat_index_c >= 32:
                score = 58 + (heat_index_c - 32) * 2.1
            elif heat_index_c >= 27:
                score = 35 + (heat_index_c - 27) * 4.6
            else:
                score = max(0.0, (heat_index_c - 18) * 2.6)
            heat_stress_index = max(0, min(100, int(round(score))))
            heat_stress_risk = _risk_from_index(heat_stress_index)

        result: list[dict[str, Any]] = [
            {
                "entity_id": "sensor.rip_current_risk",
                "name": "Rip current risk",
                "value": rip_risk,
                "source": "internal_model",
                "icon": "mdi:waves-arrow-right",
            },
            {
                "entity_id": "sensor.rip_current_index",
                "name": "Rip current index",
                "value": rip_index if rip_index is not None else "unavailable",
                "unit": "/100",
                "source": "internal_model",
                "icon": "mdi:chart-line",
            },
            {
                "entity_id": "sensor.heat_stress_risk",
                "name": "Heat stress risk",
                "value": heat_stress_risk,
                "source": "internal_model",
                "icon": "mdi:thermometer-alert",
            },
            {
                "entity_id": "sensor.heat_stress_index",
                "name": "Heat stress index",
                "value": heat_stress_index if heat_stress_index is not None else "unavailable",
                "unit": "/100",
                "source": "internal_model",
                "icon": "mdi:chart-line",
            },
            {
                "entity_id": "sensor.heat_index_c",
                "name": "Heat index",
                "value": heat_index_c if heat_index_c is not None else "unavailable",
                "unit": "degC",
                "source": "internal_model",
                "icon": "mdi:thermometer-high",
            },
            {
                "entity_id": "sensor.wet_bulb_c",
                "name": "Wet bulb temperature",
                "value": wet_bulb_c if wet_bulb_c is not None else "unavailable",
                "unit": "degC",
                "source": "internal_model",
                "icon": "mdi:thermometer-water",
            },
        ]

        if not isinstance(personas, list):
            return result

        for persona in personas:
            if not isinstance(persona, dict):
                continue
            if persona.get("enabled") is False:
                continue

            persona_id = str(persona.get("id") or "").strip()
            if not persona_id:
                continue
            persona_name = str(persona.get("name") or persona_id).strip() or persona_id
            skin_type = _safe_int(persona.get("skin_type"), 3)
            if skin_type < 1:
                skin_type = 1
            if skin_type > 6:
                skin_type = 6
            spf = _clamp_float(persona.get("spf", 1.0), 1.0, 1.0, 100.0)
            shade_factor = _clamp_float(persona.get("shade_factor", 1.0), 1.0, 0.2, 5.0)
            uv_sensitivity = _clamp_float(
                persona.get("uv_sensitivity", 1.0), 1.0, 0.5, 2.5
            )
            heat_sensitivity = _clamp_float(
                persona.get("heat_sensitivity", 1.0), 1.0, 0.6, 1.8
            )
            person_entity_id = persona.get("person_entity_id")
            if not isinstance(person_entity_id, str) or not person_entity_id.strip():
                person_entity_id = None
            else:
                person_entity_id = person_entity_id.strip()

            presence = "unknown"
            if person_entity_id is not None:
                state = self.hass.states.get(person_entity_id)
                if state is None:
                    presence = "unavailable"
                else:
                    presence = str(state.state or "unknown")

            burn_minutes = (
                _sunburn_minutes(
                    uv_index=uv_index,
                    skin_type=skin_type,
                    spf=spf,
                    shade_factor=shade_factor,
                    uv_sensitivity=uv_sensitivity,
                )
                if uv_index is not None
                else None
            )
            burn_risk = _sunburn_risk(burn_minutes)

            persona_heat_index: int | None = None
            persona_heat_risk = "unavailable"
            if heat_stress_index is not None:
                persona_heat_index = max(
                    0, min(100, int(round(heat_stress_index * heat_sensitivity)))
                )
                persona_heat_risk = _risk_from_index(persona_heat_index)

            persona_prefix = f"sensor.aura_{persona_id}"
            result.extend(
                [
                    {
                        "entity_id": f"{persona_prefix}_sunburn_time_min",
                        "name": f"{persona_name} sunburn time",
                        "value": burn_minutes if burn_minutes is not None else "unavailable",
                        "unit": "min",
                        "source": "persona_profile",
                        "icon": "mdi:white-balance-sunny",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_sunburn_risk",
                        "name": f"{persona_name} sunburn risk",
                        "value": burn_risk,
                        "source": "persona_profile",
                        "icon": "mdi:sun-thermometer-outline",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_heat_stress_index",
                        "name": f"{persona_name} heat stress index",
                        "value": (
                            persona_heat_index
                            if persona_heat_index is not None
                            else "unavailable"
                        ),
                        "unit": "/100",
                        "source": "persona_profile",
                        "icon": "mdi:thermometer-alert",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_heat_stress_risk",
                        "name": f"{persona_name} heat stress risk",
                        "value": persona_heat_risk,
                        "source": "persona_profile",
                        "icon": "mdi:thermometer-alert",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_presence",
                        "name": f"{persona_name} presence",
                        "value": presence,
                        "source": "ha_person"
                        if person_entity_id is not None
                        else "persona_profile",
                        "icon": "mdi:account",
                        "source_entity": person_entity_id,
                    },
                    {
                        "entity_id": f"{persona_prefix}_profile",
                        "name": f"{persona_name} profile",
                        "value": (
                            f"skin_type={skin_type}, spf={spf:g}, shade={shade_factor:g}, "
                            f"uv_sens={uv_sensitivity:g}, heat_sens={heat_sensitivity:g}"
                        ),
                        "source": "persona_profile",
                        "icon": "mdi:account-details-outline",
                        "source_entity": person_entity_id,
                    },
                ]
            )

        return result

    def _build_climate_extra_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        weather_data: dict[str, Any] | None,
        marine_data: dict[str, Any] | None,
        air_data: dict[str, Any] | None,
        latitude: float,
        longitude: float,
        personas: Any,
        tracking_entities: Any,
        gdacs_events: list[dict[str, Any]] | None,
        cap_data: dict[str, Any] | None,
        algae_tile_data: dict[str, Any] | None,
        smoke_tile_data: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Build extra climate/hazard metrics: UV/astro, WBGT, thunder, tides, algae, smoke, CAP, bites."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        weather_hourly = weather_data.get("hourly", {}) if isinstance(weather_data, dict) else {}
        marine_hourly = marine_data.get("hourly", {}) if isinstance(marine_data, dict) else {}
        weather_daily = weather_data.get("daily", {}) if isinstance(weather_data, dict) else {}

        weather_idx = self._select_hour_index(weather_hourly)
        marine_idx = self._select_hour_index(marine_hourly)

        def hourly_float(
            hourly: dict[str, Any], key: str, idx: int, digits: int | None = None
        ) -> float | None:
            value = _hourly_value(hourly, key, idx, None)
            return _optional_float(value, digits)

        def hourly_int(hourly: dict[str, Any], key: str, idx: int) -> int | None:
            value = _hourly_value(hourly, key, idx, None)
            return _optional_int(value)

        def metric(
            entity_id: str,
            name: str,
            value: Any,
            unit: str | None = None,
            icon: str | None = None,
            source: str = "internal_model",
            source_entity: str | None = None,
            extras: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            item: dict[str, Any] = {
                "entity_id": entity_id,
                "name": name,
                "value": "unavailable" if value is None else value,
                "source": source,
            }
            if unit is not None:
                item["unit"] = unit
            if icon is not None:
                item["icon"] = icon
            if source_entity is not None:
                item["source_entity"] = source_entity
            if isinstance(extras, dict):
                item.update(extras)
            return item

        uv_now = hourly_float(weather_hourly, "uv_index", weather_idx, 1)
        temperature_now = hourly_float(weather_hourly, "temperature_2m", weather_idx, 1)
        apparent_now = hourly_float(weather_hourly, "apparent_temperature", weather_idx, 1)
        humidity_now = hourly_float(weather_hourly, "relative_humidity_2m", weather_idx, 1)
        cloud_cover_now = hourly_float(weather_hourly, "cloud_cover", weather_idx, 1)
        cape_now = hourly_float(weather_hourly, "cape", weather_idx, 1)
        precip_now = hourly_float(weather_hourly, "precipitation", weather_idx, 1)
        wind_now = hourly_float(weather_hourly, "wind_speed_10m", weather_idx, 1)
        shortwave_now = hourly_float(weather_hourly, "shortwave_radiation", weather_idx, 1)
        weather_code_now = hourly_int(weather_hourly, "weather_code", weather_idx)
        sea_temp_now = hourly_float(marine_hourly, "sea_surface_temperature", marine_idx, 1)
        if sea_temp_now is None:
            sea_temp_now = _optional_float(
                values.get("sensor.beach_water_temperature_official"),
                1,
            )
        wave_height_now = hourly_float(marine_hourly, "wave_height", marine_idx, 2)
        if wave_height_now is None:
            wave_height_now = _optional_float(values.get("sensor.wave_height"), 2)

        tz = dt_util.get_time_zone(self.hass.config.time_zone) or UTC
        weather_time = weather_hourly.get("time")

        def astro_row(offset: int) -> tuple[float | None, float | None]:
            idx = weather_idx + offset
            raw_time: Any = None
            if isinstance(weather_time, list) and 0 <= idx < len(weather_time):
                raw_time = weather_time[idx]
            local_time = _parse_hourly_time(raw_time, tz)
            if local_time is None:
                return None, None
            cloud = hourly_float(weather_hourly, "cloud_cover", idx, 1)
            solar_elevation = _solar_elevation_degrees(
                local_time,
                latitude=latitude,
                longitude=longitude,
            )
            astro_uv = _astro_uv_from_solar(
                solar_elevation_deg=solar_elevation,
                cloud_cover_pct=cloud,
            )
            return astro_uv, round(solar_elevation, 1)

        astro_uv_now, astro_solar_now = astro_row(0)
        astro_future: list[float] = []
        for offset in (1, 2, 3):
            future_uv, _future_solar = astro_row(offset)
            if future_uv is not None:
                astro_future.append(future_uv)
        astro_uv_3h_max = max(astro_future) if astro_future else None
        astro_risk_3h = "unavailable"
        if astro_uv_3h_max is not None:
            astro_risk_3h = _risk_from_index(
                max(0, min(100, int(round((astro_uv_3h_max / 11.0) * 100.0))))
            )
        astro_now_vs_3h = "unavailable"
        if astro_uv_now is not None and astro_uv_3h_max is not None:
            if astro_uv_3h_max >= astro_uv_now + 1.5:
                astro_now_vs_3h = "rising"
            elif astro_uv_now >= astro_uv_3h_max + 1.5:
                astro_now_vs_3h = "falling"
            else:
                astro_now_vs_3h = "stable"

        uv_effective_now = astro_uv_now if astro_uv_now is not None else uv_now

        uv_sed_1h: float | None = None
        if uv_effective_now is not None:
            uv_sed_1h = round(max(0.0, uv_effective_now) * 0.9, 2)
        uv_status = "unavailable"
        if uv_effective_now is not None:
            if uv_effective_now >= 11:
                uv_status = "extreme"
            elif uv_effective_now >= 8:
                uv_status = "very_high"
            elif uv_effective_now >= 6:
                uv_status = "high"
            elif uv_effective_now >= 3:
                uv_status = "moderate"
            else:
                uv_status = "low"

        trackers: list[dict[str, Any]] = []
        tracker_ids: set[str] = set()
        tracker_entities_set: set[str] = set()

        def add_tracker(
            *,
            tracker_id: str,
            name: str,
            entity_id: str | None,
            exposure_factor: float,
        ) -> None:
            if not isinstance(entity_id, str) or not entity_id.strip():
                return
            normalized_entity = entity_id.strip()
            if normalized_entity in tracker_entities_set:
                return
            normalized_id = tracker_id.strip().lower()
            if not normalized_id:
                normalized_id = _normalize_tracking_id(name, len(trackers))
            if normalized_id in tracker_ids:
                normalized_id = f"{normalized_id}_{len(trackers) + 1}"
            tracker_entities_set.add(normalized_entity)
            tracker_ids.add(normalized_id)
            trackers.append(
                {
                    "id": normalized_id,
                    "name": name,
                    "entity_id": normalized_entity,
                    "uv_exposure_factor": max(0.0, min(2.5, exposure_factor)),
                }
            )

        if isinstance(personas, list):
            for idx, persona in enumerate(personas):
                if not isinstance(persona, dict):
                    continue
                if persona.get("enabled") is False:
                    continue
                persona_id = _normalize_tracking_id(persona.get("id"), idx)
                persona_name = str(persona.get("name") or persona_id).strip() or persona_id
                tracker_entity_id = persona.get("tracker_entity_id")
                person_entity_id = persona.get("person_entity_id")
                if not isinstance(tracker_entity_id, str) or not tracker_entity_id.strip():
                    tracker_entity_id = (
                        person_entity_id if isinstance(person_entity_id, str) else None
                    )
                add_tracker(
                    tracker_id=persona_id,
                    name=persona_name,
                    entity_id=tracker_entity_id,
                    exposure_factor=_clamp_float(
                        persona.get("uv_exposure_factor", 1.0), 1.0, 0.0, 2.5
                    ),
                )

        if isinstance(tracking_entities, list):
            for idx, tracker in enumerate(tracking_entities):
                if not isinstance(tracker, dict):
                    continue
                add_tracker(
                    tracker_id=_normalize_tracking_id(
                        tracker.get("id", tracker.get("entity_id")),
                        idx,
                    ),
                    name=str(tracker.get("name") or tracker.get("id") or f"tracker_{idx + 1}"),
                    entity_id=tracker.get("entity_id")
                    if isinstance(tracker.get("entity_id"), str)
                    else None,
                    exposure_factor=_clamp_float(
                        tracker.get("uv_exposure_factor", 1.0), 1.0, 0.0, 2.5
                    ),
                )

        local_day = dt_util.now().strftime("%Y-%m-%d")
        if self._uv_sed_day != local_day:
            self._uv_sed_by_tracker = {}
            self._uv_sed_day = local_day
            self._uv_sed_last_update = None

        now_utc = datetime.now(tz=UTC)
        delta_hours = 0.0
        if self._uv_sed_last_update is not None:
            delta_hours = max(
                0.0,
                min(
                    1.5,
                    (now_utc - self._uv_sed_last_update).total_seconds() / 3600.0,
                ),
            )
        self._uv_sed_last_update = now_utc

        def outdoor_weight(state_value: str) -> float:
            value = state_value.strip().lower()
            if value in {"", "unknown", "unavailable", "none"}:
                return 0.0
            if value == "home":
                return 0.0
            if value in {"not_home", "away"}:
                return 0.6
            if any(
                token in value
                for token in (
                    "walking",
                    "on_foot",
                    "walk",
                    "foot",
                    "beach",
                    "outdoor",
                    "park",
                    "running",
                    "cycling",
                    "sport",
                    "пеш",
                    "пляж",
                    "улиц",
                    "прогул",
                )
            ):
                return 1.0
            return 0.5

        tracker_metrics: list[dict[str, Any]] = []
        sed_total_today = 0.0
        for tracker in trackers:
            tracker_id = str(tracker.get("id") or "").strip()
            if not tracker_id:
                continue
            entity_id = str(tracker.get("entity_id") or "").strip()
            if not entity_id:
                continue
            tracker_name = str(tracker.get("name") or tracker_id).strip() or tracker_id
            exposure_factor = _clamp_float(
                tracker.get("uv_exposure_factor", 1.0), 1.0, 0.0, 2.5
            )

            state = self.hass.states.get(entity_id)
            state_value = str(state.state or "unknown") if state is not None else "unavailable"
            exposure_state = "indoors"
            weight = outdoor_weight(state_value)
            if state_value in {"unavailable", "unknown"}:
                exposure_state = "unknown"
            elif weight >= 0.9:
                exposure_state = "outdoor"
            elif weight > 0.0:
                exposure_state = "mixed"

            previous_sed = _safe_float(self._uv_sed_by_tracker.get(tracker_id, 0.0), 0.0)
            if uv_sed_1h is not None and delta_hours > 0:
                increment = uv_sed_1h * delta_hours * weight * exposure_factor
                previous_sed += increment
            current_sed = round(max(0.0, min(40.0, previous_sed)), 2)
            self._uv_sed_by_tracker[tracker_id] = current_sed
            sed_total_today += current_sed

            tracker_prefix = f"sensor.aura_tracker_{tracker_id}"
            tracker_metrics.extend(
                [
                    metric(
                        f"{tracker_prefix}_uv_sed_today",
                        f"{tracker_name} UV SED today",
                        current_sed,
                        unit="SED",
                        icon="mdi:white-balance-sunny",
                        source="ha_tracking",
                        source_entity=entity_id,
                        extras={"state": state_value},
                    ),
                    metric(
                        f"{tracker_prefix}_uv_exposure_state",
                        f"{tracker_name} UV exposure state",
                        exposure_state,
                        icon="mdi:walk",
                        source="ha_tracking",
                        source_entity=entity_id,
                    ),
                ]
            )

        sed_total_value: float | None = None
        if trackers:
            sed_total_value = round(sed_total_today, 2)

        wbgt_c: float | None = None
        dehydration_index: int | None = None
        dehydration_risk = "unavailable"
        if temperature_now is not None and humidity_now is not None:
            vapor_hpa = (humidity_now / 100.0) * 6.105 * math.exp(
                (17.27 * temperature_now) / (237.7 + temperature_now)
            )
            wbgt = 0.567 * temperature_now + 0.393 * vapor_hpa + 3.94
            if shortwave_now is not None:
                wbgt += min(4.5, max(0.0, shortwave_now - 180.0) / 140.0)
            if wind_now is not None:
                wbgt -= min(2.5, max(0.0, wind_now) / 20.0)
            wbgt_c = round(wbgt, 1)

            score = max(0.0, (wbgt_c - 20.0) * 4.6)
            if uv_effective_now is not None:
                score += max(0.0, uv_effective_now - 3.0) * 4.2
            if wind_now is not None:
                score += max(0.0, wind_now - 15.0) * 0.7
            if apparent_now is not None:
                score += max(0.0, apparent_now - 30.0) * 1.8
            dehydration_index = max(0, min(100, int(round(score))))
            dehydration_risk = _risk_from_index(dehydration_index)

        def thunder_index_for_offset(offset: int) -> int | None:
            idx = weather_idx + offset
            cape_v = hourly_float(weather_hourly, "cape", idx, 0)
            precip_v = hourly_float(weather_hourly, "precipitation", idx, 1)
            cloud_v = hourly_float(weather_hourly, "cloud_cover", idx, 1)
            humidity_v = hourly_float(weather_hourly, "relative_humidity_2m", idx, 1)
            code_v = hourly_int(weather_hourly, "weather_code", idx)
            if (
                cape_v is None
                and precip_v is None
                and cloud_v is None
                and humidity_v is None
                and code_v is None
            ):
                return None

            score = 0.0
            if code_v in {95, 96, 99}:
                score += 72.0
            elif code_v in {80, 81, 82}:
                score += 14.0

            if cape_v is not None:
                if cape_v >= 2500:
                    score += 35.0
                elif cape_v >= 1500:
                    score += 25.0
                elif cape_v >= 800:
                    score += 16.0
                elif cape_v >= 300:
                    score += 8.0

            if precip_v is not None:
                if precip_v >= 2.0:
                    score += 12.0
                elif precip_v >= 0.5:
                    score += 6.0

            if cloud_v is not None and cloud_v >= 70:
                score += 6.0
            if humidity_v is not None and humidity_v >= 75:
                score += 6.0
            return max(0, min(100, int(round(score))))

        thunder_now = thunder_index_for_offset(0)
        thunder_next = [
            value
            for value in (
                thunder_index_for_offset(1),
                thunder_index_for_offset(2),
                thunder_index_for_offset(3),
            )
            if value is not None
        ]
        thunder_future_max = max(thunder_next) if thunder_next else None
        thunder_index = thunder_now
        if thunder_index is None:
            thunder_index = thunder_future_max
        elif thunder_future_max is not None:
            thunder_index = max(thunder_index, thunder_future_max)
        thunder_risk = _risk_from_index(thunder_index) if thunder_index is not None else "unavailable"
        thunder_nowcast = "unavailable"
        if thunder_now is not None and thunder_future_max is not None:
            if thunder_future_max >= thunder_now + 12:
                thunder_nowcast = "rising"
            elif thunder_now >= thunder_future_max + 12:
                thunder_nowcast = "decreasing"
            elif thunder_future_max >= 65 or thunder_now >= 65:
                thunder_nowcast = "high"
            else:
                thunder_nowcast = "stable_low"
        elif thunder_index is not None:
            thunder_nowcast = "high" if thunder_index >= 65 else "stable_low"

        tide_level = hourly_float(marine_hourly, "sea_level_height_msl", marine_idx, 3)
        tide_plus_3h = hourly_float(marine_hourly, "sea_level_height_msl", marine_idx + 3, 3)
        tide_trend = "unavailable"
        if tide_level is not None and tide_plus_3h is not None:
            delta = tide_plus_3h - tide_level
            if delta > 0.03:
                tide_trend = "rising"
            elif delta < -0.03:
                tide_trend = "falling"
            else:
                tide_trend = "stable"

        tide_values: list[float] = []
        series = marine_hourly.get("sea_level_height_msl")
        if isinstance(series, list):
            for val in series[marine_idx : marine_idx + 24]:
                parsed = _optional_float(val)
                if parsed is not None:
                    tide_values.append(parsed)
        tide_range_24h = (
            round(max(tide_values) - min(tide_values), 3)
            if len(tide_values) >= 2
            else None
        )

        ocean_current_speed = hourly_float(
            marine_hourly, "ocean_current_velocity", marine_idx, 2
        )
        ocean_current_speed_ms = _kmh_to_ms(ocean_current_speed, 2)
        ocean_current_direction = hourly_float(
            marine_hourly, "ocean_current_direction", marine_idx, 1
        )
        current_index: int | None = None
        current_risk = "unavailable"
        if ocean_current_speed is not None:
            score = 0.0
            if ocean_current_speed >= 4.0:
                score += 82
            elif ocean_current_speed >= 3.0:
                score += 62
            elif ocean_current_speed >= 2.0:
                score += 42
            elif ocean_current_speed >= 1.2:
                score += 24
            elif ocean_current_speed >= 0.6:
                score += 12
            if wave_height_now is not None:
                if wave_height_now >= 2.0:
                    score += 18
                elif wave_height_now >= 1.2:
                    score += 10
            current_index = max(0, min(100, int(round(score))))
            current_risk = _risk_from_index(current_index)

        algae_chlorophyll: float | None = None
        algae_dataset = "unknown"
        algae_probe_distance_km: float | None = None
        algae_index: int | None = None
        algae_risk = "unavailable"
        algae_signal = "insufficient_data"
        algae_source = "unavailable"
        if isinstance(algae_tile_data, dict):
            algae_source = str(algae_tile_data.get("source") or "copernicus_oceancolour_wmts")
            algae_dataset = str(algae_tile_data.get("dataset_id") or _CMEMS_ALGAE_LAYER)
            algae_chlorophyll = _optional_float(algae_tile_data.get("value"), 3)
            algae_probe_distance_km = _optional_float(algae_tile_data.get("probe_distance_km"), 2)

        if algae_chlorophyll is not None:
            score = (math.log1p(max(0.0, algae_chlorophyll)) / math.log(11.0)) * 100.0
            algae_index = max(0, min(100, int(round(score))))
            algae_risk = _risk_from_index(algae_index)
            algae_signal = f"chl={algae_chlorophyll}mg/m3,dataset={algae_dataset}"
            if algae_probe_distance_km is not None and algae_probe_distance_km > 0:
                algae_signal += f",probe={algae_probe_distance_km}km"

        smoke_bbaod550: float | None = None
        smoke_pm25_tile: float | None = None
        smoke_fire_frp: float | None = None
        smoke_source = "unavailable"
        smoke_index: int | None = None
        smoke_risk = "unavailable"
        smoke_signal = "insufficient_data"
        if isinstance(smoke_tile_data, dict):
            smoke_source = str(smoke_tile_data.get("source") or "ecmwf_cams_wms")
            bbaod_payload = smoke_tile_data.get("bbaod550")
            pm25_payload = smoke_tile_data.get("pm2p5")
            fire_payload = smoke_tile_data.get("fire_frp")
            if isinstance(bbaod_payload, dict):
                smoke_bbaod550 = _optional_float(bbaod_payload.get("value"), 5)
            if isinstance(pm25_payload, dict):
                smoke_pm25_tile = _optional_float(pm25_payload.get("value"), 2)
            if isinstance(fire_payload, dict):
                smoke_fire_frp = _optional_float(fire_payload.get("value"), 2)

        if smoke_bbaod550 is not None or smoke_pm25_tile is not None or smoke_fire_frp is not None:
            score = 0.0
            if smoke_bbaod550 is not None:
                score += min(70.0, smoke_bbaod550 * 350.0)
            if smoke_pm25_tile is not None:
                score += min(25.0, max(0.0, smoke_pm25_tile - 5.0) * 1.25)
            if smoke_fire_frp is not None:
                score += min(20.0, smoke_fire_frp * 0.2)
            smoke_index = max(0, min(100, int(round(score))))
            smoke_risk = _risk_from_index(smoke_index)
            smoke_signal = (
                f"bbaod={smoke_bbaod550 if smoke_bbaod550 is not None else 'na'},"
                f"pm25={smoke_pm25_tile if smoke_pm25_tile is not None else 'na'},"
                f"fire={smoke_fire_frp if smoke_fire_frp is not None else 'na'}"
            )

        cap_index = _optional_int(cap_data.get("index")) if isinstance(cap_data, dict) else None
        cap_active = _optional_int(cap_data.get("active_count")) if isinstance(cap_data, dict) else None
        cap_highest = (
            str(cap_data.get("highest_severity") or "unknown")
            if isinstance(cap_data, dict)
            else "unavailable"
        )
        cap_event = (
            str(cap_data.get("top_event") or "unknown")
            if isinstance(cap_data, dict)
            else "unavailable"
        )
        cap_area = (
            str(cap_data.get("top_area") or "unknown")
            if isinstance(cap_data, dict)
            else "unavailable"
        )
        cap_expires = (
            str(cap_data.get("top_expires") or "unknown")
            if isinstance(cap_data, dict)
            else "unavailable"
        )
        cap_link = cap_data.get("top_link") if isinstance(cap_data, dict) else None
        cap_risk = _risk_from_index(cap_index) if cap_index is not None else "unavailable"
        cap_source = "meteoalarm_atom_spain" if isinstance(cap_data, dict) else "unavailable"

        mosquito_index = _optional_int(values.get("sensor.tiger_mosquito_index"))
        if mosquito_index is None:
            mosquito_index = _optional_int(values.get("sensor.mosquito_index"))
        tick_index = _optional_int(values.get("sensor.tick_index"))
        bite_index: int | None = None
        bite_risk = "unavailable"
        if mosquito_index is not None or tick_index is not None:
            score = 0.0
            if mosquito_index is not None:
                score += mosquito_index * 0.6
            if tick_index is not None:
                score += tick_index * 0.35
            if humidity_now is not None and humidity_now > 65:
                score += min(10.0, (humidity_now - 65) * 0.4)
            if temperature_now is not None and 18 <= temperature_now <= 32:
                score += 8.0
            bite_index = max(0, min(100, int(round(score))))
            bite_risk = _risk_from_index(bite_index)

        bite_outlook = "unavailable"
        daily_time = weather_daily.get("time") if isinstance(weather_daily, dict) else None
        if (
            isinstance(daily_time, list)
            and daily_time
            and mosquito_index is not None
            and tick_index is not None
        ):
            risk_rank = {"very_low": 1, "low": 2, "moderate": 3, "high": 4, "very_high": 5}
            day_scores: list[int] = []
            for idx, _day in enumerate(daily_time[:3]):
                temp_max = _safe_float(
                    _hourly_value(weather_daily, "temperature_2m_max", idx, 0.0), 0.0
                )
                temp_min = _safe_float(
                    _hourly_value(weather_daily, "temperature_2m_min", idx, 0.0), 0.0
                )
                rain_prob_max = _safe_int(
                    _hourly_value(weather_daily, "precipitation_probability_max", idx, 0), 0
                )
                wind_max = _safe_float(
                    _hourly_value(weather_daily, "wind_speed_10m_max", idx, 0.0), 0.0
                )
                mos_risk = _forecast_mosquito_risk(
                    baseline_index=mosquito_index,
                    temp_min=temp_min,
                    temp_max=temp_max,
                    rain_probability_max=rain_prob_max,
                    wind_max_kmh=wind_max,
                )
                tick_risk_est = _forecast_tick_risk(
                    baseline_index=tick_index,
                    temp_min=temp_min,
                    temp_max=temp_max,
                    rain_probability_max=rain_prob_max,
                    wind_max_kmh=wind_max,
                )
                day_score = max(risk_rank.get(mos_risk, 1), risk_rank.get(tick_risk_est, 1))
                day_scores.append(day_score)
            if day_scores:
                avg = sum(day_scores) / len(day_scores)
                if avg >= 4.5:
                    bite_outlook = "very_high"
                elif avg >= 3.5:
                    bite_outlook = "high"
                elif avg >= 2.5:
                    bite_outlook = "moderate"
                elif avg >= 1.5:
                    bite_outlook = "low"
                else:
                    bite_outlook = "very_low"

        result: list[dict[str, Any]] = [
            metric("sensor.uv_dose_sed_1h", "UV dose (1h full exposure)", uv_sed_1h, "SED"),
            metric(
                "sensor.uv_dose_sed_today_est",
                "UV dose today (tracked)",
                sed_total_value,
                "SED",
            ),
            metric("sensor.uv_dose_status", "UV dose status", uv_status),
            metric(
                "sensor.astro_solar_elevation",
                "Astro solar elevation",
                astro_solar_now,
                "deg",
                source="astro_model",
            ),
            metric(
                "sensor.astro_uv_index_now",
                "Astro UV index now",
                astro_uv_now,
                source="astro_model",
            ),
            metric(
                "sensor.astro_uv_index_3h_max",
                "Astro UV index +3h max",
                astro_uv_3h_max,
                source="astro_model",
            ),
            metric(
                "sensor.astro_uv_risk_3h",
                "Astro UV risk +3h",
                astro_risk_3h,
                source="astro_model",
            ),
            metric(
                "sensor.astro_uv_now_vs_3h",
                "Astro UV now vs +3h",
                astro_now_vs_3h,
                source="astro_model",
            ),
            metric("sensor.wbgt_c", "WBGT", wbgt_c, "degC"),
            metric(
                "sensor.dehydration_index",
                "Dehydration index",
                dehydration_index,
                "/100",
            ),
            metric("sensor.dehydration_risk", "Dehydration risk", dehydration_risk),
            metric("sensor.thunderstorm_risk", "Thunderstorm risk", thunder_risk),
            metric("sensor.thunderstorm_index", "Thunderstorm index", thunder_index, "/100"),
            metric("sensor.thunderstorm_cape", "CAPE", cape_now, "J/kg"),
            metric(
                "sensor.thunderstorm_nowcast_3h",
                "Thunderstorm nowcast +3h",
                thunder_nowcast,
            ),
            metric("sensor.tide_level_m", "Tide level (MSL)", tide_level, "m"),
            metric("sensor.tide_trend_3h", "Tide trend +3h", tide_trend),
            metric("sensor.tide_range_24h_m", "Tide range 24h", tide_range_24h, "m"),
            metric(
                "sensor.ocean_current_speed",
                "Ocean current speed",
                ocean_current_speed_ms,
                "m/s",
            ),
            metric(
                "sensor.ocean_current_direction",
                "Ocean current direction",
                ocean_current_direction,
                "deg",
            ),
            metric("sensor.current_risk", "Current risk", current_risk),
            metric("sensor.algae_bloom_risk", "Algae bloom risk", algae_risk),
            metric("sensor.algae_bloom_index", "Algae bloom index", algae_index, "/100"),
            metric("sensor.algae_bloom_signal", "Algae bloom signal", algae_signal),
            metric(
                "sensor.algae_chlorophyll_mg_m3",
                "Algae chlorophyll",
                algae_chlorophyll,
                "mg/m3",
                source=algae_source,
            ),
            metric(
                "sensor.algae_source",
                "Algae source",
                algae_source,
                source=algae_source,
                extras={
                    "dataset_id": algae_dataset,
                    "probe_distance_km": algae_probe_distance_km,
                },
            ),
            metric("sensor.smoke_transport_risk", "Smoke transport risk", smoke_risk),
            metric("sensor.smoke_transport_index", "Smoke transport index", smoke_index, "/100"),
            metric("sensor.smoke_transport_signal", "Smoke transport signal", smoke_signal),
            metric(
                "sensor.smoke_cams_bbaod550",
                "Smoke CAMS bbaod550",
                smoke_bbaod550,
                source=smoke_source,
            ),
            metric(
                "sensor.smoke_cams_pm25",
                "Smoke CAMS PM2.5",
                smoke_pm25_tile,
                "ug/m3",
                source=smoke_source,
            ),
            metric(
                "sensor.smoke_cams_fire_frp",
                "Smoke CAMS fire radiative power",
                smoke_fire_frp,
                "W/m2",
                source=smoke_source,
            ),
            metric(
                "sensor.smoke_source",
                "Smoke source",
                smoke_source,
                source=smoke_source,
                extras={
                    "bbaod550": smoke_bbaod550,
                    "pm2p5": smoke_pm25_tile,
                    "fire_frp": smoke_fire_frp,
                },
            ),
            metric("sensor.cap_alert_risk", "CAP alert risk", cap_risk, source=cap_source),
            metric(
                "sensor.cap_alert_index",
                "CAP alert index",
                cap_index,
                "/100",
                source=cap_source,
            ),
            metric(
                "sensor.cap_alerts_active",
                "CAP alerts active",
                cap_active,
                source=cap_source,
            ),
            metric(
                "sensor.cap_highest_severity",
                "CAP highest severity",
                cap_highest,
                source=cap_source,
            ),
            metric("sensor.cap_top_event", "CAP top event", cap_event, source=cap_source),
            metric("sensor.cap_top_area", "CAP top area", cap_area, source=cap_source),
            metric("sensor.cap_top_expires", "CAP top expires", cap_expires, source=cap_source),
            metric(
                "sensor.cap_source",
                "CAP source",
                cap_source,
                source=cap_source,
                extras={"cap_link": cap_link},
            ),
            metric("sensor.bite_index", "Bite index", bite_index, "/100"),
            metric("sensor.bite_risk", "Bite risk", bite_risk),
            metric("sensor.bite_outlook_3d", "Bite outlook 3d", bite_outlook),
        ]
        result.extend(tracker_metrics)
        return result

    def _build_daily_planner_metrics(
        self,
        *,
        metrics: list[dict[str, Any]],
        weather_data: dict[str, Any] | None,
        marine_data: dict[str, Any] | None,
        air_data: dict[str, Any] | None,
        latitude: float,
        longitude: float,
        personas: Any,
        daily_plan_enabled: bool,
        default_planner_mode: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Build daily planner + smart notification hints with astro-UV support."""
        values = {item.get("entity_id"): item.get("value") for item in metrics}
        planner_mode_default = _normalize_planner_mode(default_planner_mode)

        mode_profiles: dict[str, dict[str, float]] = {
            "normal": {
                "uv_limit": 6.0,
                "heat_limit": 31.0,
                "outdoor_threshold": 65.0,
                "beach_threshold": 68.0,
            },
            "child": {
                "uv_limit": 3.5,
                "heat_limit": 28.5,
                "outdoor_threshold": 72.0,
                "beach_threshold": 74.0,
            },
            "elderly": {
                "uv_limit": 5.0,
                "heat_limit": 28.0,
                "outdoor_threshold": 70.0,
                "beach_threshold": 72.0,
            },
            "sport": {
                "uv_limit": 7.0,
                "heat_limit": 33.0,
                "outdoor_threshold": 62.0,
                "beach_threshold": 66.0,
            },
            "beach_day": {
                "uv_limit": 6.5,
                "heat_limit": 32.0,
                "outdoor_threshold": 60.0,
                "beach_threshold": 64.0,
            },
        }
        comparison_hours = 3
        jellyfish_baseline = str(values.get("sensor.jellyfish_risk") or "").strip().lower()
        rip_index = _optional_int(values.get("sensor.rip_current_index"))
        base_jellyfish_penalty = {
            "very_high": 18.0,
            "high": 12.0,
            "moderate": 6.0,
            "low": 2.0,
            "very_low": 1.0,
            "off_season": 0.0,
        }.get(jellyfish_baseline, 3.0)

        weather_hourly = weather_data.get("hourly", {}) if isinstance(weather_data, dict) else {}
        marine_hourly = marine_data.get("hourly", {}) if isinstance(marine_data, dict) else {}
        air_hourly = air_data.get("hourly", {}) if isinstance(air_data, dict) else {}

        weather_times = weather_hourly.get("time")
        hourly_rows: list[dict[str, Any]] = []
        if isinstance(weather_times, list) and weather_times:
            tz = dt_util.get_time_zone(self.hass.config.time_zone) or UTC
            start_idx = self._select_hour_index(weather_hourly)
            end_idx = min(len(weather_times), start_idx + 24)
            for idx in range(start_idx, end_idx):
                raw_time = weather_times[idx]
                local_dt = _parse_hourly_time(raw_time, tz)
                if local_dt is None:
                    continue
                cloud_cover = _optional_float(
                    _hourly_value(weather_hourly, "cloud_cover", idx, None)
                )
                solar_elevation = _solar_elevation_degrees(
                    local_dt,
                    latitude=latitude,
                    longitude=longitude,
                )
                astro_uv = _astro_uv_from_solar(
                    solar_elevation_deg=solar_elevation,
                    cloud_cover_pct=cloud_cover,
                )
                hourly_rows.append(
                    {
                        "label": local_dt.strftime("%m-%d %H:00"),
                        "uv": _optional_float(_hourly_value(weather_hourly, "uv_index", idx, None)),
                        "astro_uv": astro_uv,
                        "solar_elevation": round(solar_elevation, 1),
                        "cloud_cover": cloud_cover,
                        "apparent_temp": _optional_float(
                            _hourly_value(weather_hourly, "apparent_temperature", idx, None)
                        ),
                        "rain_prob": _optional_float(
                            _hourly_value(weather_hourly, "precipitation_probability", idx, None)
                        ),
                        "wind": _optional_float(
                            _hourly_value(weather_hourly, "wind_speed_10m", idx, None)
                        ),
                        "aqi": _optional_float(
                            _hourly_value(air_hourly, "european_aqi", idx, None)
                        ),
                        "sea_temp": _optional_float(
                            _hourly_value(marine_hourly, "sea_surface_temperature", idx, None)
                        ),
                        "wave_height": _optional_float(
                            _hourly_value(marine_hourly, "wave_height", idx, None)
                        ),
                    }
                )

        personas_rows: list[dict[str, Any]] = []
        if isinstance(personas, list):
            personas_rows = [
                row
                for row in personas
                if isinstance(row, dict)
                and row.get("enabled") is not False
                and str(row.get("id") or "").strip()
            ]

        def planner_metric(
            entity_id: str,
            name: str,
            value: Any,
            *,
            icon: str | None = None,
            source_entity: str | None = None,
            extras: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            item: dict[str, Any] = {
                "entity_id": entity_id,
                "name": name,
                "value": "unavailable" if value is None else value,
                "source": "internal_planner",
            }
            if icon is not None:
                item["icon"] = icon
            if source_entity:
                item["source_entity"] = source_entity
            if isinstance(extras, dict):
                item.update(extras)
            return item

        def score_outdoor(
            row: dict[str, Any],
            *,
            mode: str,
            skin_type: int,
            uv_sensitivity: float,
            heat_sensitivity: float,
        ) -> int:
            profile = mode_profiles.get(mode, mode_profiles["normal"])
            score = 100.0

            uv = _optional_float(row.get("astro_uv"))
            if uv is None:
                uv = _optional_float(row.get("uv"))
            if uv is None:
                score -= 8.0
            else:
                uv_limit = profile["uv_limit"] + (skin_type - 3) * 0.35
                score -= max(0.0, uv - uv_limit) * 14.0 * uv_sensitivity

            apparent_temp = _optional_float(row.get("apparent_temp"))
            if apparent_temp is None:
                score -= 5.0
            else:
                score -= max(0.0, apparent_temp - profile["heat_limit"]) * 4.2 * heat_sensitivity

            rain_prob = _optional_float(row.get("rain_prob"))
            if rain_prob is not None:
                score -= max(0.0, rain_prob - 10.0) * 0.55

            wind = _optional_float(row.get("wind"))
            if wind is not None and wind > 15.0:
                score -= (wind - 15.0) * 1.1

            aqi = _optional_float(row.get("aqi"))
            if aqi is not None and aqi > 35.0:
                score -= (aqi - 35.0) * 0.45

            return max(0, min(100, int(round(score))))

        def score_beach(
            row: dict[str, Any],
            *,
            mode: str,
            skin_type: int,
            uv_sensitivity: float,
            heat_sensitivity: float,
        ) -> int:
            score = float(
                score_outdoor(
                    row,
                    mode=mode,
                    skin_type=skin_type,
                    uv_sensitivity=uv_sensitivity,
                    heat_sensitivity=heat_sensitivity,
                )
            )

            sea_temp = _optional_float(row.get("sea_temp"))
            if sea_temp is None:
                score -= 12.0
            elif sea_temp < 19.0:
                score -= 35.0
            elif sea_temp < 21.0:
                score -= 16.0
            elif sea_temp >= 24.0:
                score += 5.0

            wave_height = _optional_float(row.get("wave_height"))
            if wave_height is None:
                score -= 8.0
            elif wave_height > 2.2:
                score -= 36.0
            elif wave_height > 1.5:
                score -= 22.0
            elif wave_height > 1.1:
                score -= 12.0

            if rip_index is not None:
                score -= rip_index * 0.12
            score -= base_jellyfish_penalty

            return max(0, min(100, int(round(score))))

        def trend_label(now_score: int | None, future_score: int | None) -> str:
            if now_score is None or future_score is None:
                return "unavailable"
            delta = future_score - now_score
            if delta >= 8:
                return "better_in_3h"
            if delta <= -8:
                return "better_now"
            return "stable"

        def best_hours(
            rows: list[dict[str, Any]],
            scores: list[int],
            threshold: float,
        ) -> str:
            accepted = [
                rows[idx]["label"]
                for idx, score in enumerate(scores)
                if idx < len(rows) and score >= threshold
            ]
            if not accepted:
                return "none"
            if len(accepted) > 8:
                return ", ".join(accepted[:8]) + ", ..."
            return ", ".join(accepted)

        def pack_list_for_mode(
            *,
            mode: str,
            sea_temp_now: float | None,
            rain_now: float | None,
            uv_now: float | None,
            trend_outdoor: str,
        ) -> str:
            items = [
                "water",
                "towel",
                "sunscreen SPF50+",
                "hat",
                "sunglasses",
            ]
            if mode == "child":
                items.extend(["UV shirt", "spare clothes", "kids snack"])
            elif mode == "elderly":
                items.extend(["electrolytes", "light chair", "medication kit"])
            elif mode == "sport":
                items.extend(["electrolytes", "sports bottle", "energy snack"])
            elif mode == "beach_day":
                items.extend(["umbrella", "beach mat", "snorkel mask"])

            if sea_temp_now is not None and sea_temp_now < 21.0:
                items.append("light hoodie")
            if rain_now is not None and rain_now >= 35.0:
                items.append("light rain jacket")
            if uv_now is not None and uv_now >= 6.0:
                items.append("after-sun gel")
            if jellyfish_baseline in {"high", "very_high"}:
                items.append("anti-sting kit")
            if trend_outdoor == "better_in_3h":
                items.append("option to start 2-3h later")

            unique_items: list[str] = []
            seen: set[str] = set()
            for item in items:
                key = item.lower().strip()
                if key in seen:
                    continue
                seen.add(key)
                unique_items.append(item)
            return ", ".join(unique_items)

        sea_temp_official = _optional_float(values.get("sensor.beach_water_temperature_official"))
        sea_temp_model = _optional_float(values.get("sensor.sea_temperature_openmeteo"))
        sea_temp_now = sea_temp_official if sea_temp_official is not None else sea_temp_model
        rain_now = _optional_float(hourly_rows[0].get("rain_prob")) if hourly_rows else None
        uv_now = _optional_float(hourly_rows[0].get("astro_uv")) if hourly_rows else None
        if uv_now is None:
            uv_now = _optional_float(hourly_rows[0].get("uv")) if hourly_rows else None

        default_outdoor_scores: list[int] = []
        default_beach_scores: list[int] = []
        for row in hourly_rows:
            default_outdoor_scores.append(
                score_outdoor(
                    row,
                    mode=planner_mode_default,
                    skin_type=3,
                    uv_sensitivity=1.0,
                    heat_sensitivity=1.0,
                )
            )
            default_beach_scores.append(
                score_beach(
                    row,
                    mode=planner_mode_default,
                    skin_type=3,
                    uv_sensitivity=1.0,
                    heat_sensitivity=1.0,
                )
            )

        comparison_index: int | None = None
        if len(hourly_rows) > 3:
            comparison_index = 3
        elif len(hourly_rows) > 2:
            comparison_index = 2

        outdoor_now = default_outdoor_scores[0] if default_outdoor_scores else None
        outdoor_future = (
            default_outdoor_scores[comparison_index]
            if comparison_index is not None and comparison_index < len(default_outdoor_scores)
            else None
        )
        beach_now = default_beach_scores[0] if default_beach_scores else None
        beach_future = (
            default_beach_scores[comparison_index]
            if comparison_index is not None and comparison_index < len(default_beach_scores)
            else None
        )
        outdoor_trend = trend_label(outdoor_now, outdoor_future)
        beach_trend = trend_label(beach_now, beach_future)
        outdoor_summary = (
            f"{outdoor_now}->{outdoor_future}"
            if outdoor_now is not None and outdoor_future is not None
            else "unavailable"
        )
        beach_summary = (
            f"{beach_now}->{beach_future}"
            if beach_now is not None and beach_future is not None
            else "unavailable"
        )
        now_vs_summary = f"outdoor:{outdoor_summary}, beach:{beach_summary}"

        beach_recommendation = str(values.get("sensor.beach_recommendation") or "").strip().lower()
        beach_flag = str(values.get("sensor.beach_flag_calculated") or "").strip().lower()
        has_beach_premise = (
            sea_temp_now is not None
            and sea_temp_now >= 19.0
            and beach_flag != "red"
            and (
                beach_recommendation == "recommended"
                or (beach_now is not None and beach_now >= 68)
            )
        )

        walking_tokens = ("walking", "on_foot", "walk", "foot", "пеш", "топ")
        is_walking = False
        for persona in personas_rows:
            person_entity_id = persona.get("person_entity_id")
            if not isinstance(person_entity_id, str) or not person_entity_id.strip():
                continue
            state = self.hass.states.get(person_entity_id.strip())
            if state is None:
                continue
            value = str(state.state or "").strip().lower()
            if not value:
                continue
            if any(token in value for token in walking_tokens):
                is_walking = True
                break
            if value not in {"home", "unknown", "unavailable", "none"}:
                is_walking = True

        beach_pack_trigger = "not_ready"
        if not daily_plan_enabled:
            beach_pack_trigger = "disabled"
        elif is_walking and has_beach_premise:
            beach_pack_trigger = "ready"
        global_pack_list = pack_list_for_mode(
            mode=planner_mode_default,
            sea_temp_now=sea_temp_now,
            rain_now=rain_now,
            uv_now=uv_now,
            trend_outdoor=outdoor_trend,
        )
        global_notification_state = "notify" if beach_pack_trigger == "ready" else "idle"
        global_notification_key = "aura_beach_pack_plan"

        result: list[dict[str, Any]] = [
            planner_metric(
                "sensor.aura_daily_plan_status",
                "AURA daily plan status",
                "enabled" if daily_plan_enabled else "disabled",
                icon="mdi:calendar-check",
            ),
            planner_metric(
                "sensor.aura_planner_mode_default",
                "AURA planner mode (default)",
                planner_mode_default,
                icon="mdi:calendar-clock",
            ),
            planner_metric(
                "sensor.aura_now_vs_3h_outdoor",
                "AURA outdoor now vs +2..3h",
                outdoor_trend if daily_plan_enabled else "disabled",
                icon="mdi:walk",
            ),
            planner_metric(
                "sensor.aura_now_vs_3h_beach",
                "AURA beach now vs +2..3h",
                beach_trend if daily_plan_enabled else "disabled",
                icon="mdi:beach",
            ),
            planner_metric(
                "sensor.aura_now_vs_3h_summary",
                "AURA now vs +2..3h summary",
                now_vs_summary if daily_plan_enabled else "daily_plan_disabled",
                icon="mdi:timeline-clock-outline",
            ),
            planner_metric(
                "sensor.aura_beach_pack_trigger",
                "AURA beach pack trigger",
                beach_pack_trigger,
                icon="mdi:bag-suitcase-outline",
            ),
            planner_metric(
                "sensor.aura_beach_pack_list",
                "AURA beach pack list",
                global_pack_list if daily_plan_enabled else "daily_plan_disabled",
                icon="mdi:bag-personal",
            ),
            planner_metric(
                "sensor.aura_beach_notification_key",
                "AURA beach notification key",
                global_notification_key,
                icon="mdi:key-outline",
            ),
            planner_metric(
                "sensor.aura_beach_notification_state",
                "AURA beach notification state",
                global_notification_state,
                icon="mdi:bell-ring-outline",
                extras={
                    "notification_key": global_notification_key,
                    "notification_family": "ai_foundation",
                    "notification_scope": "outdoor",
                    "notification_message_ru": (
                        "Пляжный сбор активирован: условия подходят."
                        if global_notification_state == "notify"
                        else "Пляжный сбор не требуется."
                    ),
                    "notification_message_en": (
                        "Beach pack plan is active: conditions look good."
                        if global_notification_state == "notify"
                        else "Beach pack plan is idle."
                    ),
                },
            ),
        ]

        planner_payload: dict[str, Any] = {
            "enabled": daily_plan_enabled,
            "default_mode": planner_mode_default,
            "comparison_hours": comparison_hours,
            "now_vs_3h": {
                "outdoor": outdoor_trend if daily_plan_enabled else "disabled",
                "beach": beach_trend if daily_plan_enabled else "disabled",
                "outdoor_scores": {
                    "now": outdoor_now,
                    "future": outdoor_future,
                },
                "beach_scores": {
                    "now": beach_now,
                    "future": beach_future,
                },
                "summary": now_vs_summary,
            },
            "beach_pack": {
                "trigger": beach_pack_trigger,
                "is_walking": is_walking,
                "sea_temp_now": sea_temp_now,
                "list": global_pack_list,
                "notification_key": global_notification_key,
                "notification_state": global_notification_state,
            },
            "personas": [],
        }

        for persona in personas_rows:
            persona_id = str(persona.get("id") or "").strip()
            if not persona_id:
                continue
            persona_name = str(persona.get("name") or persona_id).strip() or persona_id
            person_entity_id = persona.get("person_entity_id")
            if not isinstance(person_entity_id, str) or not person_entity_id.strip():
                person_entity_id = None
            else:
                person_entity_id = person_entity_id.strip()
            mode = _normalize_planner_mode(persona.get("planner_mode", planner_mode_default))
            skin_type = _safe_int(persona.get("skin_type"), 3)
            if skin_type < 1:
                skin_type = 1
            if skin_type > 6:
                skin_type = 6
            uv_sensitivity = _clamp_float(persona.get("uv_sensitivity", 1.0), 1.0, 0.5, 2.5)
            heat_sensitivity = _clamp_float(
                persona.get("heat_sensitivity", 1.0), 1.0, 0.6, 1.8
            )

            outdoor_scores: list[int] = []
            beach_scores: list[int] = []
            for row in hourly_rows:
                outdoor_scores.append(
                    score_outdoor(
                        row,
                        mode=mode,
                        skin_type=skin_type,
                        uv_sensitivity=uv_sensitivity,
                        heat_sensitivity=heat_sensitivity,
                    )
                )
                beach_scores.append(
                    score_beach(
                        row,
                        mode=mode,
                        skin_type=skin_type,
                        uv_sensitivity=uv_sensitivity,
                        heat_sensitivity=heat_sensitivity,
                    )
                )

            profile = mode_profiles.get(mode, mode_profiles["normal"])
            best_outdoor = (
                best_hours(hourly_rows, outdoor_scores, profile["outdoor_threshold"])
                if daily_plan_enabled and outdoor_scores
                else "unavailable"
            )
            best_beach = (
                best_hours(hourly_rows, beach_scores, profile["beach_threshold"])
                if daily_plan_enabled and beach_scores
                else "unavailable"
            )

            persona_outdoor_now = outdoor_scores[0] if outdoor_scores else None
            persona_outdoor_future = (
                outdoor_scores[comparison_index]
                if comparison_index is not None and comparison_index < len(outdoor_scores)
                else None
            )
            persona_beach_now = beach_scores[0] if beach_scores else None
            persona_beach_future = (
                beach_scores[comparison_index]
                if comparison_index is not None and comparison_index < len(beach_scores)
                else None
            )
            persona_now_vs = trend_label(persona_outdoor_now, persona_outdoor_future)
            persona_pack_ready = (
                daily_plan_enabled
                and beach_pack_trigger == "ready"
                and best_beach not in {"none", "unavailable"}
            )
            persona_pack_list = pack_list_for_mode(
                mode=mode,
                sea_temp_now=sea_temp_now,
                rain_now=rain_now,
                uv_now=uv_now,
                trend_outdoor=persona_now_vs,
            )
            persona_notification_state = "notify" if persona_pack_ready else "idle"
            persona_notification_key = f"aura_{persona_id}_beach_pack_plan"
            persona_daily_plan = (
                f"mode={mode}; outdoor={best_outdoor}; beach={best_beach}; now_vs_3h={persona_now_vs}"
                if daily_plan_enabled
                else "daily_plan_disabled"
            )

            persona_prefix = f"sensor.aura_{persona_id}"
            result.extend(
                [
                    planner_metric(
                        f"{persona_prefix}_planner_mode",
                        f"{persona_name} planner mode",
                        mode,
                        icon="mdi:calendar-clock",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_best_hours_outdoor",
                        f"{persona_name} best outdoor hours",
                        best_outdoor,
                        icon="mdi:walk",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_best_hours_beach",
                        f"{persona_name} best beach hours",
                        best_beach,
                        icon="mdi:beach",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_now_vs_3h",
                        f"{persona_name} now vs +2..3h",
                        persona_now_vs if daily_plan_enabled else "disabled",
                        icon="mdi:timeline-clock-outline",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_daily_plan",
                        f"{persona_name} daily plan",
                        persona_daily_plan,
                        icon="mdi:calendar-text",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_pack_list",
                        f"{persona_name} beach pack list",
                        persona_pack_list if daily_plan_enabled else "daily_plan_disabled",
                        icon="mdi:bag-personal",
                        source_entity=person_entity_id,
                    ),
                    planner_metric(
                        f"{persona_prefix}_smart_notification",
                        f"{persona_name} smart notification",
                        persona_notification_state,
                        icon="mdi:bell-ring-outline",
                        source_entity=person_entity_id,
                        extras={
                            "notification_key": persona_notification_key,
                            "notification_family": "ai_foundation",
                            "notification_scope": "outdoor",
                            "notification_message_ru": (
                                f"{persona_name}: собраться на пляж, окно {best_beach}."
                                if persona_notification_state == "notify"
                                else f"{persona_name}: уведомление не требуется."
                            ),
                            "notification_message_en": (
                                f"{persona_name}: beach packing is recommended ({best_beach})."
                                if persona_notification_state == "notify"
                                else f"{persona_name}: notification is idle."
                            ),
                        },
                    ),
                ]
            )

            planner_payload["personas"].append(
                {
                    "id": persona_id,
                    "name": persona_name,
                    "mode": mode,
                    "best_hours_outdoor": best_outdoor,
                    "best_hours_beach": best_beach,
                    "now_vs_3h": persona_now_vs if daily_plan_enabled else "disabled",
                    "outdoor_scores": {
                        "now": persona_outdoor_now,
                        "future": persona_outdoor_future,
                    },
                    "beach_scores": {
                        "now": persona_beach_now,
                        "future": persona_beach_future,
                    },
                    "pack_trigger": "ready" if persona_pack_ready else "idle",
                    "pack_list": persona_pack_list,
                    "notification_key": persona_notification_key,
                    "notification_state": persona_notification_state,
                    "person_entity_id": person_entity_id,
                }
            )

        return result, planner_payload
