# Beregynya AURA

Custom Home Assistant integration + Lovelace card.

The card uses an internal API endpoint and does not require existing HA weather
entities. It can optionally reuse selected HA entities in `hybrid` mode.

## What it does

- Serves own API: `/api/bereginya_aura/v1/snapshot`
- Uses persistent file cache in `.storage/bereginya_aura_snapshot.json` for fast startup after HA restart
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
- Adds astro-risk layer: UV from solar angle + cloud attenuation for now/+3h
- Adds WBGT + dehydration index
- Adds thunderstorm risk + 3h nowcast
- Adds tide/current metrics from Open-Meteo Marine (`sea_level_height_msl`, `ocean_current_velocity`)
- Adds algae bloom index from Copernicus Marine OceanColour WMTS (`GetFeatureInfo`, numeric CHL)
- Adds smoke transport index from ECMWF CAMS WMS (`GetFeatureInfo`, numeric bbaod/pm2.5/fire)
- Adds CAP civil warning summary from Meteoalarm Atom feed (Spain)
- Adds unified bite index (mosquito + tick + weather) + 3-day outlook
- Exposes icon catalog for all metrics in snapshot `meta.icons.entities`
- Adds `icon_url` + `icon_gif_url` for each entity (GIF preferred support)
- Supports extra timezone clocks via `timezones: "UTC+01,UTC+03,UTC-05"`
- Adds config flags `debug` and `public_sensor`
- If `public_sensor: true`, publishes snapshot metrics as `sensor.bereginya_aura_*`
- No synthetic substitute values: if upstream data is missing, metrics are `unavailable`
- Calculates derived metrics internally (weather summary, beach indexes, recommendation)
- Uses only HA home position (`latitude`, `longitude`, `elevation`, `timezone`) as base input
- Optionally overrides selected metrics from HA entities via mapping

## Unified sensor categories (5)

To keep dashboards and automations simple, all AURA sensors are grouped into 5 top-level categories:

- `sea_beach`: sea and beach safety
  Sensors: `sensor.sea_temperature_*`, `sensor.wave_*`, `sensor.beach_*`, `sensor.jellyfish_*`, `sensor.rip_current_*`, `sensor.tide_*`, `sensor.ocean_current_*`, `sensor.current_risk`, `sensor.algae_*`
- `bio_allergy`: allergens and biological bite risks
  Sensors: `sensor.pollen_*`, `sensor.ambrosia_risk`, `sensor.allergy_index`, `sensor.asthma_risk`, `sensor.tiger_mosquito_*`, `sensor.mosquito_index`, `sensor.tick_*`, `sensor.bite_*`
- `climate_stress`: UV/heat/hydration/air/smoke stress
  Sensors: `sensor.uv_dose_*`, `sensor.astro_uv_*`, `sensor.astro_solar_elevation`, `sensor.heat_*`, `sensor.wbgt_c`, `sensor.dehydration_*`, `sensor.thunderstorm_*`, `sensor.air_quality_*`, `sensor.saharan_dust_*`, `sensor.smoke_*`
- `hazards_alerts`: earthquakes, wildfire, civil alerts
  Sensors: `sensor.earthquake_*`, `sensor.wildfire_*`, `sensor.hazard_*`, `sensor.cap_*`
- `planner_personal`: personal planner and persona outputs
  Sensors: `sensor.aura_*`, `sensor.aura_tracker_*`, `sensor.aura_{persona}_*` (daily plan, now-vs-3h, beach pack, smart notification, personal UV/heat profile)

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
      "cap": "ok",
      "algae_tiles": "ok",
      "smoke_tiles": "ok"
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
  debug: false
  public_sensor: false
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
- `debug`: reserved debug flag (`false` by default)
- `public_sensor`: export all calculated metrics into HA states
  - `true`/`public`: publish as `sensor.bereginya_aura_*`
  - `false`/`private`: keep metrics private to card API only

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

## Architecture

Snapshot runtime is split into focused modules under `custom_components/bereginya_aura/snapshot/`:

- `options.py` normalizes YAML/config-entry options.
- `shared.py` holds generic math, time, icon and transcript helpers.
- `fetchers.py` contains upstream HTTP fetch logic.
- `metrics_external.py` builds weather, marine, pollen, CAP, fire, quake and other external metrics.
- `metrics_persona.py` builds per-person planner, UV dose and exposure metrics.
- `metrics_core.py` assembles final transcript categories, HA publish mode and snapshot extras.
- `provider.py` coordinates cache, refresh lifecycle and final snapshot assembly.

This keeps the public provider surface stable while making the data pipeline easier to change safely.

## Service

Force refresh cache:

- Service: `bereginya_aura.refresh_snapshot`

## Install (manual HACS flow)

1. Add repository as custom integration in HACS.
2. Install integration.
3. Add `bereginya_aura:` block to `configuration.yaml`.
4. Restart Home Assistant.
5. On storage-mode Lovelace, AURA auto-registers its frontend resource in dashboard resources.
6. Add `custom:bereginya-aura` card to dashboard.
7. If the browser still shows an old card state after first install/update, do a hard reload.

## Workspace Flow

In this workspace the live Home Assistant config is the operational source of truth.
`distrib/bereginya-aura` is the public OSS mirror/release repository and must be synced from HA
before PR and release work.

Main flow:

```bash
make diff-ha
make sync-from-ha
make lint
make test
make build
```

## Tests

Integration runtime smoke tests use real Home Assistant runtime and real upstream APIs.
They do not mock external weather/marine/air sources.

```bash
make test
make test-e2e
```

Sync the repository from the live HA runtime copy:

```bash
make diff-ha
make sync-from-ha
```

Install repository contents into a target HA config:

```bash
make install-local
```

Override target config directory if needed:

```bash
make install-local LOCAL_HA_CONFIG=/path/to/ha-config
```

## CI

Repository automation is expected to run through GitHub Actions:

- `ci.yml` validates PRs with lint, artifact checks, and frontend build
- `release.yml` packages the repository for tagged releases or manual release runs
