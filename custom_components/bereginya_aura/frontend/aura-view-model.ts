export type AuraLang = "ru" | "en" | "ua" | "es";
export type AuraThemeVariant = "ocean_glass" | "aurora_glass" | "sunset_glass";
export type AuraLayoutMode = "premium" | "compact";
export type AuraTone = "safe" | "warning" | "danger" | "neutral" | "info";

export interface AuraStrings {
  titleDefault: string;
  loading: string;
  apiError: string;
  details: string;
  close: string;
  unavailable: string;
  noData: string;
  yes: string;
  no: string;
  utilityTitle: string;
  localTime: string;
  freshness: string;
  source: string;
  health: string;
  forecast: string;
  weather: string;
  planner: string;
  beach: string;
  sunHeat: string;
  airPollen: string;
  bioBites: string;
  alerts: string;
  personas: string;
  tracking: string;
  system: string;
  wind: string;
  humidity: string;
  seaTemp: string;
  comfort: string;
  waveHeight: string;
  currentRisk: string;
  ripCurrent: string;
  uvIndex: string;
  heatStress: string;
  dehydration: string;
  wbgt: string;
  uvDose: string;
  airQuality: string;
  pollen: string;
  allergy: string;
  smoke: string;
  dust: string;
  jellyfish: string;
  mosquito: string;
  tick: string;
  bite: string;
  thunderstorm: string;
  wildfire: string;
  capAlerts: string;
  topAlert: string;
  betterNow: string;
  betterLater: string;
  steadyWindow: string;
  packReady: string;
  packSoon: string;
  dailyPlan: string;
  packList: string;
  bestHoursOutdoor: string;
  bestHoursBeach: string;
  sunburnTime: string;
  sunburnRisk: string;
  heatIndex: string;
  exposure: string;
  uvSed: string;
  generatedAt: string;
  forecastCount: string;
  publicSensor: string;
  fetchSources: string;
  lastUpdatedNow: string;
  minutesAgo: string;
  hoursAgo: string;
  daysAgo: string;
}

export interface AuraCardConfig extends Record<string, any> {
  type: string;
  title: string;
  lang: AuraLang;
  refresh_seconds: number;
  force_refresh: boolean;
  show_icons: boolean;
  prefer_gif_icons: boolean;
  debug: boolean;
  theme_variant: AuraThemeVariant;
  layout_mode: AuraLayoutMode;
  show_personas: boolean;
  show_tracking: boolean;
  show_debug: boolean;
  forecast_days: number;
  accent_by_risk: boolean;
}

export interface AuraStatusChipVm {
  icon: string;
  label: string;
  tone: AuraTone;
  detail?: string;
}

export interface AuraMetricVm {
  icon: string;
  label: string;
  value: string;
  tone?: AuraTone;
}

export interface AuraForecastDayVm {
  key: string;
  label: string;
  iconUrl: string | null;
  condition: string;
  tempHigh: string;
  tempLow: string;
  badge?: {
    label: string;
    tone: AuraTone;
  };
}

export interface AuraDomainVm {
  key: string;
  icon: string;
  title: string;
  tone: AuraTone;
  primaryLabel: string;
  primaryValue: string;
  secondary?: string;
  metrics: AuraMetricVm[];
}

export interface AuraPersonaVm {
  id: string;
  name: string;
  tone: AuraTone;
  advisor: string;
  summary: string | null;
  metrics: AuraMetricVm[];
  highlights: AuraStatusChipVm[];
  packList: string | null;
}

export interface AuraTrackerVm {
  id: string;
  name: string;
  tone: AuraTone;
  uvSed: string | null;
  exposure: string | null;
}

export interface AuraTimezoneVm {
  timezone: string;
  date: string;
  time: string;
  iso: string;
}

export interface AuraViewModel {
  header: {
    title: string;
    location: string;
    freshness: string;
    freshnessTone: AuraTone;
    sourceChip: AuraStatusChipVm;
    healthChip: AuraStatusChipVm;
    timezones: AuraTimezoneVm[];
  };
  hero: {
    iconUrl: string | null;
    summary: string;
    temperature: string;
    range: string;
    feelsLike: string | null;
    verdict: string;
    verdictMeta: string | null;
    verdictTone: AuraTone;
    metrics: AuraMetricVm[];
  };
  planner: {
    chips: AuraStatusChipVm[];
  };
  forecast: AuraForecastDayVm[];
  domains: AuraDomainVm[];
  personas: AuraPersonaVm[];
  tracking: AuraTrackerVm[];
  debug: {
    fields: Array<{ label: string; value: string }>;
    fetchRows: AuraStatusChipVm[];
  };
}

type AuraEntityRecord = {
  entity_id: string;
  name: string;
  value: any;
  unit: string | null;
  icon: string | null;
  attributes: Record<string, any>;
  source?: string;
  source_entity?: string;
};

