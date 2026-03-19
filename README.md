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
- Calculates rip current risk from wave/period/wind/rain
- Calculates heat stress index + wet-bulb estimate
- Supports persona profiles from YAML (`skin_type`, `spf`, sensitivities) with per-person sunburn/heat sensors
- Adds persona `daily_plan` with `planner_mode` (`normal`, `child`, `elderly`, `sport`, `beach_day`)
- Adds smart planner sensors: best outdoor/beach hours, now-vs-2..3h trend, beach pack list and notification hints
- Adds UV dose/SED tracking by HA entities (`person`/`device_tracker`) + extra configured trackers
- Adds WBGT + dehydration index
- Adds thunderstorm risk + 3h nowcast
- Adds tide/current metrics from Open-Meteo Marine (`sea_level_height_msl`, `ocean_current_velocity`)
- Adds algae bloom proxy risk from sea state + official water quality
- Adds smoke transport proxy risk from wildfire proximity + AQI/PM2.5 + wind
- Adds CAP civil warning summary from Meteoalarm Atom feed (Spain)
- Adds unified bite index (mosquito + tick + weather) + 3-day outlook
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
    "personas": [
      {
        "id": "mama",
        "name": "Mama",
        "person_entity_id": "person.mama",
        "skin_type": 2,
        "spf": 30.0,
        "shade_factor": 1.0,
        "uv_sensitivity": 1.1,
        "heat_sensitivity": 1.0,
        "planner_mode": "child",
        "enabled": true
      }
    ],
    "daily_plan": {
      "enabled": true,
      "default_mode": "normal",
      "comparison_hours": 3
    },
    "fetch": {
      "weather": "ok",
      "marine": "ok",
      "air_quality": "ok",
      "jellyfish": "ok",
      "tiger_mosquito": "ok",
      "ticks": "ok",
      "earthquakes": "ok",
      "gdacs": "ok",
      "cap": "ok"
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
  daily_plan: true
  planner_mode: normal
  tracking_entities:
    - id: avm_phone
      entity_id: person.aleksandr_meshcheriakov
      uv_exposure_factor: 1.0
    - id: vem_phone
      entity_id: person.victoria_meshchryakovf
      uv_exposure_factor: 1.0
  personas:
    - id: vem
      name: VEM
      person_entity_id: person.victoria_meshchryakovf
      tracker_entity_id: person.victoria_meshchryakovf
      skin_type: 2
      planner_mode: normal
      uv_exposure_factor: 1.0
      spf: 30
    - id: avm
      name: AVM
      person_entity_id: person.aleksandr_meshcheriakov
      tracker_entity_id: person.aleksandr_meshcheriakov
      skin_type: 3
      planner_mode: sport
      uv_exposure_factor: 1.15
      spf: 15
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

Personas options:

- `skin_type`: 1..6 (Fitzpatrick scale)
- `spf`: sunscreen factor (minimum is `1`, means no extra protection)
- `shade_factor`: extra protection from shade/clothes (`1.0` default, `>1` more protection)
- `uv_sensitivity`: UV sensitivity multiplier (`>1` burns faster, `<1` slower)
- `heat_sensitivity`: heat stress multiplier (`>1` more sensitive)
- `planner_mode`: `normal`, `child`, `elderly`, `sport`, `beach_day`
- `tracker_entity_id`: optional HA entity (`person.*` or `device_tracker.*`) for UV dose tracking
- `uv_exposure_factor`: UV exposure multiplier for tracker dose accumulation (`0..2.5`)

Planner options:

- `daily_plan`: enable planner logic (`true` by default)
- `daly_plan`: alias of `daily_plan` (for backward typo compatibility)
- `planner_mode`: global default mode for personas without own mode
- `tracking_entities`: extra HA entities for UV dose tracking (list of strings or dict with `id`, `entity_id`, `uv_exposure_factor`)
- `uv_tracking_entities`: alias for `tracking_entities`

`skin_type` reference:

- `1`: very fair skin, almost always burns, never tans
- `2`: fair skin, usually burns, tans minimally
- `3`: medium/light-brown skin, sometimes mild burn, gradually tans
- `4`: olive/light-brown skin, rarely burns, tans easily
- `5`: brown skin, very rarely burns, tans very easily
- `6`: dark-brown/black skin, almost never burns

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
