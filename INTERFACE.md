# Beregynya AURA Interface Reference

Этот файл фиксирует внешний контракт интеграции:

- API snapshot: `GET /api/bereginya_aura/v1/snapshot`
- сервис: `bereginya_aura.refresh_snapshot`
- Lovelace card: `type: custom:bereginya-aura`
- публичный экспорт в HA: `sensor.bereginya_aura_*` и `sensor.bereginya_aura_snapshot`

Документ описывает именно интерфейс данных: поля snapshot, формат `entities[]`, `forecast_daily[]`, все фиксированные сенсоры и все динамические семейства сенсоров.

## 1. Surface

### API

- Endpoint: `GET /api/bereginya_aura/v1/snapshot`
- Auth: стандартная авторизация Home Assistant
- Query params:
  - `force_refresh=1`: принудительно обойти кеш и собрать snapshot заново

### Service

- Service: `bereginya_aura.refresh_snapshot`
- Назначение: форсирует refresh внутреннего snapshot cache

### Lovelace card

- Type: `custom:bereginya-aura`
- Источник данных карточки: тот же snapshot API

### Public sensor export

Если `public_sensor: true`, каждая строка из `snapshot.entities[]` публикуется в HA как отдельный state:

- исходный `sensor.weather_summary` превращается в `sensor.bereginya_aura_weather_summary`
- исходный `sensor.aura_beach_pack_trigger` превращается в `sensor.bereginya_aura_aura_beach_pack_trigger`
- дополнительно создается агрегатный `sensor.bereginya_aura_snapshot`

Slug строится из части после `sensor.` с заменой всех не-alnum символов на `_`.

## 2. Snapshot Schema

Ответ API всегда имеет верхний уровень:

```json
{
  "meta": {},
  "entities": [],
  "forecast_daily": []
}
```

### `meta`

| Поле | Тип | Описание |
| --- | --- | --- |
| `source` | `string` | Всегда `bereginya_aura_internal_api` |
| `source_mode` | `string` | `internal`, `hybrid`, `ha_only` |
| `refresh_seconds` | `int` | TTL snapshot cache |
| `forecast_days` | `int` | Сколько дней прогноза собрано |
| `debug` | `bool` | Debug flag интеграции |
| `public_sensor` | `bool|string` | Режим публичного экспорта |
| `generated_at` | `ISO datetime` | Когда snapshot был собран |
| `timezones` | `list[object]` | Подготовленные часы для карточки |
| `home_position.latitude` | `float` | Широта HA home |
| `home_position.longitude` | `float` | Долгота HA home |
| `home_position.elevation_m` | `float` | Высота HA home |
| `home_position.timezone` | `string` | HA timezone |
| `fetch` | `object` | Статус каждого upstream fetch: `ok` или текст ошибки |
| `icons` | `object` | Каталог текущих weather/entity/forecast icon URL |
| `personas` | `list[object]` | Нормализованные persona profiles |
| `daily_plan` | `object` | Planner payload |
| `daly_plan` | `object` | Alias того же payload для backward compatibility |
| `tracking_entities` | `list` | Нормализованные tracking entities |
| `ha_overrides` | `object` | Статистика HA overrides: `attempted`, `applied`, `missing` |
| `forecast_count` | `int` | Размер `forecast_daily` |

### `meta.timezones[]`

| Поле | Тип | Описание |
| --- | --- | --- |
| `timezone` | `string` | Label часовой зоны |
| `date` | `string` | Дата для этой зоны |
| `time` | `string` | Время для этой зоны |
| `iso` | `ISO datetime` | Полный timestamp |

### `meta.fetch`

Ключи:

- `weather`
- `marine`
- `air_quality`
- `jellyfish`
- `tiger_mosquito`
- `ticks`
- `earthquakes`
- `gdacs`
- `cap`
- `algae_tiles`
- `smoke_tiles`

Значение каждого поля:

- `ok`
- или текст ошибки/причины недоступности

### `meta.icons`

| Поле | Тип | Описание |
| --- | --- | --- |
| `weather_current` | `object` | Иконка текущей погоды |
| `entities` | `object` | Каталог иконок по `entity_id` |
| `forecast_daily` | `list[object]` | Иконки forecast rows |

Типичные подполя:

- `icon`
- `icon_emoji`
- `icon_url`
- `icon_webp_url`
- `icon_gif_url`
- `icon_external_url`

### `entities[]`