const TOKEN_LABELS: Record<AuraLang, Record<string, string>> = {
  ru: {
    ok: "OK",
    healthy: "Стабильно",
    partial: "Частично",
    degraded: "Сбои",
    unknown: "Неизвестно",
    unavailable: "Недоступно",
    none: "Нет",
    low: "Низкий",
    moderate: "Умеренный",
    medium: "Умеренный",
    high: "Высокий",
    very_high: "Очень высокий",
    extreme: "Экстремальный",
    watch: "Наблюдение",
    advisory: "Предупреждение",
    warning: "Опасно",
    severe: "Серьёзно",
    red: "Красный",
    orange: "Оранжевый",
    yellow: "Жёлтый",
    green: "Зелёный",
    on: "Да",
    off: "Нет",
    true: "Да",
    false: "Нет",
    off_season: "Не сезон",
    stable: "Стабильно",
    now: "Сейчас",
    later: "Позже",
    open: "Открыто",
    closed: "Закрыто",
  },
  en: {
    ok: "OK",
    healthy: "Healthy",
    partial: "Partial",
    degraded: "Degraded",
    unknown: "Unknown",
    unavailable: "Unavailable",
    none: "None",
    low: "Low",
    moderate: "Moderate",
    medium: "Moderate",
    high: "High",
    very_high: "Very high",
    extreme: "Extreme",
    watch: "Watch",
    advisory: "Advisory",
    warning: "Warning",
    severe: "Severe",
    red: "Red",
    orange: "Orange",
    yellow: "Yellow",
    green: "Green",
    on: "On",
    off: "Off",
    true: "Yes",
    false: "No",
    off_season: "Off season",
    stable: "Stable",
    now: "Now",
    later: "Later",
    open: "Open",
    closed: "Closed",
  },
  ua: {
    ok: "OK",
    healthy: "Стабільно",
    partial: "Частково",
    degraded: "Збій",
    unknown: "Невідомо",
    unavailable: "Недоступно",
    none: "Немає",
    low: "Низький",
    moderate: "Помірний",
    medium: "Помірний",
    high: "Високий",
    very_high: "Дуже високий",
    extreme: "Екстремальний",
    watch: "Спостереження",
    advisory: "Попередження",
    warning: "Небезпечно",
    severe: "Серйозно",
    red: "Червоний",
    orange: "Помаранчевий",
    yellow: "Жовтий",
    green: "Зелений",
    on: "Так",
    off: "Ні",
    true: "Так",
    false: "Ні",
    off_season: "Не сезон",
    stable: "Стабільно",
    now: "Зараз",
    later: "Пізніше",
    open: "Відкрито",
    closed: "Закрито",
  },
  es: {
    ok: "OK",
    healthy: "Estable",
    partial: "Parcial",
    degraded: "Degradado",
    unknown: "Desconocido",
    unavailable: "No disponible",
    none: "Ninguno",
    low: "Bajo",
    moderate: "Moderado",
    medium: "Moderado",
    high: "Alto",
    very_high: "Muy alto",
    extreme: "Extremo",
    watch: "Vigilancia",
    advisory: "Aviso",
    warning: "Alerta",
    severe: "Severo",
    red: "Rojo",
    orange: "Naranja",
    yellow: "Amarillo",
    green: "Verde",
    on: "Sí",
    off: "No",
    true: "Sí",
    false: "No",
    off_season: "Fuera de temporada",
    stable: "Estable",
    now: "Ahora",
    later: "Más tarde",
    open: "Abierto",
    closed: "Cerrado",
  },
};

class EntityLookup {
  private _snapshotEntities: AuraEntityRecord[];

  private _snapshotMap: Map<string, AuraEntityRecord>;

  private _hass: any;

  constructor(snapshot: any, hass: any) {
    this._snapshotEntities = Array.isArray(snapshot?.entities)
      ? snapshot.entities
          .filter((entity: any) => typeof entity?.entity_id === "string" && entity.entity_id.trim())
          .map((entity: any) => ({
            entity_id: String(entity.entity_id),
            name: String(entity.name || entity.entity_id),
            value: entity.value,
            unit: typeof entity.unit === "string" && entity.unit.trim() ? String(entity.unit) : null,
            icon: typeof entity.icon === "string" && entity.icon.trim() ? String(entity.icon) : null,
            attributes: typeof entity.attributes === "object" && entity.attributes !== null ? entity.attributes : {},
            source: typeof entity.source === "string" ? entity.source : undefined,
            source_entity: typeof entity.source_entity === "string" ? entity.source_entity : undefined,
          }))
      : [];
    this._snapshotMap = new Map(this._snapshotEntities.map((entity) => [entity.entity_id, entity]));
    this._hass = hass;
  }

  all(): AuraEntityRecord[] {
    return this._snapshotEntities;
  }

  entity(entityId: string): AuraEntityRecord | undefined {
    const fromSnapshot = this._snapshotMap.get(entityId);
    if (fromSnapshot) return fromSnapshot;
    const stateObj = this._hass?.states?.[entityId];
    if (!stateObj) return undefined;
    return {
      entity_id: entityId,
      name: String(stateObj.attributes?.friendly_name || entityId),
      value: stateObj.state,
      unit:
        typeof stateObj.attributes?.unit_of_measurement === "string" && stateObj.attributes.unit_of_measurement.trim()
          ? String(stateObj.attributes.unit_of_measurement)
          : null,
      icon: typeof stateObj.attributes?.icon === "string" ? String(stateObj.attributes.icon) : null,
      attributes: typeof stateObj.attributes === "object" && stateObj.attributes !== null ? stateObj.attributes : {},
    };
  }

  pick(ids: string[]): AuraEntityRecord | undefined {
    for (const entityId of ids) {
      const entity = this.entity(entityId);
      if (entity && !isMissing(entity.value)) return entity;
    }
    for (const entityId of ids) {
      const entity = this.entity(entityId);
      if (entity) return entity;
    }
    return undefined;
  }

  value(...ids: string[]): any {
    return this.pick(ids)?.value;
  }

  numeric(...ids: string[]): number | null {
    for (const entityId of ids) {
      const numeric = toNumber(this.entity(entityId)?.value);
      if (numeric !== null) return numeric;
    }
    return null;
  }

  text(...ids: string[]): string | null {
    const entity = this.pick(ids);
    if (!entity || isMissing(entity.value)) return null;
    return String(entity.value);
  }

  withPrefix(prefix: string): AuraEntityRecord[] {
    return this._snapshotEntities.filter((entity) => entity.entity_id.startsWith(prefix));
  }
}

export function normalizeCardConfig(raw: Record<string, any> | null | undefined): AuraCardConfig {
  const source = raw && typeof raw === "object" ? raw : {};
  const forecastDaysRaw = Number(source.forecast_days ?? 5);
  const refreshRaw = Number(source.refresh_seconds ?? 120);
  const lang = normalizeLang(source.lang);
  const themeVariant = normalizeThemeVariant(source.theme_variant);
  const layoutMode = normalizeLayoutMode(source.layout_mode);

  return {
    ...source,
    type: "custom:bereginya-aura",
    title: typeof source.title === "string" && source.title.trim() ? source.title.trim() : "Beregynya AURA",
    lang,
    refresh_seconds: Number.isFinite(refreshRaw) ? Math.max(15, Math.round(refreshRaw)) : 120,
    force_refresh: source.force_refresh === true,
    show_icons: source.show_icons !== false,
    prefer_gif_icons: source.prefer_gif_icons === true,
    debug: source.debug === true,
    theme_variant: themeVariant,
    layout_mode: layoutMode,
    show_personas: source.show_personas !== false,
    show_tracking: source.show_tracking !== false,
    show_debug: source.show_debug === true,
    forecast_days: Number.isFinite(forecastDaysRaw) ? Math.max(3, Math.min(7, Math.round(forecastDaysRaw))) : 5,
    accent_by_risk: source.accent_by_risk !== false,
  };
}

