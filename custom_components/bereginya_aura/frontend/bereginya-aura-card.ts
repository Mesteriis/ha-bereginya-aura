type AuraLang = "ru" | "en" | "ua" | "es";

type AuraDict = {
  titleDefault: string;
  loading: string;
  apiError: string;
  source: string;
  mode: string;
  refresh: string;
  generatedAt: string;
  homeLatitude: string;
  homeLongitude: string;
  fetchMain: string;
  fetchExtra: string;
  haOverrides: string;
  timezones: string;
  entityTranscript: string;
  forecast: string;
  unavailable: string;
};

const I18N: Record<AuraLang, AuraDict> = {
  ru: {
    titleDefault: "Берегиня AURA",
    loading: "Загрузка данных внутреннего API AURA...",
    apiError: "Ошибка API",
    source: "Источник",
    mode: "Режим",
    refresh: "Обновление",
    generatedAt: "Сгенерировано",
    homeLatitude: "Широта дома",
    homeLongitude: "Долгота дома",
    fetchMain: "Получение weather/marine/air",
    fetchExtra: "Получение jellyfish/mosquito/ticks",
    haOverrides: "HA overrides применено",
    timezones: "Часовые зоны",
    entityTranscript: "Транскрипт сущностей",
    forecast: "Прогноз",
    unavailable: "недоступно",
  },
  en: {
    titleDefault: "Beregynya AURA",
    loading: "Loading internal AURA API data...",
    apiError: "API error",
    source: "Source",
    mode: "Mode",
    refresh: "Refresh",
    generatedAt: "Generated at",
    homeLatitude: "Home latitude",
    homeLongitude: "Home longitude",
    fetchMain: "Fetch weather/marine/air",
    fetchExtra: "Fetch jellyfish/mosquito/ticks",
    haOverrides: "HA overrides applied",
    timezones: "Timezones",
    entityTranscript: "Entity Transcript",
    forecast: "Forecast",
    unavailable: "unavailable",
  },
  ua: {
    titleDefault: "Берегиня AURA",
    loading: "Завантаження даних внутрішнього API AURA...",
    apiError: "Помилка API",
    source: "Джерело",
    mode: "Режим",
    refresh: "Оновлення",
    generatedAt: "Згенеровано",
    homeLatitude: "Широта дому",
    homeLongitude: "Довгота дому",
    fetchMain: "Отримання weather/marine/air",
    fetchExtra: "Отримання jellyfish/mosquito/ticks",
    haOverrides: "HA overrides застосовано",
    timezones: "Часові пояси",
    entityTranscript: "Транскрипт сутностей",
    forecast: "Прогноз",
    unavailable: "недоступно",
  },
  es: {
    titleDefault: "Beregynya AURA",
    loading: "Cargando datos del API interno AURA...",
    apiError: "Error de API",
    source: "Fuente",
    mode: "Modo",
    refresh: "Actualización",
    generatedAt: "Generado",
    homeLatitude: "Latitud de casa",
    homeLongitude: "Longitud de casa",
    fetchMain: "Fetch weather/marine/air",
    fetchExtra: "Fetch jellyfish/mosquito/ticks",
    haOverrides: "HA overrides aplicados",
    timezones: "Zonas horarias",
    entityTranscript: "Transcripción de entidades",
    forecast: "Pronóstico",
    unavailable: "no disponible",
  },
};

class BeregynyaAuraCard extends HTMLElement {
  private _config: Record<string, any> = {};
  private _hass: any = null;
  private _snapshot: any = null;
  private _error: string | null = null;
  private _lastRefreshTs = 0;
  private _refreshPromise: Promise<void> | null = null;
  private _markdownCard: any;