Каждая строка из `entities[]` описывает одну метрику/сенсор.

| Поле | Тип | Описание |
| --- | --- | --- |
| `entity_id` | `string` | Канонический ID сенсора, например `sensor.uv_index` |
| `name` | `string` | Человеческое имя метрики |
| `value` | `string|number|bool` | Значение |
| `unit` | `string` | Единица измерения, если есть |
| `source` | `string` | Источник: `internal_api`, `internal_model`, `astro_model`, `persona_profile`, `ha_entity`, `ha_tracking` и т.д. |
| `source_entity` | `string` | HA entity, если значение было взято/привязано к HA |
| `icon` | `string` | MDI icon |
| `icon_url` | `string` | PNG icon URL |
| `icon_webp_url` | `string` | WebP icon URL |
| `icon_gif_url` | `string` | GIF icon URL |
| `icon_external_url` | `string` | Внешняя icon/link URL, если есть |
| `...extras` | `any` | Некоторые сенсоры добавляют служебные поля, например planner notification payload |

### `forecast_daily[]`

Каждый объект описывает один день прогноза.

| Поле | Тип | Описание |
| --- | --- | --- |
| `date` | `YYYY-MM-DD` | День прогноза |
| `weather_code` | `int` | Код погоды |
| `temp_min` | `float` | Минимальная температура дня |
| `temp_max` | `float` | Максимальная температура дня |
| `rain_probability_max` | `int` | Максимальная вероятность осадков |
| `rain_sum_mm` | `float` | Суммарные осадки |
| `uv_max` | `float` | Пиковый UV |
| `wind_max_ms` | `float` | Максимальный ветер в `m/s` |
| `wind_max_kmh` | `float` | Максимальный ветер в `km/h` |
| `sea_temp_avg` | `float` | Средняя температура моря |
| `wave_height_max` | `float` | Максимальная высота волны |
| `wave_period_avg` | `float` | Средний wave period |
| `aqi_max` | `int` | Максимальный AQI |
| `dust_max` | `float` | Пиковая dust concentration |
| `pollen_total_est` | `int` | Оценка суммарной пыльцы |
| `allergy_index` | `int 0..100` | Аллергенный индекс |
| `asthma_risk` | `enum` | Риск для астмы |
| `beach_flag` | `green|yellow|red` | Пляжный флаг |
| `beach_score` | `int 0..10` | Итоговый beach score |
| `mosquito_risk_est` | `enum` | Оценка риска москитов |
| `jellyfish_risk_est` | `enum` | Оценка риска медуз |
| `tick_risk_est` | `enum` | Оценка риска клещей |
| `weather_icon_*` | `string` | URL иконок погоды |
| `mosquito_icon_gif_url` | `string` | GIF иконка москитов |
| `jellyfish_icon_gif_url` | `string` | GIF иконка медуз |
| `tick_icon_gif_url` | `string` | GIF иконка клещей |

## 3. Common Value Conventions

### Общие недоступные значения

Интеграция активно использует:

- `unavailable`
- `unknown`
- `none`

### Risk enums

Большинство `*_risk` полей используют один из следующих токенов:

- `very_low`
- `low`
- `moderate`
- `high`
- `very_high`
- `extreme`
- `unavailable`

Исключения:

- `sensor.beach_danger_index`: `Low`, `Medium`, `High`
- `sensor.jellyfish_risk`: может встречаться `off_season`

### Trend / planner enums

Типичные planner и trend tokens:

- `rising`
- `falling`
- `stable`
- `decreasing`
- `high`
- `stable_low`
- `better_now`
- `better_in_3h`
- `disabled`
- `ready`
- `not_ready`
- `notify`
- `idle`
- `indoors`
- `mixed`
- `outdoor`

### Planner mode enums

- `normal`
- `child`
- `elderly`
- `sport`
- `beach_day`

## 4. Fixed Sensor Catalog

### Weather and Sea