export function buildAuraViewModel(
  snapshot: any,
  hass: any,
  config: AuraCardConfig,
  options: {
    lang: AuraLang;
    strings: AuraStrings;
    now?: Date;
  },
): AuraViewModel {
  const lang = options.lang;
  const strings = options.strings;
  const now = options.now ?? new Date();
  const locale = localeOf(lang);
  const meta = snapshot?.meta && typeof snapshot.meta === "object" ? snapshot.meta : {};
  const lookup = new EntityLookup(snapshot, hass);
  const forecast = Array.isArray(snapshot?.forecast_daily) ? snapshot.forecast_daily : [];

  const freshness = buildFreshness(meta.generated_at, now, strings);
  const sourceMode = present(meta.source_mode, lang, strings);
  const timezones = buildTimezones(meta, now, locale);
  const health = buildFetchHealth(meta.fetch, lang, strings);

  const tempEntity = lookup.pick([
    "sensor.weather_temperature",
    "sensor.air_temperature",
    "sensor.outdoor_temperature",
    "sensor.current_temperature",
    "sensor.temperature",
  ]);
  const apparentEntity = lookup.pick(["sensor.apparent_temperature"]);
  const heroTemp =
    formatTemperatureMaybe(tempEntity?.value, lang, strings, locale) ??
    formatTemperatureMaybe(apparentEntity?.value, lang, strings, locale) ??
    formatTemperatureMaybe(forecast[0]?.temp_max, lang, strings, locale) ??
    strings.unavailable;
  const heroRange = formatTemperatureRange(forecast[0]?.temp_max, forecast[0]?.temp_min, lang, strings, locale);
  const feelsLike =
    tempEntity && apparentEntity && toNumber(apparentEntity.value) !== null
      ? displayEntityValue(apparentEntity, lang, strings, locale, { temperature: true })
      : null;
  const weatherSummary = sanitizeWeatherSummary(
    lookup.text("sensor.weather_summary") || present(forecast[0]?.weather_label || forecast[0]?.weather, lang, strings),
    lang,
    strings,
  );
  const heroVerdictTone = config.accent_by_risk
    ? beachVerdictTone(
        lookup.value("sensor.beach_flag_calculated"),
        lookup.value("sensor.current_risk"),
        lookup.numeric("sensor.beach_comfort_index"),
      )
    : "neutral";
  const heroVerdict = present(lookup.value("sensor.beach_flag_calculated"), lang, strings);
  const heroVerdictMeta = toNumber(lookup.value("sensor.beach_comfort_index"))
    ? `${strings.comfort} ${formatNumber(lookup.value("sensor.beach_comfort_index"), locale, 1)}/10`
    : null;

  const plannerChips = buildPlannerChips(lookup, meta, lang, strings, config.accent_by_risk).slice(0, 3);
  const forecastDays = forecast
    .slice(0, config.forecast_days)
    .map((day: any, index: number) => buildForecastDay(day, index, lang, strings, locale));

  const domains = [
    buildBeachDomain(lookup, lang, strings, locale, config.accent_by_risk),
    buildSunHeatDomain(lookup, lang, strings, locale, config.accent_by_risk),
    buildAirDomain(lookup, lang, strings, locale, config.accent_by_risk),
    buildBioDomain(lookup, lang, strings, locale, config.accent_by_risk),
    buildAlertsDomain(lookup, lang, strings, locale, config.accent_by_risk),
  ];

  const personas = config.show_personas ? buildPersonas(meta.personas, lookup, lang, strings, locale, config) : [];
  const tracking = config.show_tracking
    ? buildTracking(meta.tracking_entities, lookup, lang, strings, locale, config.accent_by_risk)
    : [];

  return {
    header: {
      title: config.title || strings.titleDefault,
      location: buildLocation(meta.home_position, locale),
      freshness: freshness.label,
      freshnessTone: freshness.tone,
      sourceChip: {
        icon: "mdi:database-outline",
        label: `${strings.source}: ${sourceMode}`,
        tone: "info",
      },
      healthChip: {
        icon: "mdi:pulse",
        label: `${strings.health}: ${health.label}`,
        tone: health.tone,
        detail: health.detail,
      },
      timezones,
    },
    hero: {
      iconUrl: config.show_icons ? resolveWeatherIcon(meta, forecast[0]) : null,
      summary: weatherSummary,
      temperature: heroTemp,
      range: heroRange,
      feelsLike,
      verdict: heroVerdict,
      verdictMeta: heroVerdictMeta,
      verdictTone: heroVerdictTone,
      metrics: [
        buildMetric(strings.wind, "mdi:weather-windy", lookup.pick(["sensor.wind_speed"]), lang, strings, locale),
        buildMetric(strings.humidity, "mdi:water-percent", lookup.pick(["sensor.humidity"]), lang, strings, locale),
        buildMetric(
          strings.seaTemp,
          "mdi:waves",
          lookup.pick(["sensor.sea_temperature_openmeteo"]),
          lang,
          strings,
          locale,
          { temperature: true },
        ),
      ].filter(Boolean) as AuraMetricVm[],
    },
    planner: {
      chips: plannerChips,
    },
    forecast: forecastDays,
    domains,
    personas,
    tracking,
    debug: {
      fields: [
        { label: strings.generatedAt, value: present(meta.generated_at, lang, strings) },
        { label: strings.source, value: sourceMode },
        { label: strings.forecastCount, value: present(meta.forecast_count ?? forecast.length, lang, strings) },
        { label: strings.publicSensor, value: present(meta.public_sensor, lang, strings) },
      ],
      fetchRows: health.rows,
    },
  };
}

