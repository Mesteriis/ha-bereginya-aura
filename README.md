# Beregynya AURA

Custom Home Assistant integration + Lovelace card.

The card uses an internal API endpoint and does not require existing HA weather
entities. It can optionally reuse selected HA entities in `hybrid` mode.

## What it does

- Serves own API: `/api/bereginya_aura/v1/snapshot`
- Pulls core data from Open-Meteo directly (weather, marine, air quality, pollen, dust)
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
  frontend/bereginya-aura-card.js
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
      "air_quality": "ok"
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
      "source": "internal_api"
    }
  ],
  "forecast_daily": [
    {
      "date": "2026-03-20",
      "temp_min": 12.3,
      "temp_max": 19.4,
      "rain_probability_max": 35,
      "rain_sum_mm": 1.1,
      "uv_max": 5.7,
      "sea_temp_avg": 14.8,
      "aqi_max": 42,
      "allergy_index": 31,
      "asthma_risk": "low",
      "beach_score": 7
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
  sources:
    precipitation_probability: sensor.precipitation_probability
    uv_index: sensor.uv_index
    sea_temperature: sensor.sea_temperature_openmeteo
    wave_period: sensor.wave_period
    aqi: sensor.air_quality_european_aqi
    pollen_total: sensor.pollen_total
    pollen_ambrosia: sensor.pollen_ragweed
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
```

Card renders markdown transcript with source markers for each metric.

## Service

Force refresh cache:

- Service: `bereginya_aura.refresh_snapshot`

## Install (manual HACS flow)

1. Add repository as custom integration in HACS.
2. Install integration.
3. Add `bereginya_aura:` block to `configuration.yaml`.
4. Restart Home Assistant.
5. Add `custom:bereginya-aura` card to dashboard.