| Entity ID | Meaning | Type / values |
| --- | --- | --- |
| `sensor.weather_summary` | Weather summary | summary string |
| `sensor.weather_code` | Weather code | WMO code / integer |
| `sensor.precipitation_probability` | Precipitation probability | number `%` |
| `sensor.precipitation` | Precipitation | number `mm` |
| `sensor.uv_index` | UV index | float |
| `sensor.rain_next_6h` | Rain probability next 6h | number `%` |
| `sensor.wind_speed` | Wind speed | number `m/s` |
| `sensor.pressure` | Pressure | number `hPa` |
| `sensor.humidity` | Humidity | number `%` |
| `sensor.apparent_temperature` | Apparent temperature | number `degC` |
| `sensor.sea_temperature_openmeteo` | Sea temperature | number `degC` |
| `sensor.sea_temperature_openmeteo_3h` | Sea temperature +3h | number `degC` |
| `sensor.sea_temperature_openmeteo_6h` | Sea temperature +6h | number `degC` |
| `sensor.wave_height` | Wave height | number `m` |
| `sensor.wave_period` | Wave period | number `s` |

### Air, Pollen and Beach Comfort

| Entity ID | Meaning | Type / values |
| --- | --- | --- |
| `sensor.pollen_total` | Pollen total | number `grains/m3` |
| `sensor.pollen_birch` | Pollen birch | number `grains/m3` |
| `sensor.pollen_alder` | Pollen alder | number `grains/m3` |
| `sensor.pollen_grass` | Pollen grass | number `grains/m3` |
| `sensor.pollen_olive` | Pollen olive | number `grains/m3` |
| `sensor.pollen_ragweed` | Pollen ragweed | number `grains/m3` |
| `sensor.pollen_ambrosia` | Pollen ambrosia | number `grains/m3` |
| `sensor.pollen_mugwort` | Pollen mugwort | number `grains/m3` |
| `sensor.ambrosia_risk` | Ambrosia risk | `low|moderate|high|very_high|unavailable` |
| `sensor.allergy_index` | Allergy index | int `0..100` |
| `sensor.asthma_risk` | Asthma risk | risk enum |
| `sensor.air_quality_european_aqi` | European AQI | number `AQI` |
| `sensor.air_quality_pm25` | PM2.5 | number `ug/m3` |
| `sensor.air_quality_pm10` | PM10 | number `ug/m3` |
| `sensor.air_quality_ozone` | Ozone (O3) | number `ug/m3` |
| `sensor.air_quality_no2` | Nitrogen dioxide | number `ug/m3` |
| `sensor.air_quality_so2` | Sulfur dioxide | number `ug/m3` |
| `sensor.air_quality_co` | Carbon monoxide | number `ug/m3` |
| `sensor.waqi_barcelona` | WAQI proxy | numeric proxy |
| `sensor.saharan_dust_level` | Saharan dust level | token/string |
| `sensor.saharan_dust_forecast_6h` | Saharan dust forecast +6h | number `ug/m3` |
| `sensor.beach_flag_calculated` | Beach flag (calculated) | `green|yellow|red|unavailable` |
| `sensor.beach_danger_index` | Beach danger index | `Low|Medium|High|unavailable` |
| `sensor.beach_crowding_estimate` | Beach crowding estimate | `empty|normal|crowded|very_crowded|unavailable` |
| `sensor.beach_comfort_index` | Beach comfort index | int `0..10` |
| `sensor.beach_recommendation` | Beach recommendation | `Recommended|Not ideal|unavailable` |

### Marine and Bio Hazards

| Entity ID | Meaning | Type / values |
| --- | --- | --- |
| `sensor.jellyfish_risk` | Jellyfish risk | risk enum, может быть `off_season` |
| `sensor.jellyfish_official_risk` | Jellyfish official risk | risk enum |
| `sensor.jellyfish_official_status` | Jellyfish official status | official status string |
| `sensor.jellyfish_species_count` | Jellyfish species count | integer count |
| `sensor.jellyfish_last_update` | Jellyfish last update | datetime/string |
| `sensor.jellyfish_nearest_beach` | Nearest beach (PlatgesCat) | string |
| `sensor.jellyfish_nearest_beach_distance` | Nearest beach distance | number `km` |
| `sensor.beach_water_quality_official` | Beach water quality (official) | string |
| `sensor.beach_water_temperature_official` | Beach water temperature (official) | number `degC` |
| `sensor.jellyfish_icon_code` | Jellyfish icon code | status/icon code string |
| `sensor.tiger_mosquito_risk` | Tiger mosquito risk | risk enum |
| `sensor.tiger_mosquito_index` | Tiger mosquito index | int `0..100` |
| `sensor.mosquito_index` | Mosquito index | int `0..100` |
| `sensor.tiger_mosquito_reports_30d` | Tiger mosquito reports 30d | integer count |
| `sensor.tiger_mosquito_reports_180d` | Tiger mosquito reports 180d | integer count |
| `sensor.tiger_mosquito_high_confidence` | Tiger mosquito high confidence | number `%` |
| `sensor.tiger_mosquito_confidence_avg` | Tiger mosquito confidence avg | number `%` |
| `sensor.tiger_mosquito_last_report` | Tiger mosquito last report | datetime/string |
| `sensor.tiger_mosquito_icon_url` | Tiger mosquito icon URL | URL |
| `sensor.tick_risk` | Tick risk | risk enum |
| `sensor.tick_index` | Tick index | int `0..100` |
| `sensor.tick_reports_30d` | Tick reports 30d | integer count |
| `sensor.tick_reports_180d` | Tick reports 180d | integer count |
| `sensor.tick_last_report` | Tick last report | datetime/string |
| `sensor.tick_source` | Tick source | string source/taxon |
| `sensor.tick_icon_url` | Tick icon URL | URL |
| `sensor.rip_current_risk` | Rip current risk | risk enum |
| `sensor.rip_current_index` | Rip current index | int `0..100` |