export function buildDebugTranscript(
  snapshot: any,
  config: AuraCardConfig,
  options: { lang: AuraLang; strings: AuraStrings },
): string {
  const lang = options.lang;
  const strings = options.strings;
  if (!snapshot) return strings.loading;

  const meta = snapshot?.meta && typeof snapshot.meta === "object" ? snapshot.meta : {};
  const lookup = new EntityLookup(snapshot, null);
  const forecast = Array.isArray(snapshot?.forecast_daily) ? snapshot.forecast_daily : [];
  const lines: string[] = [];

  lines.push(`# ${config.title || strings.titleDefault}`);
  lines.push("");
  lines.push(`- ${strings.source}: ${present(meta.source_mode, lang, strings)}`);
  lines.push(`- ${strings.generatedAt}: ${present(meta.generated_at, lang, strings)}`);
  lines.push(`- ${strings.forecastCount}: ${String(forecast.length)}`);
  lines.push(`- ${strings.publicSensor}: ${present(meta.public_sensor, lang, strings)}`);
  lines.push("");
  lines.push(`## ${strings.fetchSources}`);
  const healthRows = buildFetchHealth(meta.fetch, lang, strings).rows;
  if (healthRows.length === 0) {
    lines.push(`- ${strings.noData}`);
  } else {
    for (const row of healthRows) {
      lines.push(`- ${row.label}`);
    }
  }
  lines.push("");
  lines.push("## Entities");
  for (const entity of lookup.all()) {
    const unit = entity.unit ? ` ${entity.unit}` : "";
    const source = entity.source ? ` (${entity.source})` : "";
    lines.push(`- ${entity.entity_id}: ${present(entity.value, lang, strings)}${unit}${source}`);
  }
  if (forecast.length > 0) {
    lines.push("");
    lines.push(`## ${strings.forecast}`);
    for (const day of forecast) {
      lines.push(
        `- ${present(day.date, lang, strings)}: ${formatTemperatureRange(day.temp_max, day.temp_min, lang, strings, localeOf(lang))}, rain ${present(day.rain_probability_max, lang, strings)}%, sea ${formatTemperature(day.sea_temp_avg, lang, strings, localeOf(lang))}`,
      );
    }
  }
  return lines.join("\n");
}

function buildPlannerChips(
  lookup: EntityLookup,
  meta: Record<string, any>,
  lang: AuraLang,
  strings: AuraStrings,
  accentByRisk: boolean,
): AuraStatusChipVm[] {
  const chips: AuraStatusChipVm[] = [];
  const summaryDecision = summarizeDecision(
    lookup.value("sensor.aura_now_vs_3h_summary"),
    lang,
    strings,
    accentByRisk,
    "mdi:timeline-clock-outline",
  );
  if (summaryDecision) chips.push(summaryDecision);

  const beachDecision = summarizeDecision(
    lookup.value("sensor.aura_now_vs_3h_beach"),
    lang,
    strings,
    accentByRisk,
    "mdi:beach",
  );
  if (beachDecision && !chips.find((chip) => chip.label === beachDecision.label)) chips.push(beachDecision);

  const outdoorDecision = summarizeDecision(
    lookup.value("sensor.aura_now_vs_3h_outdoor"),
    lang,
    strings,
    accentByRisk,
    "mdi:pine-tree",
  );
  if (outdoorDecision && !chips.find((chip) => chip.label === outdoorDecision.label)) chips.push(outdoorDecision);

  const packTrigger = truthy(lookup.value("sensor.aura_beach_pack_trigger"));
  const packList = compactList(lookup.value("sensor.aura_beach_pack_list"), lang, strings);
  if (packTrigger) {
    chips.push({
      icon: "mdi:bag-suitcase-outline",
      label: strings.packReady,
      tone: accentByRisk ? "safe" : "neutral",
      detail: packList,
    });
  } else if (packList) {
    chips.push({
      icon: "mdi:bag-carry-on",
      label: strings.packSoon,
      tone: accentByRisk ? "warning" : "neutral",
      detail: packList,
    });
  }

  const planText =
    extractPlanText(meta.daily_plan, lang, strings) ||
    extractPlanText(meta.daly_plan, lang, strings) ||
    presentMaybe(lookup.value("sensor.aura_daily_plan_status"), lang, strings);
  if (planText) {
    chips.push({
      icon: "mdi:calendar-check-outline",
      label: strings.dailyPlan,
      tone: "neutral",
      detail: planText,
    });
  }

  return chips;
}

function buildForecastDay(
  day: any,
  index: number,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
): AuraForecastDayVm {
  const rain = toNumber(day?.rain_probability_max);
  const beachScore = toNumber(day?.beach_score);
  const risk = presentMaybe(day?.tick_risk_est, lang, strings);
  let badge: AuraForecastDayVm["badge"];

  if (rain !== null && rain >= 20) {
    badge = {
      label: `${Math.round(rain)}%`,
      tone: rain >= 50 ? "warning" : "neutral",
    };
  } else if (beachScore !== null) {
    badge = {
      label: `${formatNumber(beachScore, locale, 1)}/10`,
      tone: beachScore >= 7 ? "safe" : beachScore >= 5 ? "warning" : "danger",
    };
  } else if (risk) {
    badge = {
      label: risk,
      tone: toneFromValue(day?.tick_risk_est),
    };
  }

  return {
    key: String(day?.date || index),
    label: dayLabel(day?.date, index, lang, strings, locale),
    iconUrl: resolveForecastIcon(day),
    condition: present(day?.weather_label || day?.weather, lang, strings),
    tempHigh: formatTemperature(day?.temp_max, lang, strings, locale),
    tempLow: formatTemperature(day?.temp_min, lang, strings, locale),
    badge,
  };
}

function buildBeachDomain(
  lookup: EntityLookup,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
  accentByRisk: boolean,
): AuraDomainVm {
  const comfort = toNumber(lookup.value("sensor.beach_comfort_index"));
  const flag = present(lookup.value("sensor.beach_flag_calculated"), lang, strings);
  const tone = accentByRisk
    ? beachVerdictTone(lookup.value("sensor.beach_flag_calculated"), lookup.value("sensor.current_risk"), comfort)
    : "neutral";

  return {
    key: "beach",
    icon: "mdi:beach",
    title: strings.beach,
    tone,
    primaryLabel: strings.comfort,
    primaryValue: comfort !== null ? `${formatNumber(comfort, locale, 1)}/10` : flag,
    secondary: comfort !== null ? flag : presentMaybe(lookup.value("sensor.current_risk"), lang, strings),
    metrics: [
      buildMetric(strings.seaTemp, "mdi:waves", lookup.pick(["sensor.sea_temperature_openmeteo"]), lang, strings, locale, {
        temperature: true,
      }),
      buildMetric(strings.waveHeight, "mdi:waves-arrow-up", lookup.pick(["sensor.wave_height"]), lang, strings, locale),
      buildMetric(strings.currentRisk, "mdi:currents", lookup.pick(["sensor.current_risk"]), lang, strings, locale),
      buildMetric(strings.ripCurrent, "mdi:resistor-nodes", lookup.pick(["sensor.rip_current_risk"]), lang, strings, locale),
    ].filter(Boolean) as AuraMetricVm[],
  };
}

