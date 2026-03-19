# Beregynya AURA

Custom Home Assistant integration + Lovelace card.

The card uses an internal API endpoint and does not require existing HA weather
entities. It can optionally reuse selected HA entities in `hybrid` mode.

## What it does

- Serves own API: `/api/bereginya_aura/v1/snapshot`
- Pulls core data from Open-Meteo directly (weather, marine, air quality, pollen, dust)
- Pulls official jellyfish/beach state for nearest beach from PlatgesCat (ACA)
- Pulls tiger mosquito observations around home point from Mosquito Alert API
- Pulls tick observations around home point from iNaturalist API
- Pulls local earthquake activity around home point from USGS Earthquake Catalog API
- Pulls global wildfire + multi-hazard events from GDACS RSS feed
- Exposes icon catalog for all metrics in snapshot `meta.icons.entities`
- Adds `icon_url` + `icon_gif_url` for each entity (GIF preferred support)
- Supports extra timezone clocks via `timezones: "UTC+01,UTC+03,UTC-05"`
- No synthetic substitute values: if upstream data is missing, metrics are `unavailable`
- Calculates derived metrics internally (weather summary, beach indexes, recommendation)
- Uses only HA home position (`latitude`, `longitude`, `elevation`, `timezone`) as base input
- Optionally overrides selected metrics from HA entities via mapping

## Repository layout

```text
custom_components/bereginya_aura/
  __init__.py
  manifest.json
  const.py
  api.py
  provider.py
  frontend/bereginya-aura-card.ts
  frontend/bereginya-aura-card.js
  frontend/bereginya-aura-card.js.gz
hacs.json
```

## API

- Endpoint: `GET /api/bereginya_aura/v1/snapshot`
- Auth: Home Assistant authenticated API
- Query params:
  - `force_refresh=1` to bypass cache

Response:

```json
{
  "meta": {
    "source": "bereginya_aura_internal_api",
    "source_mode": "internal",
    "refresh_seconds": 900,
    "forecast_days": 7,
    "generated_at": "2026-03-19T20:00:00+00:00",
    "home_position": {
      "latitude": 41.123456,
      "longitude": 2.123456,
      "elevation_m": 10.0,
      "timezone": "Europe/Madrid"
    },
    "fetch": {
      "weather": "ok",
      "marine": "ok",
      "air_quality": "ok",
      "jellyfish": "ok",
      "tiger_mosquito": "ok",
      "ticks": "ok",
      "earthquakes": "ok",
      "gdacs": "ok"
    },
    "timezones": [
      {"timezone":"UTC+01","time":"22:05"},
      {"timezone":"UTC+03","time":"00:05"},
      {"timezone":"UTC-05","time":"16:05"}
    ],
    "icons": {
      "weather_current": {
        "weather_code": 3,
        "emoji_code": "2601_fe0f",
        "icon_url": "https://fonts.gstatic.com/s/e/notoemoji/latest/2601_fe0f/512.png",
        "icon_gif_url": "https://fonts.gstatic.com/s/e/notoemoji/latest/2601_fe0f/512.gif"
      },
      "entities": {
        "sensor.tiger_mosquito_risk": {
          "icon": "mdi:mosquito",
          "icon_url": "https://fonts.gstatic.com/s/e/notoemoji/latest/1f99f/512.png",
          "icon_gif_url": "https://fonts.gstatic.com/s/e/notoemoji/latest/1f99f/512.gif"
        }
      }
    },
    "ha_overrides": {
      "attempted": 0,
      "applied": 0,
      "missing": 0
    },
    "forecast_count": 7
  },
  "entities": [
    {
      "entity_id": "sensor.sea_temperature_openmeteo",
      "name": "Sea temperature",
      "value": 14.3,
      "unit": "degC",
      "source": "internal_api",
      "icon_url": "https://fonts.gstatic.com/s/e/notoemoji/latest/1f30a/512.png",
      "icon_gif_url": "https://fonts.gstatic.com/s/e/notoemoji/latest/1f30a/512.gif"
    }
  ],
  "forecast_daily": [
    {
      "date": "2026-03-20",
      "temp_min": 12.3,
      "temp_max": 19.4,
      "weather_icon_gif_url": "https://fonts.gstatic.com/s/e/notoemoji/latest/2601_fe0f/512.gif",
      "rain_probability_max": 35,
      "rain_sum_mm": 1.1,
      "uv_max": 5.7,
      "sea_temp_avg": 14.8,
      "aqi_max": 42,
      "allergy_index": 31,
      "asthma_risk": "low",
      "beach_score": 7,
      "mosquito_risk_est": "low",
      "jellyfish_risk_est": "off_season",
      "tick_risk_est": "moderate"
    }
  ]
}
```

## YAML configuration

Minimal:

```yaml
bereginya_aura:
```

Advanced (`hybrid` mode with optional HA sources):

```yaml
bereginya_aura:
  source_mode: hybrid
  refresh_seconds: 600
  forecast_days: 7
  timezones: "UTC+01,UTC+03,UTC-05"
  sources:
    precipitation_probability: sensor.precipitation_probability
    uv_index: sensor.uv_index
    sea_temperature: sensor.sea_temperature_openmeteo
    wave_period: sensor.wave_period
    aqi: sensor.air_quality_european_aqi
    pollen_total: sensor.pollen_total
    pollen_ambrosia: sensor.pollen_ragweed
    jellyfish_risk: sensor.jellyfish_risk
    mosquito_index: sensor.mosquito_index
    tick_risk: sensor.tick_risk
    tick_index: sensor.tick_index
    earthquake_risk: sensor.earthquake_risk
    wildfire_risk: sensor.wildfire_risk
    hazard_top_event_type: sensor.hazard_top_event_type
    beach_comfort_index: sensor.beach_comfort_index
```

Supported `source_mode`:

- `internal`: only internal API data
- `hybrid`: internal data + mapped HA entity overrides
- `ha_only`: only mapped HA values; unmapped metrics become unavailable

## Lovelace card

Card type: `custom:bereginya-aura`

```yaml
type: custom:bereginya-aura
title: Beregynya AURA Transcript
refresh_seconds: 120
force_refresh: false
lang: ru
show_icons: true
prefer_gif_icons: true
```

Card supports languages: `ru` (default), `en`, `ua`, `es`.
Source of truth for frontend is TypeScript (`frontend/bereginya-aura-card.ts`).

## Service

Force refresh cache:

- Service: `bereginya_aura.refresh_snapshot`

## Install (manual HACS flow)

1. Add repository as custom integration in HACS.
2. Install integration.
3. Add `bereginya_aura:` block to `configuration.yaml`.
4. Restart Home Assistant.
5. Add `custom:bereginya-aura` card to dashboard.
