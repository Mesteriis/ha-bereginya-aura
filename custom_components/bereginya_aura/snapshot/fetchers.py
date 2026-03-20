"""Remote source fetchers for Beregynya AURA."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree as ET

from aiohttp import ClientError
from homeassistant.util import dt as dt_util

from .constants import *  # noqa: F403
from .shared import *  # noqa: F403


class AuraFetchersMixin:
    async def _async_fetch_json(self, url: str) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch JSON from remote API."""
        try:
            async with self._session.get(url, timeout=25) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
            if not isinstance(payload, dict):
                return None, "invalid_payload"
            return payload, None
        except (TimeoutError, ClientError, ValueError) as err:
            return None, str(err)

    async def _async_fetch_text(self, url: str) -> tuple[str | None, str | None]:
        """Fetch text payload from remote API."""
        try:
            async with self._session.get(url, timeout=25) as response:
                response.raise_for_status()
                payload = await response.text()
            if not isinstance(payload, str) or not payload.strip():
                return None, "empty_payload"
            return payload, None
        except (TimeoutError, ClientError, ValueError) as err:
            return None, str(err)

    async def _async_fetch_cams_featureinfo(
        self,
        *,
        layer: str,
        style: str,
        latitude: float,
        longitude: float,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch numeric CAMS value via WMS GetFeatureInfo."""
        span = 0.03
        params = {
            "token": "public",
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": layer,
            "QUERY_LAYERS": layer,
            "STYLES": style,
            "FORMAT": "image/png",
            "CRS": "EPSG:4326",
            "BBOX": (
                f"{latitude - span / 2.0:.6f},{longitude - span / 2.0:.6f},"
                f"{latitude + span / 2.0:.6f},{longitude + span / 2.0:.6f}"
            ),
            "WIDTH": 101,
            "HEIGHT": 101,
            "I": 50,
            "J": 50,
            "INFO_FORMAT": "text/plain",
        }
        url = _build_url(_ECMWF_CAMS_WMS, params)
        payload, error = await self._async_fetch_text(url)
        if not isinstance(payload, str):
            return None, error or f"{layer}:request_failed"

        parsed = _parse_cams_featureinfo_text(payload)
        if not isinstance(parsed, dict):
            return None, f"{layer}:invalid_featureinfo"
        parsed["layer"] = layer
        parsed["style"] = style
        parsed["source"] = "ecmwf_cams_wms"
        return parsed, None

    async def _async_fetch_smoke_tile_data(
        self,
        *,
        latitude: float,
        longitude: float,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch smoke-relevant numeric fields from CAMS WMS."""
        layer_map = {
            "bbaod550": ("composition_bbaod550", "sh_all_aod"),
            "pm2p5": ("composition_pm2p5", "sh_all_pm2p5_defra_daqi"),
            "fire_frp": ("composition_fire", "sh_all_fire"),
        }
        tasks = [
            self._async_fetch_cams_featureinfo(
                layer=layer,
                style=style,
                latitude=latitude,
                longitude=longitude,
            )
            for layer, style in layer_map.values()
        ]
        results = await asyncio.gather(*tasks)

        payload: dict[str, Any] = {
            "source": "ecmwf_cams_wms",
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
        }
        errors: list[str] = []

        for key, (result, err) in zip(layer_map.keys(), results):
            if isinstance(result, dict):
                payload[key] = result
            if err is not None:
                errors.append(str(err))

        if not any(key in payload for key in layer_map):
            return None, "; ".join(errors) if errors else "smoke_tiles_unavailable"
        return payload, "; ".join(errors) if errors else None

    async def _async_fetch_cmems_featureinfo(
        self,
        *,
        layer: str,
        style: str,
        latitude: float,
        longitude: float,
        zoom: int = 6,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch numeric CMEMS value via WMTS GetFeatureInfo."""
        col, row, pixel_x, pixel_y = _geo_to_wmts_tile(
            latitude,
            longitude,
            zoom=zoom,
        )
        params = {
            "SERVICE": "WMTS",
            "REQUEST": "GetFeatureInfo",
            "VERSION": "1.0.0",
            "LAYER": layer,
            "tilematrixset": "EPSG:3857",
            "tilematrix": zoom,
            "tilerow": row,
            "tilecol": col,
            "i": pixel_x,
            "j": pixel_y,
            "INFOFORMAT": "application/json",
            "STYLE": style,
        }
        url = _build_url(_CMEMS_WMTS, params)
        payload, error = await self._async_fetch_json(url)
        if not isinstance(payload, dict):
            return None, error or f"{layer}:request_failed"

        features = payload.get("features")
        if not isinstance(features, list) or not features:
            return None, f"{layer}:no_features"
        first = features[0]
        if not isinstance(first, dict):
            return None, f"{layer}:invalid_feature"

        properties = first.get("properties")
        if not isinstance(properties, dict):
            return None, f"{layer}:missing_properties"

        geometry = first.get("geometry")
        geom_coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None
        lat_resolved: float | None = _optional_float(properties.get("lat"), 6)
        lon_resolved: float | None = _optional_float(properties.get("lon"), 6)
        if (
            (lat_resolved is None or lon_resolved is None)
            and isinstance(geom_coordinates, list)
            and len(geom_coordinates) >= 2
        ):
            lat_candidate = _optional_float(geom_coordinates[0], 6)
            lon_candidate = _optional_float(geom_coordinates[1], 6)
            if lat_resolved is None:
                lat_resolved = lat_candidate
            if lon_resolved is None:
                lon_resolved = lon_candidate

        return (
            {
                "layer": layer,
                "style": style,
                "dataset_id": properties.get("datasetId"),
                "variable_id": properties.get("variableId"),
                "value": _optional_float(properties.get("value"), 6),
                "unit": properties.get("units"),
                "grid_lat": lat_resolved,
                "grid_lon": lon_resolved,
                "source": "copernicus_marine_wmts",
            },
            None,
        )

    async def _async_fetch_algae_tile_data(
        self,
        *,
        latitude: float,
        longitude: float,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch chlorophyll value from Copernicus OceanColour tiles."""
        # Probe nearby points to handle inland homes while still using the same source.
        probes = [
            (0.0, 0.0),
            (0.06, 0.0),
            (-0.06, 0.0),
            (0.0, 0.06),
            (0.0, -0.06),
            (0.12, 0.0),
            (-0.12, 0.0),
            (0.0, 0.12),
            (0.0, -0.12),
        ]
        errors: list[str] = []

        for delta_lat, delta_lon in probes:
            probe_lat = latitude + delta_lat
            probe_lon = longitude + delta_lon
            result, err = await self._async_fetch_cmems_featureinfo(
                layer=_CMEMS_ALGAE_LAYER,
                style=_CMEMS_ALGAE_STYLE,
                latitude=probe_lat,
                longitude=probe_lon,
                zoom=6,
            )
            if err is not None:
                errors.append(str(err))
                continue
            if not isinstance(result, dict):
                continue
            value = _optional_float(result.get("value"), 6)
            if value is None:
                continue
            payload = dict(result)
            payload["probe_latitude"] = round(probe_lat, 6)
            payload["probe_longitude"] = round(probe_lon, 6)
            payload["probe_distance_km"] = round(
                _haversine_km(latitude, longitude, probe_lat, probe_lon),
                2,
            )
            payload["source"] = "copernicus_oceancolour_wmts"
            return payload, "; ".join(errors) if errors else None

        return None, "; ".join(errors) if errors else "algae_tiles_unavailable"

    async def _async_fetch_earthquake_data(
        self, *, latitude: float, longitude: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch recent earthquake activity around home point from USGS."""
        now = datetime.now(tz=UTC)
        start_24h = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
        start_7d = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        common = {
            "format": "geojson",
            "latitude": f"{latitude:.6f}",
            "longitude": f"{longitude:.6f}",
            "maxradiuskm": 700,
            "orderby": "time",
            "limit": 200,
        }
        url_24h = _build_url(
            _USGS_EQ_QUERY,
            {
                **common,
                "starttime": start_24h,
                "endtime": end_time,
            },
        )
        url_7d = _build_url(
            _USGS_EQ_QUERY,
            {
                **common,
                "starttime": start_7d,
                "endtime": end_time,
            },
        )
        (data_24h, err_24h), (data_7d, err_7d) = await asyncio.gather(
            self._async_fetch_json(url_24h),
            self._async_fetch_json(url_7d),
        )
        if not isinstance(data_24h, dict) and not isinstance(data_7d, dict):
            return None, err_24h or err_7d or "earthquake_api_unavailable"

        features_24h = data_24h.get("features", []) if isinstance(data_24h, dict) else []
        features_7d = data_7d.get("features", []) if isinstance(data_7d, dict) else []
        if not isinstance(features_24h, list):
            features_24h = []
        if not isinstance(features_7d, list):
            features_7d = []

        count_24h = _safe_int(
            data_24h.get("metadata", {}).get("count") if isinstance(data_24h, dict) else len(features_24h),
            len(features_24h),
        )
        count_7d = _safe_int(
            data_7d.get("metadata", {}).get("count") if isinstance(data_7d, dict) else len(features_7d),
            len(features_7d),
        )

        max_mag_7d: float | None = None
        nearest_dist_km: float | None = None
        nearest_mag: float | None = None
        nearest_url: str | None = None
        latest_time_ms: int | None = None
        latest_place: str | None = None

        for feature in features_7d:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties")
            geometry = feature.get("geometry")
            if not isinstance(properties, dict):
                continue
            mag = _optional_float(properties.get("mag"), 1)
            if mag is not None and (max_mag_7d is None or mag > max_mag_7d):
                max_mag_7d = mag

            raw_time = properties.get("time")
            if isinstance(raw_time, (int, float)):
                ts = int(raw_time)
                if latest_time_ms is None or ts > latest_time_ms:
                    latest_time_ms = ts
                    latest_place = str(properties.get("place") or "unknown")

            if not isinstance(geometry, dict):
                continue
            coordinates = geometry.get("coordinates")
            if not isinstance(coordinates, list) or len(coordinates) < 2:
                continue
            ev_lon = _optional_float(coordinates[0])
            ev_lat = _optional_float(coordinates[1])
            if ev_lon is None or ev_lat is None:
                continue
            dist_km = _haversine_km(latitude, longitude, ev_lat, ev_lon)
            if nearest_dist_km is None or dist_km < nearest_dist_km:
                nearest_dist_km = round(dist_km, 1)
                nearest_mag = mag
                nearest_url = properties.get("url")

        tsunami_24h = 0
        for feature in features_24h:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                continue
            tsunami_flag = _safe_int(properties.get("tsunami"), 0)
            if tsunami_flag == 1:
                tsunami_24h += 1

        latest_iso = "unknown"
        if latest_time_ms is not None:
            latest_iso = datetime.fromtimestamp(latest_time_ms / 1000, tz=UTC).isoformat()

        partial_errors = [err for err in (err_24h, err_7d) if err is not None]
        error_text = "; ".join(partial_errors) if partial_errors else None
        return (
            {
                "count_24h": count_24h,
                "count_7d": count_7d,
                "max_mag_7d": max_mag_7d,
                "nearest_distance_km": nearest_dist_km,
                "nearest_magnitude": nearest_mag,
                "nearest_event_url": nearest_url,
                "latest_time": latest_iso,
                "latest_place": latest_place or "unknown",
                "tsunami_events_24h": tsunami_24h,
            },
            error_text,
        )

    async def _async_fetch_gdacs_events(self) -> tuple[list[dict[str, Any]] | None, str | None]:
        """Fetch GDACS events feed and parse current event metadata."""
        xml_text, xml_err = await self._async_fetch_text(_GDACS_RSS)
        if not isinstance(xml_text, str):
            return None, xml_err or "gdacs_feed_unavailable"

        ns = {
            "gdacs": "http://www.gdacs.org",
            "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
            "georss": "http://www.georss.org/georss",
        }
        try:
            root = ET.fromstring(xml_text.lstrip("\ufeff\r\n\t "))
        except ET.ParseError as err:
            return None, f"xml_parse_error:{err}"

        events: list[dict[str, Any]] = []
        for item in root.findall("./channel/item"):
            title = str(item.findtext("title", default="")).strip()
            link = str(item.findtext("link", default="")).strip()
            pub_date_raw = str(item.findtext("pubDate", default="")).strip()
            event_type = str(item.findtext("gdacs:eventtype", default="", namespaces=ns)).strip().upper()
            alert_level = str(item.findtext("gdacs:alertlevel", default="", namespaces=ns)).strip().lower()
            country = str(item.findtext("gdacs:country", default="", namespaces=ns)).strip()
            icon_url = str(item.findtext("gdacs:icon", default="", namespaces=ns)).strip()
            severity = str(item.findtext("gdacs:severity", default="", namespaces=ns)).strip()
            is_current = str(
                item.findtext("gdacs:iscurrent", default="false", namespaces=ns)
            ).strip().lower() == "true"

            pub_iso = None
            pub_ts = 0
            if pub_date_raw:
                try:
                    parsed = parsedate_to_datetime(pub_date_raw)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    parsed = parsed.astimezone(UTC)
                    pub_iso = parsed.isoformat()
                    pub_ts = int(parsed.timestamp())
                except (TypeError, ValueError, OverflowError):
                    pub_iso = None
                    pub_ts = 0

            lat = None
            lon = None
            point = str(item.findtext("georss:point", default="", namespaces=ns)).strip()
            if point:
                parts = [part for part in point.split(" ") if part]
                if len(parts) >= 2:
                    lat = _optional_float(parts[0], 4)
                    lon = _optional_float(parts[1], 4)
            if lat is None or lon is None:
                lat = _optional_float(item.findtext("geo:Point/geo:lat", default="", namespaces=ns), 4)
                lon = _optional_float(item.findtext("geo:Point/geo:long", default="", namespaces=ns), 4)

            if not event_type:
                continue

            events.append(
                {
                    "event_type": event_type,
                    "alert_level": alert_level if alert_level else "unknown",
                    "is_current": is_current,
                    "title": title or "unknown",
                    "country": country or "unknown",
                    "link": link or None,
                    "icon_url": icon_url or None,
                    "severity": severity or None,
                    "latitude": lat,
                    "longitude": lon,
                    "published_at": pub_iso,
                    "published_ts": pub_ts,
                }
            )

        return events, None

    async def _async_fetch_cap_alerts(
        self,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch Meteoalarm CAP-like warning feed (Spain) and aggregate active alerts."""
        xml_text, xml_err = await self._async_fetch_text(_METEOALARM_ATOM_SPAIN)
        if not isinstance(xml_text, str):
            return None, xml_err or "cap_feed_unavailable"

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "cap": "urn:oasis:names:tc:emergency:cap:1.2",
        }
        try:
            root = ET.fromstring(xml_text.lstrip("\ufeff\r\n\t "))
        except ET.ParseError as err:
            return None, f"xml_parse_error:{err}"

        now_utc = datetime.now(tz=UTC)
        entries = root.findall("./atom:entry", ns)

        severity_rank = {
            "extreme": 4,
            "severe": 3,
            "moderate": 2,
            "minor": 1,
            "unknown": 0,
        }

        warnings: list[dict[str, Any]] = []
        for entry in entries:
            severity = str(entry.findtext("cap:severity", default="", namespaces=ns)).strip().lower()
            if not severity:
                severity = "unknown"
            event = str(entry.findtext("cap:event", default="", namespaces=ns)).strip() or "unknown"
            area = str(entry.findtext("cap:areaDesc", default="", namespaces=ns)).strip() or "unknown"
            certainty = (
                str(entry.findtext("cap:certainty", default="", namespaces=ns)).strip() or "unknown"
            )
            urgency = str(entry.findtext("cap:urgency", default="", namespaces=ns)).strip() or "unknown"
            status = str(entry.findtext("cap:status", default="", namespaces=ns)).strip() or "unknown"
            link_elem = entry.find("atom:link", ns)
            link = ""
            if link_elem is not None:
                link = str(link_elem.attrib.get("href", "")).strip()

            expires_raw = str(entry.findtext("cap:expires", default="", namespaces=ns)).strip()
            sent_raw = str(entry.findtext("cap:sent", default="", namespaces=ns)).strip()

            expires_at: datetime | None = None
            sent_at: datetime | None = None
            if expires_raw:
                parsed = dt_util.parse_datetime(expires_raw)
                if parsed is not None:
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    expires_at = parsed.astimezone(UTC)
            if sent_raw:
                parsed = dt_util.parse_datetime(sent_raw)
                if parsed is not None:
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    sent_at = parsed.astimezone(UTC)

            if expires_at is not None and expires_at < now_utc:
                continue

            warnings.append(
                {
                    "severity": severity,
                    "severity_rank": severity_rank.get(severity, 0),
                    "event": event,
                    "area": area,
                    "certainty": certainty,
                    "urgency": urgency,
                    "status": status,
                    "link": link if link else None,
                    "expires_at": expires_at.isoformat() if expires_at is not None else None,
                    "expires_ts": int(expires_at.timestamp()) if expires_at is not None else 0,
                    "sent_at": sent_at.isoformat() if sent_at is not None else None,
                    "sent_ts": int(sent_at.timestamp()) if sent_at is not None else 0,
                }
            )

        active_count = len(warnings)
        highest_severity = "unknown"
        cap_index = 0
        top_event = "none"
        top_area = "none"
        top_expires = "unknown"
        top_link: str | None = None

        if warnings:
            top = max(
                warnings,
                key=lambda item: (
                    _safe_int(item.get("severity_rank"), 0),
                    _safe_int(item.get("sent_ts"), 0),
                ),
            )
            highest_severity = str(top.get("severity") or "unknown")
            top_event = str(top.get("event") or "unknown")
            top_area = str(top.get("area") or "unknown")
            top_expires = str(top.get("expires_at") or "unknown")
            top_link = top.get("link")
            cap_index = min(
                100,
                max(
                    0,
                    _safe_int(top.get("severity_rank"), 0) * 22 + min(active_count, 10) * 6,
                ),
            )

        return (
            {
                "active_count": active_count,
                "highest_severity": highest_severity,
                "index": cap_index,
                "top_event": top_event,
                "top_area": top_area,
                "top_expires": top_expires,
                "top_link": top_link,
            },
            None,
        )

    async def _async_fetch_jellyfish_data(
        self, *, latitude: float, longitude: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch nearest-beach jellyfish data from PlatgesCat."""
        front_data, front_err = await self._async_fetch_json(_PLATGESCAT_FRONT)
        if not isinstance(front_data, dict):
            return None, front_err or "front_unavailable"

        beaches = front_data.get("playas")
        if not isinstance(beaches, list) or not beaches:
            return None, "no_beaches_in_front_payload"

        nearest: dict[str, Any] | None = None
        nearest_dist_km = 10_000.0
        for beach in beaches:
            if not isinstance(beach, dict):
                continue
            lat = _safe_float(beach.get("latitud"), math.nan)
            lon = _safe_float(beach.get("longitud"), math.nan)
            if math.isnan(lat) or math.isnan(lon):
                continue
            dist_km = _haversine_km(latitude, longitude, lat, lon)
            if dist_km < nearest_dist_km:
                nearest = beach
                nearest_dist_km = dist_km

        if nearest is None:
            return None, "no_nearest_beach"

        detail_data: dict[str, Any] | None = None
        detail_err: str | None = None
        beach_id = nearest.get("id")
        if isinstance(beach_id, int):
            detail_url = f"{_PLATGESCAT_DETAIL_BASE}{beach_id}"
            detail_data, detail_err = await self._async_fetch_json(detail_url)

        result: dict[str, Any] = {
            "beach_id": nearest.get("id"),
            "beach_name": nearest.get("nombre"),
            "beach_municipality": nearest.get("municipio"),
            "distance_km": round(nearest_dist_km, 2),
            "lat": _safe_float(nearest.get("latitud"), latitude),
            "lon": _safe_float(nearest.get("longitud"), longitude),
            "front_medusa_tag": nearest.get("medusaetiqueta"),
            "front_medusa_label": nearest.get("medusasliteral"),
            "front_water_quality_tag": nearest.get("calidadaguaetiqueta"),
            "front_water_temp": _safe_float(nearest.get("temperaturaagua"), 0.0),
        }

        items = detail_data.get("items", {}) if isinstance(detail_data, dict) else {}
        if isinstance(items, dict):
            medusas = items.get("medusas")
            if isinstance(medusas, dict):
                result["status_label"] = medusas.get("peligrosidadTrad")
                result["status_tag"] = medusas.get("peligrosidadEtiqueta")
                result["status_icon"] = medusas.get("icono")
                result["species_list"] = (
                    medusas.get("llistatMeduses")
                    if isinstance(medusas.get("llistatMeduses"), list)
                    else []
                )
                fecha_mod = medusas.get("fechaModificacion")
                if isinstance(fecha_mod, dict):
                    result["last_update"] = fecha_mod.get("date")
                elif isinstance(fecha_mod, str):
                    result["last_update"] = fecha_mod

            quality = items.get("calidadPlaya")
            if isinstance(quality, dict):
                result["water_quality"] = quality.get("estado")
                result["water_quality_tag"] = quality.get("estado_etiqueta")

            state = items.get("estadoPlaya")
            if isinstance(state, dict):
                result["water_temp_c"] = _safe_float(
                    state.get("temperaturaAgua"), result["front_water_temp"]
                )
                result["sky_text"] = state.get("traduccionCielo")

            sea = items.get("estadoMar")
            if isinstance(sea, dict):
                result["wave_height"] = _safe_float(sea.get("alturaolas"), 0.0)
                result["wind_speed"] = _safe_float(sea.get("velocidadviento"), 0.0)

            result["off_season"] = bool(items.get("foraTemporada"))

        if detail_err is not None:
            return result, f"detail_partial:{detail_err}"
        return result, None

    async def _async_fetch_tiger_mosquito_data(
        self, *, latitude: float, longitude: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch tiger mosquito observations from Mosquito Alert API."""
        now = datetime.now(tz=UTC)
        after_180 = (now - timedelta(days=180)).isoformat().replace("+00:00", "Z")
        after_30 = (now - timedelta(days=30)).isoformat().replace("+00:00", "Z")
        point = f"{longitude:.6f},{latitude:.6f}"

        common_params = {
            "point": point,
            "dist": 20_000,
            "identification_taxon_ids": str(_TIGER_MOSQUITO_TAXON_ID),
            "order_by": "-received_at",
        }
        url_180 = _build_url(
            _MOSQUITO_ALERT_OBSERVATIONS,
            {
                **common_params,
                "received_at_after": after_180,
                "page_size": 200,
            },
        )
        url_30 = _build_url(
            _MOSQUITO_ALERT_OBSERVATIONS,
            {
                **common_params,
                "received_at_after": after_30,
                "page_size": 1,
            },
        )

        (data_180, err_180), (data_30, err_30) = await asyncio.gather(
            self._async_fetch_json(url_180),
            self._async_fetch_json(url_30),
        )

        if not isinstance(data_180, dict) and not isinstance(data_30, dict):
            return None, err_180 or err_30 or "mosquito_api_unavailable"

        results_180 = data_180.get("results", []) if isinstance(data_180, dict) else []
        if not isinstance(results_180, list):
            results_180 = []

        count_180 = _safe_int(
            data_180.get("count") if isinstance(data_180, dict) else len(results_180),
            len(results_180),
        )
        count_30 = _safe_int(
            data_30.get("count") if isinstance(data_30, dict) else 0,
            0,
        )

        high_confidence = 0
        confidence_sum = 0.0
        confidence_count = 0
        latest_received_at: datetime | None = None
        latest_uuid: str | None = None
        icon_url: str | None = None

        for row in results_180:
            if not isinstance(row, dict):
                continue
            received_raw = row.get("received_at") or row.get("created_at")
            if isinstance(received_raw, str):
                parsed = dt_util.parse_datetime(received_raw)
                if parsed is not None:
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=UTC)
                    if latest_received_at is None or parsed > latest_received_at:
                        latest_received_at = parsed
                        latest_uuid = row.get("uuid")

            ident = row.get("identification")
            result = ident.get("result") if isinstance(ident, dict) else {}
            if isinstance(result, dict):
                if result.get("is_high_confidence") is True:
                    high_confidence += 1
                confidence = result.get("confidence")
                if confidence is not None:
                    confidence_sum += _safe_float(confidence, 0.0)
                    confidence_count += 1

            if icon_url is None:
                if isinstance(ident, dict):
                    ident_photo = ident.get("photo")
                    if isinstance(ident_photo, dict):
                        candidate = ident_photo.get("url")
                        if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                            icon_url = candidate
                if icon_url is None:
                    photos = row.get("photos")
                    if isinstance(photos, list):
                        for photo in photos:
                            if not isinstance(photo, dict):
                                continue
                            candidate = photo.get("url")
                            if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                                icon_url = candidate
                                break

        high_conf_pct = 0
        if results_180:
            high_conf_pct = int(round((high_confidence / len(results_180)) * 100))
        confidence_avg = 0
        if confidence_count > 0:
            confidence_avg = int(round((confidence_sum / confidence_count) * 100))

        latest_iso: str | None = None
        latest_days_ago = 999
        if latest_received_at is not None:
            latest_iso = latest_received_at.astimezone(UTC).isoformat()
            latest_days_ago = max(0, int((now - latest_received_at).total_seconds() / 86_400))

        partial_errors = [err for err in (err_180, err_30) if err is not None]
        error_text = "; ".join(partial_errors) if partial_errors else None

        return (
            {
                "count_30d": count_30,
                "count_180d": count_180,
                "high_confidence_pct": high_conf_pct,
                "confidence_avg_pct": confidence_avg,
                "latest_received_at": latest_iso,
                "latest_days_ago": latest_days_ago,
                "latest_uuid": latest_uuid,
                "icon_url": icon_url,
            },
            error_text,
        )

    async def _async_fetch_tick_data(
        self, *, latitude: float, longitude: float
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Fetch tick observations around home point from iNaturalist API."""
        now = datetime.now(tz=UTC)
        d1_180 = (now - timedelta(days=180)).strftime("%Y-%m-%d")
        d1_30 = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        common = {
            "lat": f"{latitude:.6f}",
            "lng": f"{longitude:.6f}",
            "radius": 50,
            "taxon_id": _INAT_TICKS_TAXON_ID,
            "order_by": "observed_on",
            "order": "desc",
        }
        url_180 = _build_url(
            _INAT_OBSERVATIONS,
            {
                **common,
                "d1": d1_180,
                "per_page": 200,
            },
        )
        url_30 = _build_url(
            _INAT_OBSERVATIONS,
            {
                **common,
                "d1": d1_30,
                "per_page": 1,
            },
        )
        (data_180, err_180), (data_30, err_30) = await asyncio.gather(
            self._async_fetch_json(url_180),
            self._async_fetch_json(url_30),
        )
        if not isinstance(data_180, dict) and not isinstance(data_30, dict):
            return None, err_180 or err_30 or "ticks_api_unavailable"

        results_180 = data_180.get("results", []) if isinstance(data_180, dict) else []
        if not isinstance(results_180, list):
            results_180 = []

        count_180 = _safe_int(
            data_180.get("total_results") if isinstance(data_180, dict) else len(results_180),
            len(results_180),
        )
        count_30 = _safe_int(
            data_30.get("total_results") if isinstance(data_30, dict) else 0,
            0,
        )

        latest_observed = None
        research_count = 0
        needs_id_count = 0
        icon_url = None
        taxon_name = None
        common_name = None

        for row in results_180:
            if not isinstance(row, dict):
                continue
            observed_on = row.get("observed_on")
            if isinstance(observed_on, str):
                parsed = dt_util.parse_datetime(f"{observed_on}T00:00:00+00:00")
                if parsed is not None and (latest_observed is None or parsed > latest_observed):
                    latest_observed = parsed

            quality_grade = str(row.get("quality_grade") or "").lower()
            if quality_grade == "research":
                research_count += 1
            elif quality_grade == "needs_id":
                needs_id_count += 1

            taxon = row.get("taxon")
            if isinstance(taxon, dict):
                if taxon_name is None:
                    taxon_name = taxon.get("name")
                if common_name is None:
                    common_name = taxon.get("preferred_common_name")
                if icon_url is None:
                    photo = taxon.get("default_photo")
                    if isinstance(photo, dict):
                        icon_url = photo.get("square_url") or photo.get("small_url")

        latest_iso = latest_observed.isoformat() if latest_observed is not None else None
        latest_days_ago = 999
        if latest_observed is not None:
            latest_days_ago = max(0, int((now - latest_observed).total_seconds() / 86_400))

        total_quality = research_count + needs_id_count
        research_pct = int(round((research_count / total_quality) * 100)) if total_quality > 0 else 0

        partial_errors = [err for err in (err_180, err_30) if err is not None]
        error_text = "; ".join(partial_errors) if partial_errors else None

        return (
            {
                "count_30d": count_30,
                "count_180d": count_180,
                "latest_observed_at": latest_iso,
                "latest_days_ago": latest_days_ago,
                "research_pct": research_pct,
                "taxon_name": taxon_name,
                "common_name": common_name,
                "icon_url": icon_url,
            },
            error_text,
        )