function buildSunHeatDomain(
  lookup: EntityLookup,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
  accentByRisk: boolean,
): AuraDomainVm {
  const primaryValue = presentMaybe(lookup.value("sensor.heat_stress_risk"), lang, strings) || present(lookup.value("sensor.uv_dose_status"), lang, strings);
  const tone = accentByRisk
    ? strongestTone([
        lookup.value("sensor.heat_stress_risk"),
        lookup.value("sensor.dehydration_risk"),
        lookup.value("sensor.uv_dose_status"),
      ])
    : "neutral";

  return {
    key: "sun_heat",
    icon: "mdi:white-balance-sunny",
    title: strings.sunHeat,
    tone,
    primaryLabel: strings.heatStress,
    primaryValue,
    secondary: numericMetricLine(strings.uvIndex, lookup.value("sensor.uv_index"), locale),
    metrics: [
      buildMetric(strings.uvIndex, "mdi:weather-sunny-alert", lookup.pick(["sensor.uv_index"]), lang, strings, locale),
      buildMetric(strings.heatStress, "mdi:thermometer-alert", lookup.pick(["sensor.heat_stress_risk"]), lang, strings, locale),
      buildMetric(strings.dehydration, "mdi:cup-water", lookup.pick(["sensor.dehydration_risk"]), lang, strings, locale),
      buildMetric(strings.wbgt, "mdi:thermometer-lines", lookup.pick(["sensor.wbgt_c"]), lang, strings, locale, {
        temperature: true,
      }),
    ].filter(Boolean) as AuraMetricVm[],
  };
}

function buildAirDomain(
  lookup: EntityLookup,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
  accentByRisk: boolean,
): AuraDomainVm {
  const aqi = toNumber(lookup.value("sensor.air_quality_european_aqi"));
  const primaryValue = aqi !== null ? `AQI ${formatNumber(aqi, locale)}` : present(lookup.value("sensor.allergy_index"), lang, strings);
  const tone = accentByRisk
    ? strongestTone([
        lookup.value("sensor.air_quality_european_aqi"),
        lookup.value("sensor.smoke_transport_risk"),
        lookup.value("sensor.saharan_dust_level"),
        lookup.value("sensor.allergy_index"),
      ])
    : "neutral";

  return {
    key: "air_pollen",
    icon: "mdi:air-filter",
    title: strings.airPollen,
    tone,
    primaryLabel: strings.airQuality,
    primaryValue,
    secondary: presentMaybe(lookup.value("sensor.smoke_transport_risk"), lang, strings),
    metrics: [
      buildMetric(strings.pollen, "mdi:flower-pollen", lookup.pick(["sensor.pollen_total"]), lang, strings, locale),
      buildMetric(strings.allergy, "mdi:head-snowflake-outline", lookup.pick(["sensor.allergy_index"]), lang, strings, locale),
      buildMetric(strings.smoke, "mdi:smoke", lookup.pick(["sensor.smoke_transport_risk"]), lang, strings, locale),
      buildMetric(strings.dust, "mdi:weather-dust", lookup.pick(["sensor.saharan_dust_level"]), lang, strings, locale),
    ].filter(Boolean) as AuraMetricVm[],
  };
}

function buildBioDomain(
  lookup: EntityLookup,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
  accentByRisk: boolean,
): AuraDomainVm {
  const tone = accentByRisk
    ? strongestTone([
        lookup.value("sensor.bite_risk"),
        lookup.value("sensor.tiger_mosquito_risk"),
        lookup.value("sensor.tick_risk"),
        lookup.value("sensor.jellyfish_risk"),
      ])
    : "neutral";

  return {
    key: "bio_bites",
    icon: "mdi:bug-outline",
    title: strings.bioBites,
    tone,
    primaryLabel: strings.bite,
    primaryValue: present(lookup.value("sensor.bite_risk"), lang, strings),
    secondary: presentMaybe(lookup.value("sensor.tiger_mosquito_risk"), lang, strings),
    metrics: [
      buildMetric(strings.jellyfish, "mdi:jellyfish-outline", lookup.pick(["sensor.jellyfish_risk"]), lang, strings, locale),
      buildMetric(strings.mosquito, "mdi:mosquito", lookup.pick(["sensor.tiger_mosquito_risk"]), lang, strings, locale),
      buildMetric(strings.tick, "mdi:bug", lookup.pick(["sensor.tick_risk"]), lang, strings, locale),
      buildMetric(strings.bite, "mdi:hand-back-right-off-outline", lookup.pick(["sensor.bite_risk"]), lang, strings, locale),
    ].filter(Boolean) as AuraMetricVm[],
  };
}

function buildAlertsDomain(
  lookup: EntityLookup,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
  accentByRisk: boolean,
): AuraDomainVm {
  const topAlert = presentMaybe(lookup.value("sensor.hazard_top_event_title"), lang, strings);
  const tone = accentByRisk
    ? strongestTone([
        lookup.value("sensor.cap_alert_risk"),
        lookup.value("sensor.thunderstorm_risk"),
        lookup.value("sensor.wildfire_risk"),
        lookup.value("sensor.cap_alerts_active"),
      ])
    : "neutral";

  return {
    key: "alerts",
    icon: "mdi:alert-octagon-outline",
    title: strings.alerts,
    tone,
    primaryLabel: strings.topAlert,
    primaryValue: topAlert || present(lookup.value("sensor.cap_alert_risk"), lang, strings),
    secondary: presentMaybe(lookup.value("sensor.cap_alerts_active"), lang, strings),
    metrics: [
      buildMetric(strings.capAlerts, "mdi:alarm-light-outline", lookup.pick(["sensor.cap_alerts_active"]), lang, strings, locale),
      buildMetric(strings.thunderstorm, "mdi:weather-lightning-rainy", lookup.pick(["sensor.thunderstorm_risk"]), lang, strings, locale),
      buildMetric(strings.wildfire, "mdi:fire-alert", lookup.pick(["sensor.wildfire_risk"]), lang, strings, locale),
      buildMetric(strings.topAlert, "mdi:bullhorn-variant-outline", lookup.pick(["sensor.hazard_top_event_title"]), lang, strings, locale),
    ].filter(Boolean) as AuraMetricVm[],
  };
}

