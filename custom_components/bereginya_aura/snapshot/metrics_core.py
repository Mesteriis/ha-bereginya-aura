"""Core metric builders and public sensor publishing for Beregynya AURA."""

from __future__ import annotations

from typing import Any

from homeassistant.core import State
from homeassistant.util import dt as dt_util

from ..const import (
    CONF_PUBLIC_SENSOR,
    CONF_SOURCE_MODE,
    CONF_SOURCES,
    DEFAULT_PUBLIC_SENSOR,
    DOMAIN,
    INVALID_HA_STATES,
    SOURCE_MODE_HA_ONLY,
    SOURCE_MODE_HYBRID,
    SOURCE_MODE_INTERNAL,
)
from .constants import *  # noqa: F403
from .options import _coerce_public_sensor
from .shared import *  # noqa: F403


class AuraCoreMetricsMixin:
    def _select_hour_index(self, hourly: dict[str, Any]) -> int:
        """Pick index matching current local time or return 0."""
        times = hourly.get("time")
        if not isinstance(times, list) or not times:
            return 0

        tz = dt_util.get_time_zone(self.hass.config.time_zone) or UTC
        now_local = dt_util.now().astimezone(tz)
        for idx, raw_time in enumerate(times):
            if not isinstance(raw_time, str):
                continue
            parsed = dt_util.parse_datetime(raw_time)
            if parsed is None:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=tz)
            if parsed >= now_local:
                return idx
        return 0

    def _build_internal_metrics(
        self,
        *,
        latitude: float,
        longitude: float,
        weather_data: dict[str, Any] | None,
        marine_data: dict[str, Any] | None,
        air_data: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Build metrics from remote APIs without synthetic substitute values."""
        weather_hourly = weather_data.get("hourly", {}) if isinstance(weather_data, dict) else {}
        marine_hourly = marine_data.get("hourly", {}) if isinstance(marine_data, dict) else {}
        air_hourly = air_data.get("hourly", {}) if isinstance(air_data, dict) else {}

        weather_idx = self._select_hour_index(weather_hourly)
        marine_idx = self._select_hour_index(marine_hourly)
        air_idx = self._select_hour_index(air_hourly)

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
        ) -> dict[str, Any]:
            item: dict[str, Any] = {
                "entity_id": entity_id,
                "name": name,
                "value": "unavailable" if value is None else value,
                "source": "internal_api",
            }
            if unit is not None:
                item["unit"] = unit
            if icon is not None:
                item["icon"] = icon
            return item

        temperature = hourly_float(weather_hourly, "temperature_2m", weather_idx, 1)
        apparent_temperature = hourly_float(
            weather_hourly, "apparent_temperature", weather_idx, 1
        )
        precipitation_probability = hourly_int(
            weather_hourly, "precipitation_probability", weather_idx
        )
        precipitation = hourly_float(weather_hourly, "precipitation", weather_idx, 1)
        weather_code = hourly_int(weather_hourly, "weather_code", weather_idx)
        uv_index = hourly_float(weather_hourly, "uv_index", weather_idx, 1)
        wind_speed_kmh = hourly_float(weather_hourly, "wind_speed_10m", weather_idx, 1)
        wind_speed = _kmh_to_ms(wind_speed_kmh, 1)
        pressure = hourly_int(weather_hourly, "surface_pressure", weather_idx)
        humidity = hourly_int(weather_hourly, "relative_humidity_2m", weather_idx)

        rain_next_6h: int | None = None
        weather_rain = weather_hourly.get("precipitation_probability")
        if isinstance(weather_rain, list) and weather_rain:
            rain_window = weather_rain[weather_idx : weather_idx + 6]
            numeric = [_optional_float(val) for val in rain_window]
            numeric = [val for val in numeric if val is not None]
            if numeric:
                rain_next_6h = int(round(max(numeric)))

        sea_temperature = hourly_float(
            marine_hourly, "sea_surface_temperature", marine_idx, 1
        )
        sea_temperature_3h = hourly_float(
            marine_hourly, "sea_surface_temperature", marine_idx + 3, 1
        )
        sea_temperature_6h = hourly_float(
            marine_hourly, "sea_surface_temperature", marine_idx + 6, 1
        )
        wave_height = hourly_float(marine_hourly, "wave_height", marine_idx, 2)
        wave_period = hourly_float(marine_hourly, "wave_period", marine_idx, 1)

        aqi = hourly_int(air_hourly, "european_aqi", air_idx)
        pm25 = hourly_float(air_hourly, "pm2_5", air_idx, 1)
        pm10 = hourly_float(air_hourly, "pm10", air_idx, 1)
        ozone = hourly_float(air_hourly, "ozone", air_idx, 1)
        no2 = hourly_float(air_hourly, "nitrogen_dioxide", air_idx, 1)
        so2 = hourly_float(air_hourly, "sulphur_dioxide", air_idx, 1)
        co = hourly_int(air_hourly, "carbon_monoxide", air_idx)
        dust_now = hourly_float(air_hourly, "dust", air_idx, 1)
        dust_6h = hourly_float(air_hourly, "dust", air_idx + 6, 1)

        pollen_grass = hourly_int(air_hourly, "grass_pollen", air_idx)
        pollen_birch = hourly_int(air_hourly, "birch_pollen", air_idx)
        pollen_alder = hourly_int(air_hourly, "alder_pollen", air_idx)
        pollen_olive = hourly_int(air_hourly, "olive_pollen", air_idx)
        pollen_ragweed = hourly_int(air_hourly, "ragweed_pollen", air_idx)
        pollen_mugwort = hourly_int(air_hourly, "mugwort_pollen", air_idx)
        pollen_values = [
            pollen_grass,
            pollen_birch,
            pollen_alder,
            pollen_olive,
            pollen_ragweed,
            pollen_mugwort,
        ]
        pollen_total = sum(pollen_values) if all(v is not None for v in pollen_values) else None

        ambrosia_risk: str | None = None
        if pollen_ragweed is not None:
            ambrosia_risk = "low"
            if pollen_ragweed > 50:
                ambrosia_risk = "very_high"
            elif pollen_ragweed > 20:
                ambrosia_risk = "high"
            elif pollen_ragweed > 5:
                ambrosia_risk = "moderate"

        dust_level = _dust_level(dust_now) if dust_now is not None else None
        allergy_index = (
            _allergy_index(float(pollen_total), float(dust_now), float(aqi))
            if pollen_total is not None and dust_now is not None and aqi is not None
            else None
        )
        asthma_risk = (
            _asthma_risk(float(aqi), float(pm25), float(dust_now), float(pollen_total))
            if aqi is not None
            and pm25 is not None
            and dust_now is not None
            and pollen_total is not None
            else None
        )

        beach_flag: str | None = None
        if wave_height is not None and wind_speed_kmh is not None:
            beach_flag = "green"
            if wave_height > 2.0 or wind_speed_kmh > 40:
                beach_flag = "red"
            elif wave_height > 1.2 or wind_speed_kmh > 25:
                beach_flag = "yellow"

        beach_danger_index: str | None = None
        if beach_flag is not None and uv_index is not None:
            beach_danger_index = "Low"
            if beach_flag == "red" or uv_index > 10:
                beach_danger_index = "High"
            elif beach_flag == "yellow" or uv_index > 8:
                beach_danger_index = "Medium"

        beach_crowding: str | None = None
        if temperature is not None and precipitation_probability is not None:
            hour = dt_util.now().hour
            weekday = dt_util.now().weekday()
            crowd_score = 0
            if 11 <= hour <= 14:
                crowd_score += 3
            elif 10 <= hour <= 16:
                crowd_score += 2
            elif 9 <= hour <= 18:
                crowd_score += 1
            if weekday >= 5:
                crowd_score += 2
            if temperature > 25 and precipitation_probability < 20:
                crowd_score += 2
            elif temperature > 20 and precipitation_probability < 40:
                crowd_score += 1
            if precipitation_probability > 50:
                crowd_score -= 3

            if crowd_score >= 6:
                beach_crowding = "very_crowded"
            elif crowd_score >= 4:
                beach_crowding = "crowded"
            elif crowd_score >= 2:
                beach_crowding = "normal"
            else:
                beach_crowding = "empty"

        beach_comfort: int | None = None
        if (
            beach_flag is not None
            and sea_temperature is not None
            and uv_index is not None
            and beach_crowding is not None
        ):
            score = 10
            if beach_flag == "red":
                score -= 5
            elif beach_flag == "yellow":
                score -= 2
            if sea_temperature < 18:
                score -= 2
            elif sea_temperature < 20:
                score -= 1
            elif sea_temperature >= 24:
                score += 1
            if uv_index > 10:
                score -= 2
            elif uv_index > 8:
                score -= 1
            if beach_crowding == "very_crowded":
                score -= 1
            beach_comfort = max(0, min(10, score))

        beach_recommendation: str | None = None
        if (
            beach_comfort is not None
            and beach_flag is not None
            and precipitation_probability is not None
        ):
            beach_recommendation = "Not ideal"
            if (
                beach_comfort >= 7
                and beach_flag == "green"
                and precipitation_probability < 20
            ):
                beach_recommendation = "Recommended"

        weather_summary = (
            _weather_summary(float(temperature), float(precipitation_probability))
            if temperature is not None and precipitation_probability is not None
            else None
        )
        waqi_proxy = aqi + 12 if aqi is not None else None

        return [
            metric("sensor.weather_summary", "Weather summary", weather_summary),
            metric("sensor.weather_code", "Weather code", weather_code),
            metric(
                "sensor.precipitation_probability",
                "Precipitation probability",
                precipitation_probability,
                "%",
            ),
            metric("sensor.precipitation", "Precipitation", precipitation, "mm"),
            metric("sensor.uv_index", "UV index", uv_index),
            metric(
                "sensor.rain_next_6h",
                "Rain probability next 6h",
                rain_next_6h,
                "%",
            ),
            metric("sensor.wind_speed", "Wind speed", wind_speed, "m/s"),
            metric("sensor.pressure", "Pressure", pressure, "hPa"),
            metric("sensor.humidity", "Humidity", humidity, "%"),
            metric(
                "sensor.apparent_temperature",
                "Apparent temperature",
                apparent_temperature if apparent_temperature is not None else temperature,
                "degC",
            ),
            metric(
                "sensor.sea_temperature_openmeteo",
                "Sea temperature",
                sea_temperature,
                "degC",
            ),
            metric(
                "sensor.sea_temperature_openmeteo_3h",
                "Sea temperature +3h",
                sea_temperature_3h,
                "degC",
            ),
            metric(
                "sensor.sea_temperature_openmeteo_6h",
                "Sea temperature +6h",
                sea_temperature_6h,
                "degC",
            ),
            metric("sensor.wave_height", "Wave height", wave_height, "m"),
            metric("sensor.wave_period", "Wave period", wave_period, "s"),
            metric("sensor.pollen_total", "Pollen total", pollen_total, "grains/m3"),
            metric("sensor.pollen_birch", "Pollen birch", pollen_birch, "grains/m3"),
            metric("sensor.pollen_alder", "Pollen alder", pollen_alder, "grains/m3"),
            metric("sensor.pollen_grass", "Pollen grass", pollen_grass, "grains/m3"),
            metric("sensor.pollen_olive", "Pollen olive", pollen_olive, "grains/m3"),
            metric("sensor.pollen_ragweed", "Pollen ragweed", pollen_ragweed, "grains/m3"),
            metric("sensor.pollen_ambrosia", "Pollen ambrosia", pollen_ragweed, "grains/m3"),
            metric("sensor.ambrosia_risk", "Ambrosia risk", ambrosia_risk),
            metric("sensor.allergy_index", "Allergy index", allergy_index, "/100"),
            metric("sensor.asthma_risk", "Asthma risk", asthma_risk),
            metric("sensor.pollen_mugwort", "Pollen mugwort", pollen_mugwort, "grains/m3"),
            metric("sensor.air_quality_european_aqi", "European AQI", aqi, "AQI"),
            metric("sensor.air_quality_pm25", "PM2.5", pm25, "ug/m3"),
            metric("sensor.air_quality_pm10", "PM10", pm10, "ug/m3"),
            metric("sensor.air_quality_ozone", "Ozone (O3)", ozone, "ug/m3"),
            metric("sensor.air_quality_no2", "Nitrogen dioxide", no2, "ug/m3"),
            metric("sensor.air_quality_so2", "Sulfur dioxide", so2, "ug/m3"),
            metric("sensor.air_quality_co", "Carbon monoxide", co, "ug/m3"),
            metric("sensor.waqi_barcelona", "WAQI proxy", waqi_proxy),
            metric("sensor.saharan_dust_level", "Saharan dust level", dust_level),
            metric(
                "sensor.saharan_dust_forecast_6h",
                "Saharan dust forecast +6h",
                dust_6h,
                "ug/m3",
            ),
            metric("sensor.beach_flag_calculated", "Beach flag (calculated)", beach_flag),
            metric("sensor.beach_danger_index", "Beach danger index", beach_danger_index),
            metric(
                "sensor.beach_crowding_estimate",
                "Beach crowding estimate",
                beach_crowding,
            ),
            metric("sensor.beach_comfort_index", "Beach comfort index", beach_comfort, "/10"),
            metric("sensor.beach_recommendation", "Beach recommendation", beach_recommendation),
        ]

    def _build_forecast_daily(
        self,
        *,
        forecast_days: int,
        weather_data: dict[str, Any] | None,
        marine_data: dict[str, Any] | None,
        air_data: dict[str, Any] | None,
        mosquito_baseline_index: int | None,
        jellyfish_baseline_risk: str,
        tick_baseline_index: int | None,
    ) -> list[dict[str, Any]]:
        """Build 1..7 day forecast summary."""
        weather_daily = weather_data.get("daily", {}) if isinstance(weather_data, dict) else {}
        weather_days = weather_daily.get("time")
        if not isinstance(weather_days, list) or not weather_days:
            return []

        marine_hourly = marine_data.get("hourly", {}) if isinstance(marine_data, dict) else {}
        air_hourly = air_data.get("hourly", {}) if isinstance(air_data, dict) else {}

        result: list[dict[str, Any]] = []
        for idx, day in enumerate(weather_days[:forecast_days]):
            if not isinstance(day, str):
                continue

            temp_max = round(
                _safe_float(_hourly_value(weather_daily, "temperature_2m_max", idx, 0.0), 0.0), 1
            )
            temp_min = round(
                _safe_float(_hourly_value(weather_daily, "temperature_2m_min", idx, 0.0), 0.0), 1
            )
            rain_prob_max = _safe_int(
                _hourly_value(weather_daily, "precipitation_probability_max", idx, 0), 0
            )
            rain_sum = round(
                _safe_float(_hourly_value(weather_daily, "precipitation_sum", idx, 0.0), 0.0), 1
            )
            uv_max = round(
                _safe_float(_hourly_value(weather_daily, "uv_index_max", idx, 0.0), 0.0), 1
            )
            wind_max = round(
                _safe_float(_hourly_value(weather_daily, "wind_speed_10m_max", idx, 0.0), 0.0), 1
            )
            wind_max_ms = _kmh_to_ms(wind_max, 1)
            weather_code = _safe_int(_hourly_value(weather_daily, "weather_code", idx, 0), 0)

            sea_values = _daily_hourly_values(marine_hourly, "sea_surface_temperature", day)
            wave_values = _daily_hourly_values(marine_hourly, "wave_height", day)
            wave_period_values = _daily_hourly_values(marine_hourly, "wave_period", day)
            aqi_values = _daily_hourly_values(air_hourly, "european_aqi", day)
            pm25_values = _daily_hourly_values(air_hourly, "pm2_5", day)
            dust_values = _daily_hourly_values(air_hourly, "dust", day)
            pollen_grass = _daily_hourly_values(air_hourly, "grass_pollen", day)
            pollen_birch = _daily_hourly_values(air_hourly, "birch_pollen", day)
            pollen_alder = _daily_hourly_values(air_hourly, "alder_pollen", day)
            pollen_olive = _daily_hourly_values(air_hourly, "olive_pollen", day)
            pollen_ragweed = _daily_hourly_values(air_hourly, "ragweed_pollen", day)
            pollen_mugwort = _daily_hourly_values(air_hourly, "mugwort_pollen", day)

            sea_temp_avg = round(sum(sea_values) / len(sea_values), 1) if sea_values else 0.0
            wave_height_max = round(max(wave_values), 2) if wave_values else 0.0
            wave_period_avg = (
                round(sum(wave_period_values) / len(wave_period_values), 1)
                if wave_period_values
                else 0.0
            )
            aqi_max = int(round(max(aqi_values))) if aqi_values else 0
            pm25_max = round(max(pm25_values), 1) if pm25_values else 0.0
            dust_max = round(max(dust_values), 1) if dust_values else 0.0
            pollen_total = int(
                round(
                    (
                        (sum(pollen_grass) / len(pollen_grass) if pollen_grass else 0.0)
                        + (sum(pollen_birch) / len(pollen_birch) if pollen_birch else 0.0)
                        + (sum(pollen_alder) / len(pollen_alder) if pollen_alder else 0.0)
                        + (sum(pollen_olive) / len(pollen_olive) if pollen_olive else 0.0)
                        + (sum(pollen_ragweed) / len(pollen_ragweed) if pollen_ragweed else 0.0)
                        + (sum(pollen_mugwort) / len(pollen_mugwort) if pollen_mugwort else 0.0)
                    )
                )
            )

            allergy_index = _allergy_index(float(pollen_total), float(dust_max), float(aqi_max))
            asthma_risk = _asthma_risk(
                float(aqi_max), float(pm25_max), float(dust_max), float(pollen_total)
            )

            beach_flag = "green"
            if wave_height_max > 2.0 or wind_max > 40:
                beach_flag = "red"
            elif wave_height_max > 1.2 or wind_max > 25:
                beach_flag = "yellow"

            beach_score = 10
            if beach_flag == "red":
                beach_score -= 5
            elif beach_flag == "yellow":
                beach_score -= 2
            if sea_temp_avg < 18:
                beach_score -= 2
            elif sea_temp_avg < 20:
                beach_score -= 1
            elif sea_temp_avg >= 24:
                beach_score += 1
            if uv_max > 10:
                beach_score -= 2
            elif uv_max > 8:
                beach_score -= 1
            if rain_prob_max > 60:
                beach_score -= 2
            elif rain_prob_max > 30:
                beach_score -= 1
            beach_score = max(0, min(10, beach_score))

            mosquito_risk_est = (
                _forecast_mosquito_risk(
                    baseline_index=mosquito_baseline_index,
                    temp_min=temp_min,
                    temp_max=temp_max,
                    rain_probability_max=rain_prob_max,
                    wind_max_kmh=wind_max,
                )
                if mosquito_baseline_index is not None
                else "unavailable"
            )
            jellyfish_risk_est = _forecast_jellyfish_risk(
                baseline_risk=jellyfish_baseline_risk,
                sea_temp_avg=sea_temp_avg,
                wave_height_max=wave_height_max,
                wind_max_kmh=wind_max,
            )
            tick_risk_est = (
                _forecast_tick_risk(
                    baseline_index=tick_baseline_index,
                    temp_min=temp_min,
                    temp_max=temp_max,
                    rain_probability_max=rain_prob_max,
                    wind_max_kmh=wind_max,
                )
                if tick_baseline_index is not None
                else "unavailable"
            )

            result.append(
                {
                    "date": day,
                    "weather_code": weather_code,
                    "temp_min": temp_min,
                    "temp_max": temp_max,
                    "rain_probability_max": rain_prob_max,
                    "rain_sum_mm": rain_sum,
                    "uv_max": uv_max,
                    "wind_max_ms": wind_max_ms,
                    "wind_max_kmh": wind_max,
                    "sea_temp_avg": sea_temp_avg,
                    "wave_height_max": wave_height_max,
                    "wave_period_avg": wave_period_avg,
                    "aqi_max": aqi_max,
                    "dust_max": dust_max,
                    "pollen_total_est": pollen_total,
                    "allergy_index": allergy_index,
                    "asthma_risk": asthma_risk,
                    "beach_flag": beach_flag,
                    "beach_score": beach_score,
                    "mosquito_risk_est": mosquito_risk_est,
                    "jellyfish_risk_est": jellyfish_risk_est,
                    "tick_risk_est": tick_risk_est,
                }
            )

        return result

    def _decorate_entity_icons(self, metrics: list[dict[str, Any]]) -> None:
        """Attach icon URLs (PNG/WebP/GIF) to each metric."""
        weather_code: int | None = None
        for metric in metrics:
            if metric.get("entity_id") != "sensor.weather_code":
                continue
            weather_code = _optional_int(metric.get("value"))
            break

        for metric in metrics:
            entity_id = metric.get("entity_id")
            if not isinstance(entity_id, str):
                continue
            emoji_code = _metric_emoji_code(entity_id, weather_code)
            if emoji_code is None:
                continue

            bundle = _noto_icon_bundle(emoji_code)
            metric["icon_emoji"] = bundle["emoji_code"]
            metric["icon_url"] = bundle["icon_url"]
            metric["icon_webp_url"] = bundle["icon_webp_url"]
            metric["icon_gif_url"] = bundle["icon_gif_url"]

            value = metric.get("value")
            if entity_id == "sensor.tick_icon_url":
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    metric["icon_external_url"] = value
            elif entity_id == "sensor.tiger_mosquito_icon_url":
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    metric["icon_external_url"] = value
            elif entity_id in {
                "sensor.wildfire_icon_url",
                "sensor.hazard_top_event_icon_url",
                "sensor.earthquake_event_url",
                "sensor.wildfire_nearest_link",
            }:
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    metric["icon_external_url"] = value
            elif entity_id == "sensor.cap_source":
                cap_link = metric.get("cap_link")
                if isinstance(cap_link, str) and cap_link.startswith(("http://", "https://")):
                    metric["icon_external_url"] = cap_link
            elif entity_id == "sensor.jellyfish_icon_code":
                if isinstance(value, str) and value not in {"", "unknown", "unavailable"}:
                    metric["icon_external_code"] = value

    def _decorate_forecast_icons(self, forecast_daily: list[dict[str, Any]]) -> None:
        """Attach icon URLs to each forecast day row."""
        mosquito_bundle = _noto_icon_bundle("1f99f")
        jellyfish_bundle = _noto_icon_bundle("1f41f")
        tick_bundle = _noto_icon_bundle("1f41b")

        for day in forecast_daily:
            if not isinstance(day, dict):
                continue
            weather_code = _optional_int(day.get("weather_code"))
            weather_bundle = _noto_icon_bundle(_weather_emoji_code(weather_code))

            day["weather_icon_emoji"] = weather_bundle["emoji_code"]
            day["weather_icon_url"] = weather_bundle["icon_url"]
            day["weather_icon_webp_url"] = weather_bundle["icon_webp_url"]
            day["weather_icon_gif_url"] = weather_bundle["icon_gif_url"]

            day["mosquito_icon_gif_url"] = mosquito_bundle["icon_gif_url"]
            day["jellyfish_icon_gif_url"] = jellyfish_bundle["icon_gif_url"]
            day["tick_icon_gif_url"] = tick_bundle["icon_gif_url"]

    def _build_icon_catalog(
        self,
        *,
        metrics: list[dict[str, Any]],
        forecast_daily: list[dict[str, Any]],
        jellyfish_data: dict[str, Any] | None,
        mosquito_data: dict[str, Any] | None,
        tick_data: dict[str, Any] | None,
        earthquake_data: dict[str, Any] | None,
        gdacs_events: list[dict[str, Any]] | None,
        cap_data: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build icon catalog for external reuse."""
        weather_code: int | None = None
        for metric in metrics:
            if metric.get("entity_id") == "sensor.weather_code":
                weather_code = _optional_int(metric.get("value"))
                break
        weather_bundle = _noto_icon_bundle(_weather_emoji_code(weather_code))

        entity_icons: dict[str, dict[str, Any]] = {}
        icon_keys = (
            "icon",
            "icon_emoji",
            "icon_url",
            "icon_webp_url",
            "icon_gif_url",
            "icon_external_url",
            "icon_external_code",
        )
        for metric in metrics:
            entity_id = metric.get("entity_id")
            if not isinstance(entity_id, str):
                continue
            payload: dict[str, Any] = {}
            for key in icon_keys:
                value = metric.get(key)
                if isinstance(value, str) and value:
                    payload[key] = value
            if payload:
                entity_icons[entity_id] = payload

        catalog: dict[str, Any] = {
            "weather_current": {
                "weather_code": weather_code if weather_code is not None else "unavailable",
                **weather_bundle,
            },
            "categories": {
                "weather": weather_bundle,
                "marine": _noto_icon_bundle("1f30a"),
                "allergy": _noto_icon_bundle("1f927"),
                "air_quality": _noto_icon_bundle("1f637"),
                "jellyfish": _noto_icon_bundle("1f41f"),
                "tiger_mosquito": _noto_icon_bundle("1f99f"),
                "ticks": _noto_icon_bundle("1f41b"),
                "rip_current": _noto_icon_bundle("1f30a"),
                "heat_stress": _noto_icon_bundle("1f321_fe0f"),
                "sunburn": _noto_icon_bundle("1f31e"),
                "earthquakes": _noto_icon_bundle("1f30b"),
                "wildfire": _noto_icon_bundle("1f525"),
                "hazards": _noto_icon_bundle("1f6a8"),
                "planner": _noto_icon_bundle("1f4c5"),
                "notifications": _noto_icon_bundle("1f514"),
                "astro_risk": _noto_icon_bundle("1f31e"),
                "uv_dose": _noto_icon_bundle("1f31e"),
                "hydration": _noto_icon_bundle("1f4a7"),
                "thunderstorm": _noto_icon_bundle("26a1_fe0f"),
                "tides_currents": _noto_icon_bundle("1f30a"),
                "algae": _noto_icon_bundle("1f9ab"),
                "smoke": _noto_icon_bundle("1f32b_fe0f"),
                "cap_alerts": _noto_icon_bundle("1f6a8"),
                "bites": _noto_icon_bundle("1f99f"),
                "tracking": _noto_icon_bundle("1f4f1"),
            },
            "entities": entity_icons,
        }

        if isinstance(jellyfish_data, dict):
            catalog["jellyfish"] = {
                "status_icon_code": jellyfish_data.get("status_icon"),
                "nearest_beach": jellyfish_data.get("beach_name"),
                **_noto_icon_bundle("1f41f"),
            }
        if isinstance(mosquito_data, dict):
            catalog["tiger_mosquito"] = {
                "latest_report": mosquito_data.get("latest_received_at"),
                "external_icon_url": mosquito_data.get("icon_url"),
                **_noto_icon_bundle("1f99f"),
            }
        if isinstance(tick_data, dict):
            catalog["ticks"] = {
                "taxon": tick_data.get("taxon_name"),
                "external_icon_url": tick_data.get("icon_url"),
                "source": "iNaturalist",
                **_noto_icon_bundle("1f41b"),
            }
        if isinstance(earthquake_data, dict):
            catalog["earthquakes"] = {
                "source": "USGS",
                "count_24h": earthquake_data.get("count_24h"),
                "count_7d": earthquake_data.get("count_7d"),
                "max_magnitude_7d": earthquake_data.get("max_mag_7d"),
                "nearest_distance_km": earthquake_data.get("nearest_distance_km"),
                "event_url": earthquake_data.get("nearest_event_url"),
                **_noto_icon_bundle("1f30b"),
            }
        if isinstance(gdacs_events, list):
            current_events = [
                event for event in gdacs_events if isinstance(event, dict) and event.get("is_current") is True
            ]
            wf_events = [event for event in current_events if event.get("event_type") == "WF"]
            top_hazard_icon = None
            top_hazard_alert = "unknown"
            if current_events:
                top_event = max(
                    current_events,
                    key=lambda event: (
                        _alert_level_rank(str(event.get("alert_level"))),
                        _safe_int(event.get("published_ts"), 0),
                    ),
                )
                top_hazard_icon = top_event.get("icon_url")
                top_hazard_alert = top_event.get("alert_level")

            catalog["wildfire"] = {
                "source": "GDACS",
                "active_events_global": len(wf_events),
                "high_alert_events_global": sum(
                    1
                    for event in wf_events
                    if str(event.get("alert_level") or "").lower() in {"orange", "red"}
                ),
                "top_icon_url": wf_events[0].get("icon_url") if wf_events else None,
                **_noto_icon_bundle("1f525"),
            }
            catalog["hazards"] = {
                "source": "GDACS",
                "active_events_global": len(current_events),
                "top_alert_level": top_hazard_alert,
                "top_icon_url": top_hazard_icon,
                **_noto_icon_bundle("1f6a8"),
            }
        if isinstance(cap_data, dict):
            catalog["cap_alerts"] = {
                "source": "Meteoalarm",
                "active_alerts": cap_data.get("active_count"),
                "highest_severity": cap_data.get("highest_severity"),
                "top_event": cap_data.get("top_event"),
                "top_area": cap_data.get("top_area"),
                "top_expires": cap_data.get("top_expires"),
                "top_link": cap_data.get("top_link"),
                **_noto_icon_bundle("1f6a8"),
            }

        if forecast_daily:
            catalog["forecast_daily"] = [
                {
                    "date": day.get("date"),
                    "weather_code": day.get("weather_code"),
                    "weather_icon_url": day.get("weather_icon_url"),
                    "weather_icon_gif_url": day.get("weather_icon_gif_url"),
                    "mosquito_icon_gif_url": day.get("mosquito_icon_gif_url"),
                    "jellyfish_icon_gif_url": day.get("jellyfish_icon_gif_url"),
                    "tick_icon_gif_url": day.get("tick_icon_gif_url"),
                }
                for day in forecast_daily
                if isinstance(day, dict)
            ]

        return catalog

    def _apply_ha_sources(self, metrics: list[dict[str, Any]]) -> dict[str, int]:
        """Apply optional HA entity mappings on top of internal metrics."""
        source_mode = str(self._options[CONF_SOURCE_MODE])
        if source_mode == SOURCE_MODE_INTERNAL:
            return {"attempted": 0, "applied": 0, "missing": 0}

        source_map = self._options[CONF_SOURCES]
        if not isinstance(source_map, dict) or not source_map:
            return {"attempted": 0, "applied": 0, "missing": 0}

        metric_by_entity = {item["entity_id"]: item for item in metrics}
        attempted = 0
        applied = 0
        missing = 0

        for source_key, ha_entity_id in source_map.items():
            metric_id = _resolve_metric_id(source_key)
            if metric_id is None:
                continue
            metric = metric_by_entity.get(metric_id)
            if metric is None:
                continue

            attempted += 1
            state: State | None = self.hass.states.get(ha_entity_id)
            if state is None or state.state in INVALID_HA_STATES:
                missing += 1
                if source_mode == SOURCE_MODE_HA_ONLY:
                    metric["value"] = "unavailable"
                    metric["source"] = "ha_entity_missing"
                    metric["source_entity"] = ha_entity_id
                continue

            metric["value"] = _coerce_state_value(state.state, metric.get("value"))
            state_unit = state.attributes.get("unit_of_measurement")
            if isinstance(state_unit, str) and state_unit.strip():
                metric["unit"] = state_unit
            metric["source"] = "ha_entity"
            metric["source_entity"] = ha_entity_id
            applied += 1

        if source_mode == SOURCE_MODE_HA_ONLY:
            for metric in metrics:
                if metric.get("source") == "internal_api":
                    metric["value"] = "unavailable"
                    metric["source"] = "ha_only_unmapped"

        if source_mode == SOURCE_MODE_HYBRID and attempted == 0:
            for metric in metrics:
                if metric.get("source") != "ha_entity":
                    metric["source"] = "internal_api"

        return {"attempted": attempted, "applied": applied, "missing": missing}

    def clear_public_sensor_states(self) -> None:
        """Remove previously published public sensors."""
        for entity_id in list(self._published_public_entities):
            self.hass.states.async_remove(entity_id)
        self._published_public_entities.clear()

    def _sync_public_sensor_states(self, snapshot: dict[str, Any]) -> None:
        """Publish snapshot metrics as HA sensors when public export is enabled."""
        is_public = _coerce_public_sensor(
            self._options.get(CONF_PUBLIC_SENSOR, DEFAULT_PUBLIC_SENSOR),
            DEFAULT_PUBLIC_SENSOR,
        )
        if not is_public:
            self.clear_public_sensor_states()
            return

        entities = snapshot.get("entities")
        if not isinstance(entities, list):
            self.clear_public_sensor_states()
            return

        meta = snapshot.get("meta")
        generated_at = ""
        if isinstance(meta, dict):
            generated_at = str(meta.get("generated_at") or "")

        published_now: set[str] = set()
        used_entity_ids: set[str] = set()
        for item in entities:
            if not isinstance(item, dict):
                continue
            source_entity_id = str(item.get("entity_id") or "").strip()
            if not source_entity_id:
                continue
            public_entity_id = self._public_sensor_entity_id(
                source_entity_id,
                used_entity_ids=used_entity_ids,
            )
            state, attributes = self._public_sensor_payload(
                metric=item,
                generated_at=generated_at,
            )
            self.hass.states.async_set(public_entity_id, state, attributes)
            published_now.add(public_entity_id)

        snapshot_entity_id = f"sensor.{DOMAIN}_snapshot"
        self.hass.states.async_set(
            snapshot_entity_id,
            len(published_now),
            {
                "friendly_name": "Beregynya AURA Snapshot",
                "icon": "mdi:shield-wave",
                "attribution": "Beregynya AURA",
                "generated_at": generated_at,
                "metric_count": len(published_now),
                "source": "bereginya_aura_internal_api",
            },
        )
        published_now.add(snapshot_entity_id)

        for stale_entity_id in self._published_public_entities - published_now:
            self.hass.states.async_remove(stale_entity_id)
        self._published_public_entities = published_now

    def _public_sensor_entity_id(
        self,
        source_entity_id: str,
        *,
        used_entity_ids: set[str],
    ) -> str:
        """Build deterministic HA entity_id for public export."""
        sensor_key = source_entity_id.split(".", maxsplit=1)[-1].lower()
        sensor_slug = _PUBLIC_SENSOR_ID_PATTERN.sub("_", sensor_key).strip("_")
        if not sensor_slug:
            sensor_slug = "metric"
        base_entity_id = f"sensor.{DOMAIN}_{sensor_slug}"
        entity_id = base_entity_id
        suffix = 2
        while entity_id in used_entity_ids:
            entity_id = f"{base_entity_id}_{suffix}"
            suffix += 1
        used_entity_ids.add(entity_id)
        return entity_id

    def _public_sensor_payload(
        self,
        *,
        metric: dict[str, Any],
        generated_at: str,
    ) -> tuple[Any, dict[str, Any]]:
        """Convert metric row to HA state + attributes."""
        raw_value = metric.get("value")
        state: Any
        if raw_value is None:
            state = "unknown"
        elif isinstance(raw_value, bool):
            state = "true" if raw_value else "false"
        elif isinstance(raw_value, (int, float)):
            state = raw_value
        else:
            state_text = str(raw_value)
            if len(state_text) > 255:
                state = f"{state_text[:252]}..."
            else:
                state = state_text

        attributes: dict[str, Any] = {
            "friendly_name": metric.get("name") or metric.get("entity_id"),
            "attribution": "Beregynya AURA",
            "aura_generated_at": generated_at,
            "aura_original_entity_id": metric.get("entity_id"),
            "aura_source": metric.get("source"),
        }
        source_entity = metric.get("source_entity")
        if isinstance(source_entity, str) and source_entity.strip():
            attributes["aura_source_entity"] = source_entity

        unit = metric.get("unit")
        if isinstance(unit, str) and unit.strip():
            attributes["unit_of_measurement"] = unit

        icon = metric.get("icon")
        if isinstance(icon, str) and icon.strip():
            attributes["icon"] = icon

        for key in ("icon_url", "icon_webp_url", "icon_gif_url"):
            value = metric.get(key)
            if isinstance(value, str) and value:
                attributes[key] = value

        if not isinstance(raw_value, (int, float, bool, type(None))):
            state_text = str(raw_value)
            if len(state_text) > 255:
                attributes["aura_raw_value"] = state_text

        return state, attributes