### Climate Stress and Environmental Risk

| Entity ID | Meaning | Type / values |
| --- | --- | --- |
| `sensor.heat_stress_risk` | Heat stress risk | risk enum |
| `sensor.heat_stress_index` | Heat stress index | int `0..100` |
| `sensor.heat_index_c` | Heat index | number `degC` |
| `sensor.wet_bulb_c` | Wet bulb temperature | number `degC` |
| `sensor.uv_dose_sed_1h` | UV dose (1h full exposure) | number `SED` |
| `sensor.uv_dose_sed_today_est` | UV dose today (tracked) | number `SED` |
| `sensor.uv_dose_status` | UV dose status | `low|moderate|high|very_high|extreme|unavailable` |
| `sensor.astro_solar_elevation` | Astro solar elevation | number `deg` |
| `sensor.astro_uv_index_now` | Astro UV index now | float |
| `sensor.astro_uv_index_3h_max` | Astro UV index +3h max | float |
| `sensor.astro_uv_risk_3h` | Astro UV risk +3h | risk enum |
| `sensor.astro_uv_now_vs_3h` | Astro UV now vs +3h | `rising|falling|stable|unavailable` |
| `sensor.wbgt_c` | WBGT | number `degC` |
| `sensor.dehydration_index` | Dehydration index | int `0..100` |
| `sensor.dehydration_risk` | Dehydration risk | risk enum |
| `sensor.thunderstorm_risk` | Thunderstorm risk | risk enum |
| `sensor.thunderstorm_index` | Thunderstorm index | int `0..100` |
| `sensor.thunderstorm_cape` | CAPE | number `J/kg` |
| `sensor.thunderstorm_nowcast_3h` | Thunderstorm nowcast +3h | `rising|decreasing|high|stable_low|unavailable` |
| `sensor.tide_level_m` | Tide level (MSL) | number `m` |
| `sensor.tide_trend_3h` | Tide trend +3h | `rising|falling|stable|unavailable` |
| `sensor.tide_range_24h_m` | Tide range 24h | number `m` |
| `sensor.ocean_current_speed` | Ocean current speed | number `m/s` |
| `sensor.ocean_current_direction` | Ocean current direction | number `deg` |
| `sensor.current_risk` | Current risk | risk enum |
| `sensor.algae_bloom_risk` | Algae bloom risk | risk enum |
| `sensor.algae_bloom_index` | Algae bloom index | int `0..100` |
| `sensor.algae_bloom_signal` | Algae bloom signal | diagnostic string |
| `sensor.algae_chlorophyll_mg_m3` | Algae chlorophyll | number `mg/m3` |
| `sensor.algae_source` | Algae source | source string |
| `sensor.smoke_transport_risk` | Smoke transport risk | risk enum |
| `sensor.smoke_transport_index` | Smoke transport index | int `0..100` |
| `sensor.smoke_transport_signal` | Smoke transport signal | diagnostic string |
| `sensor.smoke_cams_bbaod550` | Smoke CAMS bbaod550 | float/no unit |
| `sensor.smoke_cams_pm25` | Smoke CAMS PM2.5 | number `ug/m3` |
| `sensor.smoke_cams_fire_frp` | Smoke CAMS fire radiative power | number `W/m2` |
| `sensor.smoke_source` | Smoke source | source string |
| `sensor.cap_alert_risk` | CAP alert risk | risk enum |
| `sensor.cap_alert_index` | CAP alert index | int `0..100` |
| `sensor.cap_alerts_active` | CAP alerts active | integer count |
| `sensor.cap_highest_severity` | CAP highest severity | severity string |
| `sensor.cap_top_event` | CAP top event | string |
| `sensor.cap_top_area` | CAP top area | string |
| `sensor.cap_top_expires` | CAP top expires | datetime/string |
| `sensor.cap_source` | CAP source | source string |
| `sensor.bite_index` | Bite index | int `0..100` |
| `sensor.bite_risk` | Bite risk | risk enum |
| `sensor.bite_outlook_3d` | Bite outlook 3d | risk enum |