function buildPersonas(
  personasRaw: any,
  lookup: EntityLookup,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
  config: AuraCardConfig,
): AuraPersonaVm[] {
  const rows = Array.isArray(personasRaw) ? personasRaw : [];
  const personas = rows
    .map((row: any) => {
      const id = typeof row?.id === "string" && row.id.trim() ? row.id.trim() : null;
      if (!id) return null;
      const name = typeof row?.name === "string" && row.name.trim() ? row.name.trim() : id.toUpperCase();
      const prefix = `sensor.aura_${id}_`;
      const summary =
        presentMaybe(lookup.value(`${prefix}daily_plan`), lang, strings) ||
        presentMaybe(lookup.value(`${prefix}now_vs_3h`), lang, strings);
      const packList = compactList(lookup.value(`${prefix}pack_list`), lang, strings);
      const tone = config.accent_by_risk
        ? strongestTone([lookup.value(`${prefix}sunburn_risk`), lookup.value(`${prefix}heat_stress_risk`)])
        : "neutral";

      const metrics = [
        buildMetric(strings.sunburnTime, "mdi:timer-outline", lookup.pick([`${prefix}sunburn_time_min`]), lang, strings, locale, {
          unitOverride: "min",
        }),
        buildMetric(strings.sunburnRisk, "mdi:white-balance-sunny-alert", lookup.pick([`${prefix}sunburn_risk`]), lang, strings, locale),
        buildMetric(strings.heatIndex, "mdi:thermometer-water", lookup.pick([`${prefix}heat_stress_index`]), lang, strings, locale),
        buildMetric(strings.heatStress, "mdi:thermometer-alert", lookup.pick([`${prefix}heat_stress_risk`]), lang, strings, locale),
      ].filter(Boolean) as AuraMetricVm[];

      const highlights = [
        buildStatusChip("mdi:pine-tree", strings.bestHoursOutdoor, lookup.value(`${prefix}best_hours_outdoor`), lang, strings, "neutral"),
        buildStatusChip("mdi:beach", strings.bestHoursBeach, lookup.value(`${prefix}best_hours_beach`), lang, strings, "neutral"),
        summarizeDecision(lookup.value(`${prefix}now_vs_3h`), lang, strings, config.accent_by_risk, "mdi:timeline-clock-outline"),
      ].filter(Boolean) as AuraStatusChipVm[];

      const hasData = metrics.length > 0 || highlights.length > 0 || summary || packList;
      if (!hasData) return null;
      return {
        id,
        name,
        tone,
        advisor: summary || strings.noData,
        summary,
        metrics,
        highlights,
        packList,
      };
    })
    .filter(Boolean) as AuraPersonaVm[];

  return personas;
}

function buildTracking(
  trackingRaw: any,
  lookup: EntityLookup,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
  accentByRisk: boolean,
): AuraTrackerVm[] {
  const ids = new Map<string, { id: string; name: string }>();
  if (Array.isArray(trackingRaw)) {
    for (const row of trackingRaw) {
      if (typeof row === "string" && row.trim()) {
        ids.set(row.trim(), { id: row.trim(), name: row.trim() });
      } else if (typeof row === "object" && row !== null) {
        const id = typeof row.id === "string" && row.id.trim() ? row.id.trim() : null;
        if (!id) continue;
        const name =
          typeof row.name === "string" && row.name.trim()
            ? row.name.trim()
            : typeof row.entity_id === "string" && row.entity_id.trim()
              ? row.entity_id.trim()
              : id;
        ids.set(id, { id, name });
      }
    }
  }

  for (const entity of lookup.withPrefix("sensor.aura_tracker_")) {
    const match = entity.entity_id.match(/^sensor\.aura_tracker_(.+)_(uv_sed_today|uv_exposure_state)$/);
    if (!match) continue;
    if (!ids.has(match[1])) {
      ids.set(match[1], { id: match[1], name: match[1].toUpperCase() });
    }
  }

  return Array.from(ids.values())
    .map((row) => {
      const uvSed = displayEntityValue(
        lookup.pick([`sensor.aura_tracker_${row.id}_uv_sed_today`]),
        lang,
        strings,
        locale,
        { unitOverride: "SED" },
      );
      const exposure = presentMaybe(lookup.value(`sensor.aura_tracker_${row.id}_uv_exposure_state`), lang, strings);
      if (!uvSed && !exposure) return null;
      return {
        id: row.id,
        name: row.name,
        tone: accentByRisk ? toneFromValue(lookup.value(`sensor.aura_tracker_${row.id}_uv_exposure_state`)) : "neutral",
        uvSed,
        exposure,
      };
    })
    .filter(Boolean) as AuraTrackerVm[];
}

function buildMetric(
  label: string,
  icon: string,
  entity: AuraEntityRecord | undefined,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
  options: { temperature?: boolean; unitOverride?: string } = {},
): AuraMetricVm | null {
  const value = displayEntityValue(entity, lang, strings, locale, options);
  if (!value) return null;
  return {
    icon,
    label,
    value,
    tone: entity ? toneFromValue(entity.value) : "neutral",
  };
}

function buildStatusChip(
  icon: string,
  label: string,
  rawValue: any,
  lang: AuraLang,
  strings: AuraStrings,
  defaultTone: AuraTone,
): AuraStatusChipVm | null {
  const value = presentMaybe(rawValue, lang, strings);
  if (!value) return null;
  return {
    icon,
    label,
    detail: value,
    tone: defaultTone,
  };
}

function summarizeDecision(
  rawValue: any,
  lang: AuraLang,
  strings: AuraStrings,
  accentByRisk: boolean,
  icon: string,
): AuraStatusChipVm | null {
  if (isMissing(rawValue)) return null;
  const normalized = String(rawValue).trim().toLowerCase();
  if (!normalized) return null;

  if (
    normalized.includes("3h") ||
    normalized.includes("later") ||
    normalized.includes("wait") ||
    normalized.includes("через") ||
    normalized.includes("позже")
  ) {
    return {
      icon,
      label: strings.betterLater,
      tone: accentByRisk ? "warning" : "neutral",
      detail: present(rawValue, lang, strings),
    };
  }

  if (
    normalized.includes("now") ||
    normalized.includes("сейчас") ||
    normalized.includes("better_now") ||
    normalized.includes("best_now")
  ) {
    return {
      icon,
      label: strings.betterNow,
      tone: accentByRisk ? "safe" : "neutral",
      detail: present(rawValue, lang, strings),
    };
  }

  return {
    icon,
    label: strings.steadyWindow,
    tone: "neutral",
    detail: present(rawValue, lang, strings),
  };
}