  static getStubConfig() {
    return {
      type: "custom:bereginya-aura",
      title: "Beregynya AURA Transcript",
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._markdownCard = document.createElement("hui-markdown-card");
    this.shadowRoot?.appendChild(this._markdownCard);
  }

  setConfig(config: Record<string, any>) {
    if (!config || typeof config !== "object") {
      throw new Error("Invalid configuration");
    }
    this._config = config;
    this._render();
  }

  set hass(hass: any) {
    this._hass = hass;
    this._markdownCard.hass = hass;
    const now = Date.now();
    if (!this._snapshot || now - this._lastRefreshTs > this._refreshIntervalMs()) {
      void this._refresh();
    }
  }

  getCardSize() {
    return 10;
  }

  private _lang(): AuraLang {
    const configured = String(this._config.lang || this._hass?.language || "ru")
      .trim()
      .toLowerCase();
    if (configured === "uk") return "ua";
    if (configured === "ru" || configured === "en" || configured === "ua" || configured === "es") {
      return configured;
    }
    return "ru";
  }

  private _t(key: keyof AuraDict): string {
    return I18N[this._lang()][key];
  }

  private _value(value: any): string {
    if (value === null || value === undefined || value === "unavailable") {
      return this._t("unavailable");
    }
    return String(value);
  }

  private async _refresh() {
    if (!this._hass || this._refreshPromise) {
      return;
    }

    let endpoint = "bereginya_aura/v1/snapshot";
    if (this._config.force_refresh === true) {
      endpoint += "?force_refresh=1";
    }

    this._refreshPromise = this._hass
      .callApi("GET", endpoint)
      .then((snapshot: any) => {
        this._snapshot = snapshot;
        this._error = null;
        this._lastRefreshTs = Date.now();
      })
      .catch((err: any) => {
        this._error = err?.message || String(err);
      })
      .finally(() => {
        this._refreshPromise = null;
        this._render();
      });
  }

  private _refreshIntervalMs() {
    const configured = Number(this._config.refresh_seconds ?? 120);
    if (!Number.isFinite(configured)) {
      return 120_000;
    }
    return Math.max(15_000, configured * 1000);
  }

  private _render() {
    const title = this._config.title || this._t("titleDefault");
    const lines: string[] = [`# ${title}`, ""];

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
        `- ${this._t("fetchMain")}: \`${this._value(fetch.weather)}\` / \`${this._value(fetch.marine)}\` / \`${this._value(fetch.air_quality)}\``,
      );
      lines.push(
        `- ${this._t("fetchExtra")}: \`${this._value(fetch.jellyfish)}\` / \`${this._value(fetch.tiger_mosquito)}\` / \`${this._value(fetch.ticks)}\``,
      );

      if (meta.ha_overrides) {
        lines.push(
          `- ${this._t("haOverrides")}: \`${this._value(meta.ha_overrides.applied)}\` / \`${this._value(meta.ha_overrides.attempted)}\``,
        );
      }

      const zones = Array.isArray(meta.timezones) ? meta.timezones : [];
      if (zones.length > 0) {
        const compact = zones
          .map((z: any) => `${this._value(z.timezone)} ${this._value(z.time)}`)
          .join(" | ");
        lines.push(`- ${this._t("timezones")}: ${compact}`);
      }

      lines.push("");
      lines.push(`## ${this._t("entityTranscript")}`);

      const entities = Array.isArray(this._snapshot.entities) ? this._snapshot.entities : [];
      for (const entity of entities) {
        const unit = entity.unit ? ` ${entity.unit}` : "";
        const source = entity.source ? ` _(source: ${entity.source})_` : "";
        const sourceEntity = entity.source_entity ? ` _(${entity.source_entity})_` : "";
        const icon = entity.icon && this._config.show_icons === true ? ` _[${entity.icon}]_` : "";
        lines.push(
          `- \`${entity.entity_id}\`: **${this._value(entity.value)}${unit}**${source}${sourceEntity}${icon}`,
        );
      }

      const daily = Array.isArray(this._snapshot.forecast_daily) ? this._snapshot.forecast_daily : [];
      if (daily.length > 0) {
        lines.push("");
        lines.push(`## ${this._t("forecast")} ${daily.length}d`);
        for (const day of daily) {
          lines.push(
            `- \`${this._value(day.date)}\`: ${this._value(day.temp_min)}/${this._value(day.temp_max)} degC, rain ${this._value(day.rain_probability_max)}% (${this._value(day.rain_sum_mm)} mm), UV ${this._value(day.uv_max)}, sea ${this._value(day.sea_temp_avg)} degC, AQI ${this._value(day.aqi_max)}, allergy ${this._value(day.allergy_index)}/100, asthma ${this._value(day.asthma_risk)}, beach ${this._value(day.beach_score)}/10 (${this._value(day.beach_flag)}), mosquito ${this._value(day.mosquito_risk_est)}, jellyfish ${this._value(day.jellyfish_risk_est)}, ticks ${this._value(day.tick_risk_est)}`,
          );
        }
      }
    }

    this._markdownCard.setConfig({
      type: "markdown",
      content: lines.join("\n"),
    });
    if (this._hass) {
      this._markdownCard.hass = this._hass;
    }
  }
}

if (!customElements.get("bereginya-aura")) {
  customElements.define("bereginya-aura", BeregynyaAuraCard);
}

window.customCards = window.customCards || [];
const _auraCards = [
  {
    type: "bereginya-aura",
    name: "Beregynya AURA",
    description: "Prototype card powered by internal Beregynya AURA API.",
  },
  {
    type: "custom:bereginya-aura",
    name: "Beregynya AURA",
    description: "Prototype card powered by internal Beregynya AURA API.",
  },
];

for (const card of _auraCards) {
  if (!window.customCards.find((it: any) => it.type === card.type)) {
    window.customCards.push(card);
  }
}
