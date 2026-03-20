const I18N = {
  ru: {
    titleDefault: "Берегиня AURA",
    loading: "Загрузка данных внутреннего API AURA...",
    apiError: "Ошибка API",
    nowLabel: "Сейчас",
    todayLabel: "Сегодня",
    tomorrowLabel: "Завтра",
    windLabel: "Ветер",
    rainLabel: "Дождь",
    source: "Источник",
    mode: "Режим",
    refresh: "Обновление",
    generatedAt: "Сгенерировано",
    homeLatitude: "Широта дома",
    homeLongitude: "Долгота дома",
    fetchMain: "Получение weather/marine/air",
    fetchExtra: "Получение jellyfish/mosquito/ticks",
    fetchHazards: "Получение earthquakes/gdacs",
    haOverrides: "HA overrides применено",
    timezones: "Часовые зоны",
    entityTranscript: "Транскрипт сущностей",
    forecast: "Прогноз",
    unavailable: "недоступно",
    clock: "Часы",
    weather: "Погода",
    swipeHint: "Свайп по часам для смены зоны",
    notifyBar: "Риски",
    categories: "Категории",
    details: "Детали",
    close: "Закрыть",
    categorySea: "Море и пляж",
    categoryBio: "Био и аллергии",
    categoryClimate: "Климат-стресс",
    categoryHazards: "ЧС и алерты",
    categoryPlanner: "Планер и персоны",
    emptyCategory: "Нет данных в этой категории",
    categoryIndex: "индекс"
  },
  en: {
    titleDefault: "Beregynya AURA",
    loading: "Loading internal AURA API data...",
    apiError: "API error",
    nowLabel: "Now",
    todayLabel: "Today",
    tomorrowLabel: "Tomorrow",
    windLabel: "Wind",
    rainLabel: "Rain",
    source: "Source",
    mode: "Mode",
    refresh: "Refresh",
    generatedAt: "Generated at",
    homeLatitude: "Home latitude",
    homeLongitude: "Home longitude",
    fetchMain: "Fetch weather/marine/air",
    fetchExtra: "Fetch jellyfish/mosquito/ticks",
    fetchHazards: "Fetch earthquakes/gdacs",
    haOverrides: "HA overrides applied",
    timezones: "Timezones",
    entityTranscript: "Entity Transcript",
    forecast: "Forecast",
    unavailable: "unavailable",
    clock: "Clock",
    weather: "Weather",
    swipeHint: "Swipe clock to switch timezone",
    notifyBar: "Risk bar",
    categories: "Categories",
    details: "Details",
    close: "Close",
    categorySea: "Sea & beach",
    categoryBio: "Bio & allergy",
    categoryClimate: "Climate stress",
    categoryHazards: "Hazards & alerts",
    categoryPlanner: "Planner & personas",
    emptyCategory: "No data in this category",
    categoryIndex: "index"
  },
  ua: {
    titleDefault: "Берегиня AURA",
    loading: "Завантаження даних внутрішнього API AURA...",
    apiError: "Помилка API",
    nowLabel: "Зараз",
    todayLabel: "Сьогодні",
    tomorrowLabel: "Завтра",
    windLabel: "Вітер",
    rainLabel: "Дощ",
    source: "Джерело",
    mode: "Режим",
    refresh: "Оновлення",
    generatedAt: "Згенеровано",
    homeLatitude: "Широта дому",
    homeLongitude: "Довгота дому",
    fetchMain: "Отримання weather/marine/air",
    fetchExtra: "Отримання jellyfish/mosquito/ticks",
    fetchHazards: "Отримання earthquakes/gdacs",
    haOverrides: "HA overrides застосовано",
    timezones: "Часові пояси",
    entityTranscript: "Транскрипт сутностей",
    forecast: "Прогноз",
    unavailable: "недоступно",
    clock: "Годинник",
    weather: "Погода",
    swipeHint: "Свайп по годиннику для зміни зони",
    notifyBar: "Ризики",
    categories: "Категорії",
    details: "Деталі",
    close: "Закрити",
    categorySea: "Море і пляж",
    categoryBio: "Біо та алергії",
    categoryClimate: "Клімат-стрес",
    categoryHazards: "НС і попередження",
    categoryPlanner: "Планер і персони",
    emptyCategory: "Немає даних у цій категорії",
    categoryIndex: "індекс"
  },
  es: {
    titleDefault: "Beregynya AURA",
    loading: "Cargando datos del API interno AURA...",
    apiError: "Error de API",
    nowLabel: "Ahora",
    todayLabel: "Hoy",
    tomorrowLabel: "Mañana",
    windLabel: "Viento",
    rainLabel: "Lluvia",
    source: "Fuente",
    mode: "Modo",
    refresh: "Actualización",
    generatedAt: "Generado",
    homeLatitude: "Latitud de casa",
    homeLongitude: "Longitud de casa",
    fetchMain: "Fetch weather/marine/air",
    fetchExtra: "Fetch jellyfish/mosquito/ticks",
    fetchHazards: "Fetch earthquakes/gdacs",
    haOverrides: "HA overrides aplicados",
    timezones: "Zonas horarias",
    entityTranscript: "Transcripción de entidades",
    forecast: "Pronóstico",
    unavailable: "no disponible",
    clock: "Reloj",
    weather: "Clima",
    swipeHint: "Desliza el reloj para cambiar zona",
    notifyBar: "Riesgos",
    categories: "Categorías",
    details: "Detalles",
    close: "Cerrar",
    categorySea: "Mar y playa",
    categoryBio: "Bio y alergias",
    categoryClimate: "Estrés climático",
    categoryHazards: "Riesgos y alertas",
    categoryPlanner: "Planner y personas",
    emptyCategory: "Sin datos en esta categoría",
    categoryIndex: "índice"
  }
};
const _escapeHtml = (raw) => String(raw ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
const AURA_TAG_NAME = "bereginya-aura";
class BeregynyaAuraCard extends HTMLElement {
  _config = {};
  _hass = null;
  _snapshot = null;
  _error = null;
  _lastRefreshTs = 0;
  _refreshPromise = null;
  _root;
  _markdownCard = null;
  _activeCategory = null;
  _timezoneIndex = 0;
  _clockTouchStartX = null;
  static getStubConfig() {
    return {
      type: "custom:bereginya-aura",
      title: "Beregynya AURA"
    };
  }
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._root = document.createElement("div");
    this.shadowRoot?.appendChild(this._root);
  }
  _ensureRuntimeState() {
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }
    if (!(this._root instanceof HTMLElement)) {
      this._root = document.createElement("div");
    }
    if (this.shadowRoot && !this.shadowRoot.contains(this._root)) {
      this.shadowRoot.innerHTML = "";
      this.shadowRoot.appendChild(this._root);
    }
    if (!this._config || typeof this._config !== "object") this._config = {};
    if (typeof this._lastRefreshTs !== "number") this._lastRefreshTs = 0;
    if (this._refreshPromise === void 0) this._refreshPromise = null;
    if (this._snapshot === void 0) this._snapshot = null;
    if (this._error === void 0) this._error = null;
    if (typeof this._timezoneIndex !== "number") this._timezoneIndex = 0;
    if (this._activeCategory === void 0) this._activeCategory = null;
    if (this._clockTouchStartX === void 0) this._clockTouchStartX = null;
    if (this._markdownCard === void 0) this._markdownCard = null;
  }
  setConfig(config) {
    this._ensureRuntimeState();
    if (!config || typeof config !== "object") {
      this._config = {};
    } else {
      this._config = config;
    }
    if (this._hass) {
      this._render();
    }
  }
  set hass(hass) {
    this._ensureRuntimeState();
    this._hass = hass;
    const now = Date.now();
    if (!this._snapshot || now - this._lastRefreshTs > this._refreshIntervalMs()) {
      void this._refresh();
    }
    this._render();
  }
  getCardSize() {
    return this._debugEnabled() ? 10 : 4;
  }
  getGridOptions() {
    return {
      rows: this._debugEnabled() ? 8 : 4,
      columns: 12,
      min_rows: this._debugEnabled() ? 6 : 4,
      min_columns: 12
    };
  }
  _lang() {
    const configured = String(this._config.lang || this._hass?.language || "ru").trim().toLowerCase();
    if (configured === "uk") return "ua";
    if (configured === "ru" || configured === "en" || configured === "ua" || configured === "es") {
      return configured;
    }
    return "ru";
  }
  _t(key) {
    return I18N[this._lang()][key];
  }
  _value(value) {
    if (value === null || value === void 0 || value === "unavailable") {
      return this._t("unavailable");
    }
    return String(value);
  }
  _debugEnabled() {
    if (typeof this._config.debug === "boolean") {
      return this._config.debug;
    }
    const metaDebug = this._snapshot?.meta?.debug;
    if (typeof metaDebug === "boolean") {
      return metaDebug;
    }
    if (typeof metaDebug === "string") {
      const normalized = metaDebug.trim().toLowerCase();
      return normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on";
    }
    return false;
  }
  async _refresh() {
    if (!this._hass || this._refreshPromise) {
      return;
    }
    let endpoint = "bereginya_aura/v1/snapshot";
    if (this._config.force_refresh === true) {
      endpoint += "?force_refresh=1";
    }
    this._refreshPromise = this._hass.callApi("GET", endpoint).then((snapshot) => {
      this._snapshot = snapshot;
      this._error = null;
      this._lastRefreshTs = Date.now();
    }).catch((err) => {
      this._error = this._formatError(err);
    }).finally(() => {
      this._refreshPromise = null;
      this._render();
    });
  }
  _formatError(err) {
    if (!err) {
      return "unknown_error";
    }
    if (typeof err === "string") {
      return err;
    }
    if (typeof err?.message === "string" && err.message.trim()) {
      return err.message;
    }
    if (typeof err?.body?.message === "string" && err.body.message.trim()) {
      return err.body.message;
    }
    if (typeof err?.body?.error === "string" && err.body.error.trim()) {
      return err.body.error;
    }
    if (typeof err?.error === "string" && err.error.trim()) {
      return err.error;
    }
    try {
      return JSON.stringify(err);
    } catch (_jsonError) {
      return String(err);
    }
  }
  _refreshIntervalMs() {
    const configured = Number(this._config.refresh_seconds ?? 120);
    if (!Number.isFinite(configured)) {
      return 12e4;
    }
    return Math.max(15e3, configured * 1e3);
  }
  _url(value) {
    if (typeof value !== "string") {
      return null;
    }
    const raw = value.trim();
    if (!raw) {
      return null;
    }
    if (raw.startsWith("http://") || raw.startsWith("https://")) {
      return raw;
    }
    return null;
  }
  _entityIconSuffix(entity) {
    if (this._config.show_icons !== true) {
      return entity.icon ? ` _[${entity.icon}]_` : "";
    }
    const preferGif = this._config.prefer_gif_icons !== false;
    const gif = this._url(entity.icon_gif_url);
    const img = this._url(entity.icon_url) || this._url(entity.icon_webp_url);
    const ext = this._url(entity.icon_external_url);
    const primary = preferGif ? gif || img || ext : img || gif || ext;
    const links = [];
    if (primary) links.push(`[icon](${primary})`);
    if (gif && gif !== primary) links.push(`[gif](${gif})`);
    if (img && img !== primary) links.push(`[img](${img})`);
    if (ext && ext !== primary && ext !== gif && ext !== img) links.push(`[src](${ext})`);
    const mdi = entity.icon ? ` \`${entity.icon}\`` : "";
    if (links.length > 0) {
      return ` _${links.join(" / ")}_${mdi}`;
    }
    return entity.icon ? ` _[${entity.icon}]_` : "";
  }
  _forecastIconSuffix(day) {
    if (this._config.show_icons !== true) {
      return "";
    }
    const preferGif = this._config.prefer_gif_icons !== false;
    const gif = this._url(day.weather_icon_gif_url);
    const img = this._url(day.weather_icon_url);
    const primary = preferGif ? gif || img : img || gif;
    if (!primary) return "";
    const extra = gif && img && gif !== img ? ` / [img](${img})` : "";
    return ` _[weather](${primary})${extra}_`;
  }
  _entities() {
    return Array.isArray(this._snapshot?.entities) ? this._snapshot.entities : [];
  }
  _entityMap() {
    const map = /* @__PURE__ */ new Map();
    for (const entity of this._entities()) {
      const entityId = String(entity?.entity_id || "");
      if (entityId) {
        map.set(entityId, entity);
      }
    }
    return map;
  }
  _entityValue(entityMap, entityId) {
    return entityMap.get(entityId)?.value;
  }
  _entityNumeric(entityMap, entityId) {
    const value = this._entityValue(entityMap, entityId);
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  _numberLocale() {
    switch (this._lang()) {
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
  _formatNumber(value, maximumFractionDigits = 1) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return null;
    }
    const rounded = Math.round(numeric * 10) / 10;
    const hasFraction = Math.abs(rounded - Math.round(rounded)) > 0.01;
    return new Intl.NumberFormat(this._numberLocale(), {
      minimumFractionDigits: hasFraction ? 1 : 0,
      maximumFractionDigits
    }).format(rounded);
  }
  _formatTemp(value, unit = "°") {
    const formatted = this._formatNumber(value, 1);
    return formatted ? `${formatted}${unit}` : this._t("unavailable");
  }
  _formatTempRange(maxRaw, minRaw) {
    const max = this._formatNumber(maxRaw, 1);
    const min = this._formatNumber(minRaw, 1);
    if (max && min) return `${max}° / ${min}°`;
    if (max) return `${max}°`;
    if (min) return `${min}°`;
    return this._t("unavailable");
  }
  _forecastDayLabel(dateRaw, fallbackIndex) {
    const parsed = typeof dateRaw === "string" || typeof dateRaw === "number" ? new Date(dateRaw) : null;
    if (parsed && !Number.isNaN(parsed.getTime())) {
      return new Intl.DateTimeFormat(this._numberLocale(), { weekday: "short" }).format(parsed).replace(/\.$/, "").trim().toLowerCase();
    }
    if (fallbackIndex === 0) return this._t("todayLabel");
    if (fallbackIndex === 1) return this._t("tomorrowLabel");
    return `${fallbackIndex + 1}`;
  }
  _forecastDayIcon(day) {
    const gif = this._url(day?.weather_icon_gif_url);
    const img = this._url(day?.weather_icon_url) || this._url(day?.weather_icon_webp_url);
    return img || gif;
  }
  _riskScore(value) {
    if (value === null || value === void 0) {
      return 0;
    }
    const numeric = Number(value);
    if (Number.isFinite(numeric)) {
      if (numeric <= 1) return Math.round(Math.max(0, Math.min(1, numeric)) * 100);
      return Math.round(Math.max(0, Math.min(100, numeric)));
    }
    const token = String(value).trim().toLowerCase();
    if (token.includes("extreme") || token.includes("very_high") || token.includes("red")) return 92;
    if (token.includes("high") || token.includes("orange") || token.includes("danger")) return 76;
    if (token.includes("moderate") || token.includes("medium") || token.includes("yellow")) return 55;
    if (token.includes("low") || token.includes("green")) return 32;
    return 15;
  }
  _riskColor(score) {
    if (score >= 80) return "#ef5f5f";
    if (score >= 60) return "#f0a84e";
    if (score >= 35) return "#d8c852";
    return "#58b77a";
  }
  _timezones() {
    const zonesRaw = Array.isArray(this._snapshot?.meta?.timezones) ? this._snapshot.meta.timezones : [];
    const zones = zonesRaw.filter((row) => typeof row === "object" && row !== null).map((row) => ({
      timezone: String(row.timezone || row.offset || "HOME"),
      date: String(row.date || ""),
      time: String(row.time || ""),
      iso: String(row.iso || "")
    })).filter((row) => row.timezone || row.time);
    if (zones.length > 0) {
      return zones;
    }
    const generated = String(this._snapshot?.meta?.generated_at || "");
    const fallback = generated ? new Date(generated) : /* @__PURE__ */ new Date();
    return [
      {
        timezone: String(this._snapshot?.meta?.home_position?.timezone || "HOME"),
        date: fallback.toISOString().slice(0, 10),
        time: fallback.toTimeString().slice(0, 5),
        iso: fallback.toISOString()
      }
    ];
  }
  _activeTimezoneRow() {
    const zones = this._timezones();
    if (this._timezoneIndex >= zones.length) {
      this._timezoneIndex = 0;
    }
    if (this._timezoneIndex < 0) {
      this._timezoneIndex = zones.length - 1;
    }
    return zones[this._timezoneIndex];
  }
  _switchTimezone(direction) {
    const zones = this._timezones();
    if (zones.length <= 1) return;
    this._timezoneIndex = (this._timezoneIndex + direction + zones.length) % zones.length;
    this._render();
  }
  _categoryDefs() {
    return [
      {
        id: "sea_beach",
        icon: "🌊",
        title: this._t("categorySea"),
        match: (id) => id.startsWith("sensor.sea_temperature_") || id.startsWith("sensor.wave_") || id.startsWith("sensor.beach_") || id.startsWith("sensor.jellyfish_") || id.startsWith("sensor.rip_current_") || id.startsWith("sensor.tide_") || id.startsWith("sensor.ocean_current_") || id === "sensor.current_risk" || id.startsWith("sensor.algae_")
      },
      {
        id: "bio_allergy",
        icon: "🦟",
        title: this._t("categoryBio"),
        match: (id) => id.startsWith("sensor.pollen_") || id === "sensor.ambrosia_risk" || id === "sensor.allergy_index" || id === "sensor.asthma_risk" || id.startsWith("sensor.tiger_mosquito_") || id === "sensor.mosquito_index" || id.startsWith("sensor.tick_") || id.startsWith("sensor.bite_")
      },
      {
        id: "climate_stress",
        icon: "☀️",
        title: this._t("categoryClimate"),
        match: (id) => id.startsWith("sensor.uv_dose_") || id.startsWith("sensor.astro_uv_") || id === "sensor.astro_solar_elevation" || id.startsWith("sensor.heat_") || id === "sensor.wbgt_c" || id.startsWith("sensor.dehydration_") || id.startsWith("sensor.thunderstorm_") || id.startsWith("sensor.air_quality_") || id.startsWith("sensor.saharan_dust_") || id.startsWith("sensor.smoke_")
      },
      {
        id: "hazards_alerts",
        icon: "🚨",
        title: this._t("categoryHazards"),
        match: (id) => id.startsWith("sensor.earthquake_") || id.startsWith("sensor.wildfire_") || id.startsWith("sensor.hazard_") || id.startsWith("sensor.cap_")
      },
      {
        id: "planner_personal",
        icon: "📅",
        title: this._t("categoryPlanner"),
        match: (id) => id.startsWith("sensor.aura_")
      }
    ];
  }
  _categorySummary(id, entityMap, forecast) {
    if (id === "sea_beach") {
      const beachScore = this._entityNumeric(entityMap, "sensor.beach_comfort_index") ?? Number(forecast[0]?.beach_score ?? NaN);
      const risk = this._entityValue(entityMap, "sensor.current_risk") ?? this._entityValue(entityMap, "sensor.beach_danger_index");
      if (beachScore !== null && Number.isFinite(beachScore)) {
        return {
          primary: `${beachScore}/10`,
          secondary: this._value(risk),
          score: Math.max(0, Math.min(100, Math.round(beachScore * 10)))
        };
      }
      return {
        primary: this._value(risk),
        secondary: this._t("categoryIndex"),
        score: this._riskScore(risk)
      };
    }
    if (id === "bio_allergy") {
      const bite = this._entityNumeric(entityMap, "sensor.bite_index");
      const allergy = this._entityNumeric(entityMap, "sensor.allergy_index");
      const risk = this._entityValue(entityMap, "sensor.bite_risk") ?? this._entityValue(entityMap, "sensor.asthma_risk");
      const base = bite ?? allergy;
      if (base !== null) {
        return {
          primary: `${Math.round(base)}/100`,
          secondary: this._value(risk),
          score: Math.max(0, Math.min(100, Math.round(base)))
        };
      }
      return { primary: this._value(risk), secondary: this._t("categoryIndex"), score: this._riskScore(risk) };
    }
    if (id === "climate_stress") {
      const dehydration = this._entityNumeric(entityMap, "sensor.dehydration_index");
      const wbgt = this._entityNumeric(entityMap, "sensor.wbgt_c");
      const risk = this._entityValue(entityMap, "sensor.uv_dose_status") ?? this._entityValue(entityMap, "sensor.thunderstorm_risk");
      if (dehydration !== null) {
        return {
          primary: `${Math.round(dehydration)}/100`,
          secondary: this._value(risk),
          score: Math.max(0, Math.min(100, Math.round(dehydration)))
        };
      }
      if (wbgt !== null) {
        const wbgtScore = Math.max(0, Math.min(100, Math.round((wbgt - 15) / 20 * 100)));
        return { primary: `${wbgt}°`, secondary: this._value(risk), score: wbgtScore };
      }
      return { primary: this._value(risk), secondary: this._t("categoryIndex"), score: this._riskScore(risk) };
    }
    if (id === "hazards_alerts") {
      const hazards = this._entityNumeric(entityMap, "sensor.hazard_active_events_global");
      const cap = this._entityNumeric(entityMap, "sensor.cap_alerts_active");
      const risk = this._entityValue(entityMap, "sensor.cap_alert_risk") ?? this._entityValue(entityMap, "sensor.earthquake_risk");
      const count = hazards ?? cap;
      if (count !== null) {
        return {
          primary: String(Math.round(count)),
          secondary: this._value(risk),
          score: this._riskScore(risk)
        };
      }
      return { primary: this._value(risk), secondary: this._t("categoryIndex"), score: this._riskScore(risk) };
    }
    const plan = this._entityValue(entityMap, "sensor.aura_daily_plan_status");
    const trend = this._entityValue(entityMap, "sensor.aura_now_vs_3h_summary");
    return {
      primary: this._value(plan),
      secondary: this._value(trend),
      score: this._riskScore(plan)
    };
  }
  _buildForecastSvg(forecast) {
    const rows = forecast.filter((day) => Number.isFinite(Number(day?.temp_min)) && Number.isFinite(Number(day?.temp_max))).slice(0, 7);
    if (rows.length === 0) {
      return `<div class="graph-empty">${_escapeHtml(this._t("unavailable"))}</div>`;
    }
    const width = 520;
    const height = 132;
    const top = 12;
    const bottom = 28;
    const left = 20;
    const right = 20;
    const values = [];
    for (const row of rows) {
      values.push(Number(row.temp_min));
      values.push(Number(row.temp_max));
    }
    const max = Math.max(...values);
    const min = Math.min(...values);
    const span = Math.max(1, max - min);
    const xStep = rows.length > 1 ? (width - left - right) / (rows.length - 1) : 0;
    const yOf = (value) => top + (max - value) / span * (height - top - bottom);
    const maxPoints = rows.map((row, idx) => `${(left + idx * xStep).toFixed(1)},${yOf(Number(row.temp_max)).toFixed(1)}`).join(" ");
    const minPoints = rows.map((row, idx) => `${(left + idx * xStep).toFixed(1)},${yOf(Number(row.temp_min)).toFixed(1)}`).join(" ");
    const labels = rows.map((row, idx) => {
      const dateLabel = String(row.date || "").slice(5);
      const x = (left + idx * xStep).toFixed(1);
      return `<text x="${x}" y="${height - 8}" text-anchor="middle" class="graph-day">${_escapeHtml(dateLabel)}</text>`;
    }).join("");
    const rainBars = rows.map((row, idx) => {
      const rain = Math.max(0, Math.min(100, Number(row.rain_probability_max || 0)));
      const barHeight = rain / 100 * 18;
      const x = left + idx * xStep - 6;
      const y = height - bottom + (18 - barHeight);
      return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="12" height="${barHeight.toFixed(1)}" rx="2" class="graph-rain"/>`;
    }).join("");
    return `
      <svg viewBox="0 0 ${width} ${height}" class="forecast-svg" aria-hidden="true">
        <line x1="${left}" y1="${top}" x2="${width - right}" y2="${top}" class="graph-grid"/>
        <line x1="${left}" y1="${((height - bottom + top) / 2).toFixed(1)}" x2="${width - right}" y2="${((height - bottom + top) / 2).toFixed(1)}" class="graph-grid"/>
        <line x1="${left}" y1="${height - bottom}" x2="${width - right}" y2="${height - bottom}" class="graph-grid"/>
        <polyline points="${maxPoints}" class="graph-max"/>
        <polyline points="${minPoints}" class="graph-min"/>
        ${rainBars}
        ${labels}
      </svg>
    `;
  }
  _getMarkdownCard() {
    if (this._markdownCard === null) {
      this._markdownCard = document.createElement("hui-markdown-card");
    }
    if (typeof this._markdownCard?.setConfig === "function") {
      return this._markdownCard;
    }
    if (customElements.get("hui-markdown-card")) {
      this._markdownCard = document.createElement("hui-markdown-card");
      if (typeof this._markdownCard?.setConfig === "function") {
        return this._markdownCard;
      }
    }
    return null;
  }
  _renderDebugFallback(lines) {
    this._root.innerHTML = `
      <style>
        .debug-fallback {
          font-family: "JetBrains Mono", "Consolas", monospace;
          font-size: 12px;
          line-height: 1.45;
          white-space: pre-wrap;
          background: linear-gradient(160deg, #edf3fb 0%, #e2e9f2 100%);
          color: #243548;
          border-radius: 14px;
          padding: 12px;
        }
      </style>
      <div class="debug-fallback">${_escapeHtml(lines.join("\n"))}</div>
    `;
  }
  _renderDebugMarkdown() {
    this._ensureRuntimeState();
    const title = this._config.title || this._t("titleDefault");
    const lines = [`# ${title}`, ""];
    if (this._error) {
      lines.push(`- ${this._t("apiError")}: \`${this._error}\``);
    } else if (!this._snapshot) {
      lines.push(`- ${this._t("loading")}`);
    } else {
      const meta = this._snapshot.meta || {};
      const home = meta.home_position || {};
      const fetch = meta.fetch || {};
      lines.push(`- ${this._t("source")}: \`${this._value(meta.source)}\``);
      lines.push(`- ${this._t("mode")}: \`${this._value(meta.source_mode)}\``);
      lines.push(`- ${this._t("refresh")}: \`${this._value(meta.refresh_seconds)}s\``);
      lines.push(`- ${this._t("generatedAt")}: \`${this._value(meta.generated_at)}\``);
      lines.push(`- ${this._t("homeLatitude")}: \`${this._value(home.latitude)}\``);
      lines.push(`- ${this._t("homeLongitude")}: \`${this._value(home.longitude)}\``);
      lines.push(
        `- ${this._t("fetchMain")}: \`${this._value(fetch.weather)}\` / \`${this._value(fetch.marine)}\` / \`${this._value(fetch.air_quality)}\``
      );
      lines.push(
        `- ${this._t("fetchExtra")}: \`${this._value(fetch.jellyfish)}\` / \`${this._value(fetch.tiger_mosquito)}\` / \`${this._value(fetch.ticks)}\``
      );
      if (fetch.earthquakes !== void 0 || fetch.gdacs !== void 0) {
        lines.push(
          `- ${this._t("fetchHazards")}: \`${this._value(fetch.earthquakes)}\` / \`${this._value(fetch.gdacs)}\``
        );
      }
      if (meta.ha_overrides) {
        lines.push(
          `- ${this._t("haOverrides")}: \`${this._value(meta.ha_overrides.applied)}\` / \`${this._value(meta.ha_overrides.attempted)}\``
        );
      }
      const zones = Array.isArray(meta.timezones) ? meta.timezones : [];
      if (zones.length > 0) {
        const compact = zones.map((z) => `${this._value(z.timezone)} ${this._value(z.time)}`).join(" | ");
        lines.push(`- ${this._t("timezones")}: ${compact}`);
      }
      lines.push("");
      lines.push(`## ${this._t("entityTranscript")}`);
      const entities = this._entities();
      for (const entity of entities) {
        const unit = entity.unit ? ` ${entity.unit}` : "";
        const source = entity.source ? ` _(source: ${entity.source})_` : "";
        const sourceEntity = entity.source_entity ? ` _(${entity.source_entity})_` : "";
        const icon = this._entityIconSuffix(entity);
        lines.push(
          `- \`${entity.entity_id}\`: **${this._value(entity.value)}${unit}**${source}${sourceEntity}${icon}`
        );
      }
      const daily = Array.isArray(this._snapshot.forecast_daily) ? this._snapshot.forecast_daily : [];
      if (daily.length > 0) {
        lines.push("");
        lines.push(`## ${this._t("forecast")} ${daily.length}d`);
        for (const day of daily) {
          const forecastIcon = this._forecastIconSuffix(day);
          lines.push(
            `- \`${this._value(day.date)}\`${forecastIcon}: ${this._value(day.temp_min)}/${this._value(day.temp_max)} degC, rain ${this._value(day.rain_probability_max)}% (${this._value(day.rain_sum_mm)} mm), UV ${this._value(day.uv_max)}, sea ${this._value(day.sea_temp_avg)} degC, AQI ${this._value(day.aqi_max)}, allergy ${this._value(day.allergy_index)}/100, asthma ${this._value(day.asthma_risk)}, beach ${this._value(day.beach_score)}/10 (${this._value(day.beach_flag)}), mosquito ${this._value(day.mosquito_risk_est)}, jellyfish ${this._value(day.jellyfish_risk_est)}, ticks ${this._value(day.tick_risk_est)}`
          );
        }
      }
    }
    const markdownCard = this._getMarkdownCard();
    if (!markdownCard) {
      this._renderDebugFallback(lines);
      return;
    }
    if (!this._root.contains(markdownCard)) {
      this._root.innerHTML = "";
      this._root.appendChild(markdownCard);
    }
    markdownCard.setConfig({
      type: "markdown",
      content: lines.join("\n")
    });
    if (this._hass) {
      markdownCard.hass = this._hass;
    }
  }
  _bindStructuredEvents() {
    const prevBtn = this._root.querySelector("[data-tz-nav='prev']");
    const nextBtn = this._root.querySelector("[data-tz-nav='next']");
    prevBtn?.addEventListener("click", () => this._switchTimezone(-1));
    nextBtn?.addEventListener("click", () => this._switchTimezone(1));
    const clockPanel = this._root.querySelector("[data-clock-panel='1']");
    clockPanel?.addEventListener(
      "touchstart",
      (event) => {
        if (event.touches.length === 1) {
          this._clockTouchStartX = event.touches[0].clientX;
        }
      },
      { passive: true }
    );
    clockPanel?.addEventListener(
      "touchend",
      (event) => {
        if (this._clockTouchStartX === null || event.changedTouches.length !== 1) return;
        const delta = event.changedTouches[0].clientX - this._clockTouchStartX;
        this._clockTouchStartX = null;
        if (Math.abs(delta) < 24) return;
        this._switchTimezone(delta < 0 ? 1 : -1);
      },
      { passive: true }
    );
    this._root.querySelectorAll("[data-category]").forEach((button) => {
      button.addEventListener("click", () => {
        const categoryId = String(button.dataset.category || "");
        this._activeCategory = categoryId;
        this._render();
      });
    });
    const backdrop = this._root.querySelector("[data-modal-backdrop='1']");
    const modal = this._root.querySelector("[data-modal-card='1']");
    const close = this._root.querySelector("[data-modal-close='1']");
    close?.addEventListener("click", () => {
      this._activeCategory = null;
      this._render();
    });
    backdrop?.addEventListener("click", () => {
      this._activeCategory = null;
      this._render();
    });
    modal?.addEventListener("click", (event) => {
      event.stopPropagation();
    });
  }
  _renderStructuredSkeleton() {
    this._root.innerHTML = `
      <style>${this._styles()}</style>
      <div class="aura-shell skeleton-shell" aria-hidden="true">
        <div class="top-row">
          <div class="clock-card skeleton-card">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long"></div>
          </div>
          <div class="weather-card skeleton-card">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line long"></div>
            <div class="skeleton-line medium"></div>
          </div>
        </div>
        <div class="divider"></div>
        <div class="notify-bar">
          <div class="notify-items">
            <div class="notify-chip skeleton-chip"></div>
            <div class="notify-chip skeleton-chip"></div>
            <div class="notify-chip skeleton-chip"></div>
            <div class="notify-chip skeleton-chip"></div>
            <div class="notify-chip skeleton-chip"></div>
            <div class="notify-chip skeleton-chip"></div>
          </div>
        </div>
        <div class="divider"></div>
        <div class="category-section">
          <div class="category-grid">
            <div class="category-btn skeleton-btn"></div>
            <div class="category-btn skeleton-btn"></div>
            <div class="category-btn skeleton-btn"></div>
            <div class="category-btn skeleton-btn"></div>
            <div class="category-btn skeleton-btn"></div>
          </div>
        </div>
      </div>
    `;
  }
  _renderStructuredCard() {
    this._ensureRuntimeState();
    if (this._markdownCard && this._markdownCard.parentElement === this._root) {
      this._root.removeChild(this._markdownCard);
    }
    if (this._error) {
      this._root.innerHTML = `
        <style>${this._styles()}</style>
        <div class="aura-shell">
          <div class="state-line error">${_escapeHtml(this._t("apiError"))}: ${_escapeHtml(this._error)}</div>
        </div>
      `;
      return;
    }
    if (!this._snapshot) {
      this._renderStructuredSkeleton();
      return;
    }
    const entityMap = this._entityMap();
    const forecast = Array.isArray(this._snapshot.forecast_daily) ? this._snapshot.forecast_daily : [];
    const timezones = this._timezones();
    const currentZone = this._activeTimezoneRow();
    const weatherIcon = this._url(this._snapshot?.meta?.icons?.weather_current?.icon_url) || this._url(this._snapshot?.meta?.icons?.weather_current?.icon_gif_url) || this._forecastDayIcon(forecast[0]);
    const temp = this._entityNumeric(entityMap, "sensor.apparent_temperature") ?? this._entityNumeric(entityMap, "sensor.weather_temperature") ?? Number(forecast[0]?.temp_max ?? NaN);
    const tempView = Number.isFinite(temp) ? `${this._formatTemp(temp, " °C")}` : this._t("unavailable");
    const weatherSummaryRaw = this._entityValue(entityMap, "sensor.weather_summary");
    const weatherSummary = weatherSummaryRaw === null || weatherSummaryRaw === void 0 || weatherSummaryRaw === "unavailable" ? this._t("weather") : String(weatherSummaryRaw);
    const weatherSource = `${this._t("forecast")} AURA`;
    const currentRange = this._formatTempRange(forecast[0]?.temp_max, forecast[0]?.temp_min);
    const weatherForecast = forecast.slice(0, 5).map((day, index) => {
      const dayLabel = this._forecastDayLabel(day?.date, index);
      const dayIcon = this._forecastDayIcon(day);
      const dayHigh = this._formatTemp(day?.temp_max);
      const dayLow = this._formatTemp(day?.temp_min);
      return `<div class="weather-day">
          <div class="weather-day-label">${_escapeHtml(dayLabel)}</div>
          ${dayIcon ? `<img class="weather-day-icon" src="${dayIcon}" alt="${_escapeHtml(dayLabel)}"/>` : `<div class="weather-day-icon placeholder">⛅</div>`}
          <div class="weather-day-high">${_escapeHtml(dayHigh)}</div>
          <div class="weather-day-low">${_escapeHtml(dayLow)}</div>
        </div>`;
    }).join("");
    const notifyRows = [
      { icon: "☀️", label: "UV", value: this._entityValue(entityMap, "sensor.uv_dose_status") },
      { icon: "⚡", label: "Storm", value: this._entityValue(entityMap, "sensor.thunderstorm_risk") },
      { icon: "🦟", label: "Bite", value: this._entityValue(entityMap, "sensor.bite_risk") },
      { icon: "🌫️", label: "Smoke", value: this._entityValue(entityMap, "sensor.smoke_transport_risk") },
      { icon: "🚨", label: "CAP", value: this._entityValue(entityMap, "sensor.cap_alert_risk") },
      { icon: "🌊", label: "Sea", value: this._entityValue(entityMap, "sensor.current_risk") }
    ];
    const notifyHtml = notifyRows.map((row) => {
      const score = this._riskScore(row.value);
      const color = this._riskColor(score);
      return `<div class="notify-chip">
          <span class="notify-icon" title="${_escapeHtml(row.label)}: ${_escapeHtml(this._value(row.value))}">${row.icon}</span>
          <span class="notify-dot" style="background:${color};"></span>
        </div>`;
    }).join("");
    const categories = this._categoryDefs();
    const categoryButtons = categories.map((category) => {
      const summary = this._categorySummary(category.id, entityMap, forecast);
      const color = this._riskColor(summary.score);
      return `<button class="category-btn" data-category="${category.id}">
          <span class="category-icon">${category.icon}</span>
          <span class="category-dot" style="background:${color};"></span>
          <div class="category-hover">
            <div class="category-hover-title">${_escapeHtml(category.title)}</div>
            <div class="category-hover-main">${_escapeHtml(summary.primary)}</div>
            <div class="category-hover-sub">${_escapeHtml(summary.secondary)}</div>
          </div>
        </button>`;
    }).join("");
    let modalHtml = "";
    if (this._activeCategory) {
      const category = categories.find((row) => row.id === this._activeCategory);
      if (category) {
        const rows = this._entities().filter((entity) => category.match(String(entity.entity_id || "")));
        const body = rows.length > 0 ? rows.map((entity) => {
          const unit = entity.unit ? ` ${entity.unit}` : "";
          const source = entity.source ? ` (${entity.source})` : "";
          return `<div class="modal-row">
                    <div class="modal-name">${_escapeHtml(entity.name || entity.entity_id)}</div>
                    <div class="modal-meta">${_escapeHtml(entity.entity_id)}</div>
                    <div class="modal-value">${_escapeHtml(this._value(entity.value))}${_escapeHtml(unit)}${_escapeHtml(source)}</div>
                  </div>`;
        }).join("") : `<div class="modal-empty">${_escapeHtml(this._t("emptyCategory"))}</div>`;
        modalHtml = `<div class="modal-backdrop" data-modal-backdrop="1">
          <div class="modal-card" data-modal-card="1">
            <div class="modal-head">
              <div class="modal-title">${category.icon} ${_escapeHtml(category.title)}</div>
              <button class="modal-close" data-modal-close="1">${_escapeHtml(this._t("close"))}</button>
            </div>
            <div class="modal-body">${body}</div>
          </div>
        </div>`;
      }
    }
    this._root.innerHTML = `
      <style>${this._styles()}</style>
      <div class="aura-shell">
        <div class="top-row">
          <div class="clock-card" data-clock-panel="1">
            <div class="clock-zone">${_escapeHtml(currentZone.timezone || "HOME")}</div>
            <div class="clock-time">${_escapeHtml(currentZone.time || "--:--")}</div>
            <div class="clock-controls">
              <button class="clock-btn" data-tz-nav="prev">‹</button>
              <span class="clock-indicator">${this._timezoneIndex + 1}/${timezones.length}</span>
              <button class="clock-btn" data-tz-nav="next">›</button>
            </div>
          </div>
          <div class="weather-card">
            <div class="weather-head">
              <div class="weather-summary-block">
                <div class="weather-summary-main">
                  <div class="weather-icon-frame">
                    ${weatherIcon ? `<img class="weather-icon" src="${weatherIcon}" alt="weather"/>` : `<div class="weather-icon placeholder">⛅</div>`}
                  </div>
                  <div class="weather-summary-copy">
                    <div class="weather-condition">${_escapeHtml(weatherSummary)}</div>
                    <div class="weather-source">${_escapeHtml(weatherSource)}</div>
                  </div>
                </div>
                <div class="weather-current">
                  <div class="weather-current-temp">${_escapeHtml(tempView)}</div>
                  <div class="weather-current-range">${_escapeHtml(currentRange)}</div>
                </div>
              </div>
            </div>
            <div class="weather-forecast-row">
              ${weatherForecast}
            </div>
          </div>
        </div>
        <div class="divider"></div>
        <div class="notify-bar">
          <div class="notify-items">${notifyHtml}</div>
        </div>
        <div class="divider"></div>
        <div class="category-section">
          <div class="category-grid">${categoryButtons}</div>
        </div>
      </div>
      ${modalHtml}
    `;
    this._bindStructuredEvents();
  }
  _styles() {
    return `
      :host {
        display: block;
      }
      .aura-shell {
        --bg: #0a1f2f;
        --ink: #e9f4ff;
        --muted: #8fb2cf;
        --line: rgba(105, 170, 220, 0.35);
        background: #071725;
        border: 1px solid #244a67;
        border-radius: 14px;
        padding: 8px;
        box-shadow: 0 14px 28px rgba(3, 10, 18, 0.48);
        color: var(--ink);
        font-family: "Manrope", "Segoe UI", sans-serif;
        box-sizing: border-box;
      }
      .skeleton-shell {
        position: relative;
        overflow: hidden;
      }
      .skeleton-shell::after {
        content: "";
        position: absolute;
        inset: 0;
        transform: translateX(-100%);
        background: linear-gradient(
          105deg,
          rgba(255, 255, 255, 0) 0%,
          rgba(165, 205, 236, 0.12) 45%,
          rgba(255, 255, 255, 0) 100%
        );
        animation: auraSkeletonShimmer 1300ms infinite;
      }
      .skeleton-card {
        box-shadow: inset 0 0 0 1px #1d3f58;
      }
      .skeleton-line {
        height: 12px;
        border-radius: 8px;
        margin: 10px;
        background: #173954;
      }
      .skeleton-line.short {
        width: 42%;
      }
      .skeleton-line.medium {
        width: 64%;
      }
      .skeleton-line.long {
        width: 84%;
      }
      .skeleton-chip {
        background: #102c41;
        border-color: #2f6485;
      }
      .skeleton-btn {
        pointer-events: none;
        cursor: default;
      }
      @keyframes auraSkeletonShimmer {
        100% {
          transform: translateX(100%);
        }
      }
      .state-line {
        font-size: 13px;
        color: #a5c3dc;
      }
      .state-line.error {
        color: #ff8a8a;
      }
      .top-row {
        display: grid;
        grid-template-columns: 136px minmax(0, 1fr);
        gap: 8px;
        align-items: start;
      }
      .clock-card,
      .weather-card {
        border-radius: 12px;
        background: var(--bg);
        border: 1px solid #2d5775;
        align-self: start;
      }
      .clock-card {
        padding: 10px 10px 8px;
        box-shadow: 0 8px 18px rgba(1, 8, 15, 0.52);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
      }
      .weather-card {
        position: relative;
        overflow: hidden;
        padding: 14px 16px 12px;
        background:
          radial-gradient(circle at 88% 16%, rgba(255, 214, 92, 0.14), transparent 22%),
          linear-gradient(180deg, rgba(20, 47, 67, 0.98), rgba(11, 30, 43, 0.98));
        box-shadow: inset 0 0 0 1px #1d3f58, 0 12px 22px rgba(2, 10, 18, 0.34);
      }
      .clock-zone {
        font-size: 12px;
        color: #92b3ce;
      }
      .clock-time {
        font-size: 26px;
        line-height: 1.1;
        font-weight: 800;
        margin-top: 2px;
        color: #ffffff;
      }
      .clock-controls {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 10px;
      }
      .clock-btn {
        border: 0;
        border-radius: 8px;
        width: 24px;
        height: 24px;
        background: #123247;
        color: #cde7ff;
        border: 1px solid #2e607f;
        cursor: pointer;
      }
      .clock-indicator {
        font-size: 11px;
        color: #90afca;
      }
      .weather-head {
        min-width: 0;
      }
      .weather-summary-block {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 16px;
        align-items: start;
      }
      .weather-summary-main {
        display: grid;
        grid-template-columns: 74px minmax(0, 1fr);
        gap: 14px;
        align-items: start;
      }
      .weather-icon-frame {
        width: 74px;
        height: 74px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .weather-icon {
        width: 74px;
        height: 74px;
        object-fit: contain;
      }
      .weather-icon.placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 38px;
      }
      .weather-summary-copy {
        min-width: 0;
      }
      .weather-condition {
        font-size: 22px;
        line-height: 1.1;
        font-weight: 700;
        color: #f5fbff;
      }
      .weather-source {
        margin-top: 6px;
        font-size: 11px;
        color: #96b8cb;
      }
      .weather-current {
        text-align: right;
        min-width: 0;
      }
      .weather-current-temp {
        font-size: 34px;
        line-height: 1;
        font-weight: 700;
        color: #f7fcff;
      }
      .weather-current-range {
        margin-top: 8px;
        font-size: 14px;
        color: #9fbccc;
      }
      .weather-forecast-row {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 6px;
        margin-top: 14px;
        padding-top: 12px;
        border-top: 1px solid rgba(113, 161, 193, 0.16);
      }
      .weather-day {
        min-width: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
      }
      .weather-day-label {
        font-size: 12px;
        font-weight: 600;
        color: #dcecf6;
        line-height: 1.1;
      }
      .weather-day-icon {
        width: 44px;
        height: 44px;
        margin-top: 10px;
        object-fit: contain;
      }
      .weather-day-icon.placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
      }
      .weather-day-high {
        margin-top: 10px;
        font-size: 15px;
        font-weight: 700;
        color: #f3fbff;
      }
      .weather-day-low {
        margin-top: 4px;
        font-size: 12px;
        color: #98b7c9;
      }
      .divider {
        height: 6px;
        position: relative;
      }
      .divider::before {
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        top: 50%;
        height: 1px;
        background: var(--line);
        transform: translateY(-50%);
      }
      .notify-bar {
        min-height: 0;
      }
      .notify-items {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
      }
      .notify-chip {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 9px;
        font-size: 11px;
        background: #102c41;
        color: #e9f4ff;
        border: 1px solid #2f6485;
        box-shadow: inset 0 0 0 1px #1c3f58;
      }
      .notify-icon {
        font-size: 14px;
      }
      .notify-dot {
        position: absolute;
        right: 4px;
        bottom: 4px;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        border: 1px solid rgba(5, 16, 26, 0.75);
      }
      .category-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 5px;
      }
      .category-btn {
        position: relative;
        border: 1px solid #2b5f81;
        border-radius: 12px;
        padding: 6px;
        text-align: center;
        background: #0f2b40;
        color: #dff1ff;
        box-shadow: inset 0 0 0 1px #1c3f59, inset 0 -8px 14px rgba(3, 12, 20, 0.34);
        cursor: pointer;
        min-height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 130ms ease, border-color 130ms ease, box-shadow 130ms ease;
      }
      .category-btn:hover,
      .category-btn:focus-visible {
        transform: translateY(-2px);
        border-color: #52a9db;
        box-shadow: 0 10px 16px rgba(2, 9, 16, 0.5);
      }
      .category-icon {
        font-size: 20px;
      }
      .category-dot {
        position: absolute;
        top: 6px;
        right: 6px;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        border: 1px solid rgba(5, 14, 22, 0.72);
      }
      .category-hover {
        position: absolute;
        left: 50%;
        bottom: calc(100% + 8px);
        transform: translate(-50%, 6px);
        opacity: 0;
        pointer-events: none;
        min-width: 120px;
        max-width: 180px;
        padding: 6px 8px;
        border-radius: 10px;
        border: 1px solid #4ba5da;
        background: #06111c;
        color: #dff2ff;
        text-align: center;
        box-shadow: 0 10px 18px rgba(2, 10, 18, 0.68);
        transition: opacity 120ms ease, transform 120ms ease;
        z-index: 5;
      }
      .category-btn:hover .category-hover,
      .category-btn:focus-visible .category-hover {
        opacity: 1;
        transform: translate(-50%, 0);
      }
      .category-hover-title {
        font-size: 11px;
        color: #86aecb;
      }
      .category-hover-main {
        margin-top: 2px;
        font-size: 14px;
        font-weight: 800;
        color: #ffffff;
      }
      .category-hover-sub {
        margin-top: 1px;
        font-size: 10px;
        color: #8db1cd;
      }
      .modal-backdrop {
        position: fixed;
        inset: 0;
        z-index: 30;
        background: rgba(21, 30, 40, 0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 12px;
      }
      .modal-card {
        width: min(760px, 100%);
        max-height: min(82vh, 760px);
        overflow: hidden;
        border-radius: 16px;
        background: #eef3fa;
        box-shadow: 0 14px 30px rgba(17, 28, 40, 0.25);
        display: flex;
        flex-direction: column;
      }
      .modal-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        border-bottom: 1px solid rgba(62, 82, 103, 0.16);
      }
      .modal-title {
        font-size: 14px;
        font-weight: 700;
        color: #31465c;
      }
      .modal-close {
        border: 0;
        border-radius: 8px;
        padding: 6px 10px;
        background: #dbe4ef;
        color: #32495f;
        cursor: pointer;
      }
      .modal-body {
        overflow: auto;
        padding: 8px 12px 12px;
      }
      .modal-row {
        border-radius: 10px;
        background: #e3ebf5;
        padding: 8px 10px;
        margin-bottom: 6px;
      }
      .modal-name {
        font-size: 13px;
        font-weight: 700;
        color: #32475c;
      }
      .modal-meta {
        font-size: 10px;
        color: #677d91;
        margin-top: 2px;
      }
      .modal-value {
        margin-top: 4px;
        font-size: 12px;
        color: #40576c;
      }
      .modal-empty {
        font-size: 13px;
        color: #5a7085;
        padding: 8px 2px;
      }
      @media (max-width: 1024px) {
        .category-grid {
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }
      }
      @media (max-width: 720px) {
        .top-row {
          grid-template-columns: 1fr;
        }
        .weather-summary-block {
          grid-template-columns: 1fr;
          gap: 10px;
        }
        .weather-summary-main {
          grid-template-columns: 58px minmax(0, 1fr);
          gap: 10px;
        }
        .weather-icon-frame,
        .weather-icon {
          width: 58px;
          height: 58px;
        }
        .weather-current {
          text-align: left;
        }
        .weather-current-temp {
          font-size: 28px;
        }
        .weather-forecast-row {
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 4px;
        }
        .weather-day-icon {
          width: 38px;
          height: 38px;
        }
        .category-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
    `;
  }
  _render() {
    this._ensureRuntimeState();
    if (this._debugEnabled()) {
      this._renderDebugMarkdown();
      return;
    }
    this._renderStructuredCard();
  }
}
if (!customElements.get(AURA_TAG_NAME)) {
  customElements.define(AURA_TAG_NAME, BeregynyaAuraCard);
}
if (!Array.isArray(window.customCards)) {
  window.customCards = [];
}
const _auraCard = {
  type: "custom:bereginya-aura",
  name: "Beregynya AURA",
  description: "Beregynya AURA hybrid climate and risk card.",
  preview: true
};
if (!window.customCards.find((it) => it.type === _auraCard.type)) {
  window.customCards.push(_auraCard);
}
