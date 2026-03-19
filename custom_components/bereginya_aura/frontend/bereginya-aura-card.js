class BeregynyaAuraCard extends HTMLElement {
  static getStubConfig() {
    return {
      type: "custom:bereginya-aura",
      title: "Beregynya AURA Transcript",
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._snapshot = null;
    this._error = null;
    this._lastRefreshTs = 0;
    this._refreshPromise = null;
    this._markdownCard = document.createElement("hui-markdown-card");
    this.shadowRoot.appendChild(this._markdownCard);
  }

  setConfig(config) {
    if (!config || typeof config !== "object") {
      throw new Error("Invalid configuration");
    }
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._markdownCard.hass = hass;
    const now = Date.now();
    if (!this._snapshot || now - this._lastRefreshTs > this._refreshIntervalMs()) {
      this._refresh();
    }
  }

  getCardSize() {
    return 8;
  }

  async _refresh() {
    if (!this._hass || this._refreshPromise) {
      return;
    }

    let endpoint = "bereginya_aura/v1/snapshot";
    if (this._config.force_refresh === true) {
      endpoint += "?force_refresh=1";
    }

    this._refreshPromise = this._hass
      .callApi("GET", endpoint)
      .then((snapshot) => {
        this._snapshot = snapshot;
        this._error = null;
        this._lastRefreshTs = Date.now();
      })
      .catch((err) => {
        this._error = err?.message || String(err);
      })
      .finally(() => {
        this._refreshPromise = null;
        this._render();
      });
  }

  _refreshIntervalMs() {
    const configured = Number(this._config.refresh_seconds ?? 120);
    if (!Number.isFinite(configured)) {
      return 120_000;
    }
    return Math.max(15_000, configured * 1000);
  }

  _render() {
    const title = this._config.title || "Beregynya AURA";
    const lines = [`# ${title}`, ""];

    if (this._error) {
      lines.push(`- API error: \`${this._error}\``);
    } else if (!this._snapshot) {
      lines.push("- Loading internal AURA API data...");
    } else {
      const meta = this._snapshot.meta || {};
      const home = meta.home_position || {};
      lines.push(`- Source: \`${meta.source || "unknown"}\``);
      lines.push(`- Mode: \`${meta.source_mode || "internal"}\``);
      lines.push(`- Refresh: \`${meta.refresh_seconds ?? "n/a"}s\``);
      lines.push(`- Generated at: \`${meta.generated_at || "n/a"}\``);
      lines.push(`- Home latitude: \`${home.latitude ?? "n/a"}\``);
      lines.push(`- Home longitude: \`${home.longitude ?? "n/a"}\``);
      if (meta.fetch) {
        const fetch = meta.fetch;
        lines.push(
          `- Fetch weather/marine/air: \`${fetch.weather || "n/a"}\` / \`${fetch.marine || "n/a"}\` / \`${fetch.air_quality || "n/a"}\``,
        );
        if (fetch.jellyfish || fetch.tiger_mosquito) {
          lines.push(
            `- Fetch jellyfish/tiger_mosquito: \`${fetch.jellyfish || "n/a"}\` / \`${fetch.tiger_mosquito || "n/a"}\``,
          );
        }
      }
      if (meta.ha_overrides) {
        lines.push(
          `- HA overrides applied: \`${meta.ha_overrides.applied || 0}\` of \`${meta.ha_overrides.attempted || 0}\``,
        );
      }
      lines.push("");
      lines.push("## Entity Transcript");

      const entities = Array.isArray(this._snapshot.entities)
        ? this._snapshot.entities
        : [];
      for (const entity of entities) {
        const unit = entity.unit ? ` ${entity.unit}` : "";
        const source = entity.source ? ` _(source: ${entity.source})_` : "";
        const sourceEntity = entity.source_entity
          ? ` _(${entity.source_entity})_`
          : "";
        lines.push(
          `- \`${entity.entity_id}\`: **${entity.value}${unit}**${source}${sourceEntity}`,
        );
      }

      const daily = Array.isArray(this._snapshot.forecast_daily)
        ? this._snapshot.forecast_daily
        : [];
      if (daily.length > 0) {
        lines.push("");
        lines.push(`## Forecast ${daily.length}d`);
        for (const day of daily) {
          const extra = [
            day.mosquito_risk_est ? `, mosquito ${day.mosquito_risk_est}` : "",
            day.jellyfish_risk_est ? `, jellyfish ${day.jellyfish_risk_est}` : "",
          ].join("");
          lines.push(
            `- \`${day.date}\`: ${day.temp_min}/${day.temp_max} degC, rain ${day.rain_probability_max}% (${day.rain_sum_mm} mm), UV ${day.uv_max}, sea ${day.sea_temp_avg} degC, AQI ${day.aqi_max}, allergy ${day.allergy_index}/100, asthma ${day.asthma_risk}, beach ${day.beach_score}/10 (${day.beach_flag})${extra}`,
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
  if (!window.customCards.find((it) => it.type === card.type)) {
    window.customCards.push(card);
  }
}