### Earthquakes, Wildfire and Hazards

| Entity ID | Meaning | Type / values |
| --- | --- | --- |
| `sensor.earthquake_risk` | Earthquake risk | risk enum |
| `sensor.earthquake_index` | Earthquake index | int `0..100` |
| `sensor.earthquake_events_24h` | Earthquakes 24h | integer count |
| `sensor.earthquake_events_7d` | Earthquakes 7d | integer count |
| `sensor.earthquake_max_magnitude_7d` | Earthquake max magnitude 7d | number `M` |
| `sensor.earthquake_nearest_distance_km` | Nearest earthquake distance | number `km` |
| `sensor.earthquake_nearest_magnitude` | Nearest earthquake magnitude | number `M` |
| `sensor.earthquake_latest_time` | Latest earthquake time | datetime/string |
| `sensor.earthquake_latest_place` | Latest earthquake place | string |
| `sensor.earthquake_tsunami_events_24h` | Tsunami-flagged earthquakes 24h | integer count |
| `sensor.earthquake_event_url` | Nearest earthquake event URL | URL |
| `sensor.earthquake_source` | Earthquake source | source string |
| `sensor.wildfire_risk` | Wildfire risk | risk enum |
| `sensor.wildfire_index` | Wildfire index | int `0..100` |
| `sensor.wildfire_active_events_global` | Wildfire active events (global) | integer count |
| `sensor.wildfire_high_alert_events_global` | Wildfire high-alert events (global) | integer count |
| `sensor.wildfire_max_alert_level` | Wildfire max alert level | alert level string |
| `sensor.wildfire_nearest_distance_km` | Nearest wildfire distance | number `km` |
| `sensor.wildfire_nearest_country` | Nearest wildfire country | string |
| `sensor.wildfire_nearest_title` | Nearest wildfire title | string |
| `sensor.wildfire_nearest_link` | Nearest wildfire report URL | URL |
| `sensor.wildfire_icon_url` | Nearest wildfire icon URL | URL |
| `sensor.wildfire_source` | Wildfire source | source string |
| `sensor.hazard_active_events_global` | Hazard active events (global) | integer count |
| `sensor.hazard_high_alert_events_global` | Hazard high-alert events (global) | integer count |
| `sensor.hazard_top_event_type` | Top hazard event type | event type string |
| `sensor.hazard_top_event_alert` | Top hazard event alert | alert level string |
| `sensor.hazard_top_event_title` | Top hazard event title | string |
| `sensor.hazard_top_event_country` | Top hazard event country | string |
| `sensor.hazard_top_event_distance_km` | Top hazard event distance | number `km` |
| `sensor.hazard_top_event_icon_url` | Top hazard event icon URL | URL |
| `sensor.hazard_last_update` | Hazard feed last update | datetime/string |
| `sensor.hazard_source` | Hazard source | source string |

### AURA Planner Core

| Entity ID | Meaning | Type / values |
| --- | --- | --- |
| `sensor.aura_daily_plan_status` | AURA daily plan status | `enabled|disabled` |
| `sensor.aura_planner_mode_default` | AURA planner mode (default) | `normal|child|elderly|sport|beach_day` |
| `sensor.aura_now_vs_3h_outdoor` | AURA outdoor now vs +2..3h | `better_now|better_in_3h|stable|disabled|unavailable` |
| `sensor.aura_now_vs_3h_beach` | AURA beach now vs +2..3h | `better_now|better_in_3h|stable|disabled|unavailable` |
| `sensor.aura_now_vs_3h_summary` | AURA now vs +2..3h summary | summary string |
| `sensor.aura_beach_pack_trigger` | AURA beach pack trigger | `ready|not_ready|disabled` |
| `sensor.aura_beach_pack_list` | AURA beach pack list | comma-separated string |
| `sensor.aura_beach_notification_key` | AURA beach notification key | string key |
| `sensor.aura_beach_notification_state` | AURA beach notification state | `notify|idle` |