function buildFetchHealth(fetchRaw: any, lang: AuraLang, strings: AuraStrings): {
  label: string;
  detail?: string;
  tone: AuraTone;
  rows: AuraStatusChipVm[];
} {
  const rows = Object.entries(fetchRaw && typeof fetchRaw === "object" ? fetchRaw : {})
    .map(([key, value]) => {
      const rendered = present(value, lang, strings);
      return {
        icon: "mdi:database-refresh-outline",
        label: `${humanizeKey(key)}: ${rendered}`,
        tone: toneFromValue(value),
      } satisfies AuraStatusChipVm;
    })
    .sort((left, right) => toneWeight(right.tone) - toneWeight(left.tone));

  if (rows.length === 0) {
    return {
      label: strings.noData,
      tone: "neutral",
      rows,
    };
  }

  const maxTone = rows[0].tone;
  if (maxTone === "safe" || maxTone === "info") {
    return {
      label: `${rows.length}/${rows.length} OK`,
      detail: undefined,
      tone: "safe",
      rows,
    };
  }

  const degraded = rows.filter((row) => row.tone === "warning" || row.tone === "danger").length;
  return {
    label: `${degraded}/${rows.length}`,
    detail: rows[0].label,
    tone: maxTone === "danger" ? "danger" : "warning",
    rows,
  };
}

function buildFreshness(
  generatedAt: any,
  now: Date,
  strings: AuraStrings,
): {
  label: string;
  tone: AuraTone;
} {
  const date = parseDate(generatedAt);
  if (!date) {
    return { label: strings.unavailable, tone: "neutral" };
  }
  const deltaMs = Math.max(0, now.getTime() - date.getTime());
  const deltaMinutes = Math.round(deltaMs / 60_000);
  if (deltaMinutes <= 1) {
    return { label: strings.lastUpdatedNow, tone: "safe" };
  }
  if (deltaMinutes < 60) {
    return {
      label: `${deltaMinutes} ${strings.minutesAgo}`,
      tone: deltaMinutes <= 15 ? "safe" : "neutral",
    };
  }
  const deltaHours = Math.round(deltaMinutes / 60);
  if (deltaHours < 24) {
    return {
      label: `${deltaHours} ${strings.hoursAgo}`,
      tone: deltaHours <= 6 ? "warning" : "danger",
    };
  }
  const deltaDays = Math.round(deltaHours / 24);
  return {
    label: `${deltaDays} ${strings.daysAgo}`,
    tone: "danger",
  };
}

function buildTimezones(meta: Record<string, any>, now: Date, locale: string): AuraTimezoneVm[] {
  const rows = Array.isArray(meta.timezones)
    ? meta.timezones
        .filter((row: any) => typeof row === "object" && row !== null)
        .map((row: any) => ({
          timezone: String(row.timezone || row.offset || meta.home_position?.timezone || "HOME"),
          date: String(row.date || ""),
          time: String(row.time || ""),
          iso: String(row.iso || ""),
        }))
        .filter((row: AuraTimezoneVm) => row.timezone || row.time)
    : [];

  if (rows.length > 0) return rows;

  return [
    {
      timezone: String(meta.home_position?.timezone || "HOME"),
      date: new Intl.DateTimeFormat(locale, { day: "2-digit", month: "short" }).format(now),
      time: new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit", hour12: false }).format(now),
      iso: now.toISOString(),
    },
  ];
}

function buildLocation(homePosition: any, _locale: string): string {
  if (!homePosition || typeof homePosition !== "object") return "Home";
  const preferredLabel = firstPresentString(
    homePosition.label,
    homePosition.name,
    homePosition.city,
    homePosition.location,
    homePosition.timezone,
  );
  const timezone = preferredLabel || "Home";
  return timezone;
}

function resolveWeatherIcon(meta: Record<string, any>, firstForecast: any): string | null {
  const icon = meta?.icons?.weather_current || {};
  return firstUrl(
    icon.icon_webp_url,
    icon.icon_gif_url,
    icon.icon_url,
    icon.icon_external_url,
    firstForecast?.weather_icon_webp_url,
    firstForecast?.weather_icon_gif_url,
    firstForecast?.weather_icon_url,
  );
}

function resolveForecastIcon(day: any): string | null {
  return firstUrl(day?.weather_icon_webp_url, day?.weather_icon_url, day?.weather_icon_gif_url);
}

function beachVerdictTone(flag: any, currentRisk: any, comfort: number | null): AuraTone {
  const flagToken = normalizeToken(flag);
  if (flagToken.includes("red")) return "danger";
  if (flagToken.includes("yellow") || flagToken.includes("orange")) return "warning";
  if (flagToken.includes("green")) return "safe";
  const riskTone = strongestTone([currentRisk]);
  if (riskTone !== "neutral") return riskTone;
  if (comfort !== null) {
    if (comfort >= 7) return "safe";
    if (comfort >= 5) return "warning";
    return "danger";
  }
  return "neutral";
}

function strongestTone(values: any[]): AuraTone {
  let maxTone: AuraTone = "neutral";
  for (const value of values) {
    const tone = toneFromValue(value);
    if (toneWeight(tone) > toneWeight(maxTone)) {
      maxTone = tone;
    }
  }
  return maxTone;
}

function toneWeight(tone: AuraTone): number {
  switch (tone) {
    case "danger":
      return 4;
    case "warning":
      return 3;
    case "safe":
      return 2;
    case "info":
      return 1;
    default:
      return 0;
  }
}

function toneFromValue(value: any): AuraTone {
  if (isMissing(value)) return "neutral";
  if (typeof value === "boolean") return value ? "safe" : "neutral";
  const numeric = toNumber(value);
  if (numeric !== null) {
    if (numeric >= 80) return "danger";
    if (numeric >= 50) return "warning";
    if (numeric > 0 && numeric <= 20) return "safe";
    return "neutral";
  }
  const token = normalizeToken(value);
  if (
    token.includes("extreme") ||
    token.includes("very_high") ||
    token.includes("danger") ||
    token.includes("red") ||
    token.includes("warning")
  ) {
    return "danger";
  }
  if (
    token.includes("high") ||
    token.includes("orange") ||
    token.includes("advisory") ||
    token.includes("watch") ||
    token.includes("partial") ||
    token.includes("later")
  ) {
    return "warning";
  }
  if (
    token.includes("ok") ||
    token.includes("green") ||
    token.includes("healthy") ||
    token.includes("low") ||
    token.includes("safe") ||
    token.includes("now")
  ) {
    return "safe";
  }
  return "neutral";
}