## 5. Dynamic Sensor Families

Интеграция дополнительно генерирует семейства сенсоров из `personas[]` и `tracking_entities[]`.

### Tracking entities

| Pattern | Meaning | Type / values |
| --- | --- | --- |
| `sensor.aura_tracker_{tracker_id}_uv_sed_today` | Накопленная UV dose за текущий день для tracker | number `SED` |
| `sensor.aura_tracker_{tracker_id}_uv_exposure_state` | Outdoor exposure state tracker | `indoors|mixed|outdoor|unknown` |

`tracker_id` берется из `tracking_entities[].id` или нормализуется из имени/сущности.

### Persona profile sensors

| Pattern | Meaning | Type / values |
| --- | --- | --- |
| `sensor.aura_{persona_id}_sunburn_time_min` | Прогноз времени до sunburn | number `min` |
| `sensor.aura_{persona_id}_sunburn_risk` | Персональный UV risk | risk enum |
| `sensor.aura_{persona_id}_heat_stress_index` | Персональный heat stress index | int `0..100` |
| `sensor.aura_{persona_id}_heat_stress_risk` | Персональный heat stress risk | risk enum |
| `sensor.aura_{persona_id}_presence` | Состояние связанного `person.*` | HA state string |
| `sensor.aura_{persona_id}_profile` | Сериализованный persona profile | string |

### Persona planner sensors

| Pattern | Meaning | Type / values |
| --- | --- | --- |
| `sensor.aura_{persona_id}_planner_mode` | Planner mode конкретной persona | planner mode enum |
| `sensor.aura_{persona_id}_best_hours_outdoor` | Лучшие часы для outdoor | comma-separated hours string or `none` |
| `sensor.aura_{persona_id}_best_hours_beach` | Лучшие часы для beach | comma-separated hours string or `none` |
| `sensor.aura_{persona_id}_now_vs_3h` | Лучше сейчас или через 2-3 часа | `better_now|better_in_3h|stable|disabled|unavailable` |
| `sensor.aura_{persona_id}_daily_plan` | Итоговый daily plan summary | string |
| `sensor.aura_{persona_id}_pack_list` | Персональный pack list | comma-separated string |
| `sensor.aura_{persona_id}_smart_notification` | Персональный notification state | `notify|idle` |

`persona_id` берется из `personas[].id`.

## 6. Public Export Contract

При `public_sensor: true` метрики публикуются в Home Assistant как обычные state entities.

### `sensor.bereginya_aura_snapshot`

| Field | Value |
| --- | --- |
| state | количество опубликованных метрик |
| `friendly_name` | `Beregynya AURA Snapshot` |
| `icon` | `mdi:shield-wave` |
| `generated_at` | timestamp snapshot |
| `metric_count` | количество метрик |
| `source` | `bereginya_aura_internal_api` |

### `sensor.bereginya_aura_*`

Каждый экспортируемый sensor получает:

| Attribute | Description |
| --- | --- |
| `friendly_name` | `name` из metric row |
| `attribution` | всегда `Beregynya AURA` |
| `aura_generated_at` | timestamp snapshot |
| `aura_original_entity_id` | исходный `sensor.*` из snapshot |
| `aura_source` | `source` исходной метрики |
| `aura_source_entity` | связанный HA entity, если есть |
| `unit_of_measurement` | unit, если есть |
| `icon` | MDI icon, если есть |
| `icon_url` | PNG icon URL, если есть |
| `icon_webp_url` | WebP icon URL, если есть |
| `icon_gif_url` | GIF icon URL, если есть |
| `aura_raw_value` | полный raw string, если state пришлось обрезать до 255 chars |

## 7. Source Files

Эта спецификация собрана по текущему runtime-коду:

- `custom_components/bereginya_aura/snapshot/provider.py`
- `custom_components/bereginya_aura/snapshot/metrics_core.py`
- `custom_components/bereginya_aura/snapshot/metrics_external.py`
- `custom_components/bereginya_aura/snapshot/metrics_persona.py`
- `custom_components/bereginya_aura/const.py`

Если код добавляет новый `entity_id`, этот файл нужно обновить вместе с логикой сборки snapshot.