function displayEntityValue(
  entity: AuraEntityRecord | undefined,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
  options: { temperature?: boolean; unitOverride?: string } = {},
): string | null {
  if (!entity) return null;
  if (options.temperature) {
    return formatTemperature(entity.value, lang, strings, locale);
  }
  const numeric = toNumber(entity.value);
  const unit = options.unitOverride || entity.unit;
  if (numeric !== null) {
    return unit ? `${formatNumber(numeric, locale, 1)} ${unit}` : formatNumber(numeric, locale, 1);
  }
  const rendered = presentMaybe(entity.value, lang, strings);
  if (!rendered) return null;
  return rendered;
}

function formatTemperature(value: any, lang: AuraLang, strings: AuraStrings, locale: string): string {
  const numeric = toNumber(value);
  if (numeric === null) return strings.unavailable;
  return `${formatNumber(numeric, locale, 1)}°C`;
}

function formatTemperatureMaybe(value: any, lang: AuraLang, strings: AuraStrings, locale: string): string | null {
  const numeric = toNumber(value);
  if (numeric === null) return null;
  return `${formatNumber(numeric, locale, 1)}°C`;
}

function formatTemperatureRange(
  maxValue: any,
  minValue: any,
  lang: AuraLang,
  strings: AuraStrings,
  locale: string,
): string {
  const max = toNumber(maxValue);
  const min = toNumber(minValue);
  if (max === null && min === null) return strings.unavailable;
  if (max !== null && min !== null) return `${formatNumber(max, locale, 1)}° / ${formatNumber(min, locale, 1)}°`;
  return max !== null ? `${formatNumber(max, locale, 1)}°` : `${formatNumber(min, locale, 1)}°`;
}

function dayLabel(dateRaw: any, index: number, lang: AuraLang, strings: AuraStrings, locale: string): string {
  const date = parseDate(dateRaw);
  if (!date) {
    if (index === 0) return strings.forecast;
    return `${index + 1}`;
  }
  return new Intl.DateTimeFormat(locale, { weekday: "short" }).format(date).replace(/\.$/, "");
}

function numericMetricLine(label: string, value: any, locale: string): string | null {
  const numeric = toNumber(value);
  if (numeric === null) return null;
  return `${label} ${formatNumber(numeric, locale, 1)}`;
}

function compactList(value: any, lang: AuraLang, strings: AuraStrings): string | null {
  if (isMissing(value)) return null;
  const chunks = String(value)
    .split(/[,\n;]/)
    .map((part) => part.trim())
    .filter(Boolean);
  if (chunks.length === 0) return null;
  return chunks.slice(0, 3).join(" · ");
}

function sanitizeWeatherSummary(value: any, lang: AuraLang, strings: AuraStrings): string {
  const raw = present(value, lang, strings);
  if (raw === strings.unavailable) return raw;
  const cleaned = raw
    .replace(/[, ]*-?\d+(?:[.,]\d+)?\s*(?:°\s*[CF]|degC|degF)\b/giu, "")
    .replace(/\s{2,}/g, " ")
    .replace(/[,\s]+$/g, "")
    .trim();
  return cleaned || raw;
}

function firstPresentString(...values: any[]): string | null {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return null;
}

function extractPlanText(plan: any, lang: AuraLang, strings: AuraStrings): string | null {
  if (isMissing(plan)) return null;
  if (typeof plan === "string") return presentMaybe(plan, lang, strings);
  if (typeof plan === "object" && plan !== null) {
    for (const key of ["summary", "headline", "recommendation", "plan", "status", "label"]) {
      if (!isMissing(plan[key])) {
        return presentMaybe(plan[key], lang, strings);
      }
    }
  }
  return null;
}

function present(value: any, lang: AuraLang, strings: AuraStrings): string {
  return presentMaybe(value, lang, strings) || strings.unavailable;
}

function presentMaybe(value: any, lang: AuraLang, strings: AuraStrings): string | null {
  if (value === true) return strings.yes;
  if (value === false) return strings.no;
  if (isMissing(value)) return null;
  if (typeof value === "number") return String(value);
  const raw = String(value).trim();
  if (!raw) return null;
  const token = normalizeToken(raw);
  const mapped = TOKEN_LABELS[lang]?.[token];
  if (mapped) return mapped;
  if (/^[a-z0-9_]+$/i.test(raw)) {
    return humanizeKey(raw);
  }
  return raw;
}

function humanizeKey(value: string): string {
  return value
    .replaceAll(".", " ")
    .replaceAll("_", " ")
    .trim()
    .replace(/\s+/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function normalizeToken(value: any): string {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replaceAll("-", "_")
    .replace(/\s+/g, "_");
}

function truthy(value: any): boolean {
  if (value === true) return true;
  if (value === false || value === null || value === undefined) return false;
  const token = normalizeToken(value);
  return token === "1" || token === "true" || token === "yes" || token === "on" || token === "ready";
}

function firstUrl(...values: any[]): string | null {
  for (const value of values) {
    if (typeof value !== "string") continue;
    const raw = value.trim();
    if (!raw) continue;
    if (raw.startsWith("http://") || raw.startsWith("https://")) return raw;
  }
  return null;
}

function parseDate(value: any): Date | null {
  if (typeof value !== "string" && typeof value !== "number") return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatNumber(value: any, locale: string, maximumFractionDigits = 0): string {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return String(value);
  const rounded = Math.round(numeric * 10) / 10;
  const hasFraction = Math.abs(rounded - Math.round(rounded)) > 0.001;
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: hasFraction && maximumFractionDigits > 0 ? 1 : 0,
    maximumFractionDigits,
  }).format(rounded);
}

function toNumber(value: any): number | null {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function isMissing(value: any): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    return normalized === "" || normalized === "unknown" || normalized === "unavailable" || normalized === "none" || normalized === "null";
  }
  return false;
}

function localeOf(lang: AuraLang): string {
  switch (lang) {
    case "ru":
      return "ru-RU";
    case "ua":
      return "uk-UA";
    case "es":
      return "es-ES";
    default:
      return "en-US";
  }
}

function normalizeLang(value: any): AuraLang {
  const normalized = String(value || "ru").trim().toLowerCase();
  if (normalized === "uk") return "ua";
  if (normalized === "ru" || normalized === "en" || normalized === "ua" || normalized === "es") return normalized;
  return "ru";
}

function normalizeThemeVariant(value: any): AuraThemeVariant {
  const normalized = String(value || "ocean_glass").trim().toLowerCase();
  if (normalized === "aurora_glass" || normalized === "sunset_glass") return normalized;
  return "ocean_glass";
}

function normalizeLayoutMode(value: any): AuraLayoutMode {
  return String(value || "premium").trim().toLowerCase() === "compact" ? "compact" : "premium";
}
