import { html, nothing } from "lit";
import type { TemplateResult } from "lit";

import { renderAuraPlaygroundMain } from "./aura-card.playground.generated";
import type {
  AuraCardConfig,
  AuraDomainVm,
  AuraStatusChipVm,
  AuraStrings,
  AuraViewModel,
} from "./aura-view-model";

export interface AuraOverlayAction {
  key: string;
  icon: string;
  label: string;
  tone: string;
}

export interface AuraCardTemplateContext {
  config: AuraCardConfig;
  strings: AuraStrings;
  themeStyle: string;
  isCompact: boolean;
  activeOverlay: string | null;
  openOverlay: (key: string) => void;
  closeOverlay: () => void;
  setActivePersona: (id: string) => void;
  renderChip: (chip: AuraStatusChipVm, options?: { summaryOnly?: boolean }) => TemplateResult;
  renderWeatherArt: (iconUrl: string | null, summary: string) => TemplateResult;
  renderForecastIcon: (iconUrl: string | null, condition: string) => TemplateResult;
}

type AuraActivePersona = AuraViewModel["personas"][number] | null;

export function renderAuraSkeleton(strings: AuraStrings, themeStyle: string): TemplateResult {
  return html`
    <ha-card class="shell" style=${themeStyle}>
      <div class="surface skeleton" aria-busy="true" aria-label=${strings.loading}>
        <div class="skeleton-block hero"></div>
        <div class="skeleton-block ribbon"></div>
        <div class="skeleton-grid">
          <div class="skeleton-block ribbon"></div>
          <div class="skeleton-block ribbon"></div>
        </div>
      </div>
    </ha-card>
  `;
}

export function renderAuraError(strings: AuraStrings, themeStyle: string, error: string): TemplateResult {
  return html`
    <ha-card class="shell" style=${themeStyle}>
      <div class="error-state">
        <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
        <div class="section-title">${strings.apiError}</div>
        <div class="section-note">${error}</div>
      </div>
    </ha-card>
  `;
}

export function renderAuraMain(
  vm: AuraViewModel,
  activePersona: AuraActivePersona,
  actions: AuraOverlayAction[],
  ctx: AuraCardTemplateContext,
): TemplateResult {
  const plannerSection = vm.planner.chips.length ? renderPlanner(vm, ctx) : nothing;
  const actionsSection = actions.length
    ? html`
        <section class="subsection actions-card">
          ${renderDetailsLauncher(actions, ctx, { inline: true })}
        </section>
      `
    : nothing;
  const secondaryRail = vm.planner.chips.length || actions.length
    ? html`<div class="secondary-rail">${plannerSection}${actionsSection}</div>`
    : nothing;
  const metrics = ctx.isCompact ? vm.hero.metrics.slice(0, 2) : vm.hero.metrics.slice(0, 3);
  const metricsBlock = html`
    ${metrics.map(
      (metric) => html`
        <div class="hero-metric" title=${`${metric.label}: ${metric.value}`} aria-label=${`${metric.label}: ${metric.value}`}>
          <ha-icon icon=${metric.icon}></ha-icon>
          <div class="hero-metric-value">${metric.value}</div>
        </div>
      `,
    )}
  `;
  const secondaryLine = [vm.hero.range, vm.hero.verdictMeta].filter(Boolean).join(" • ");
  const secondaryLineBlock = secondaryLine ? html`<div class="hero-secondaryline">${secondaryLine}</div>` : nothing;
  const overlay = ctx.activeOverlay ? renderOverlay(vm, activePersona, actions, ctx) : nothing;

  return renderAuraPlaygroundMain({
    ctx,
    vm,
    activePersona,
    actions,
    surfaceClass: ctx.isCompact ? "is-compact" : "",
    heroAriaLabel: `${ctx.strings.forecast}: ${vm.hero.summary}`,
    heroArt: ctx.renderWeatherArt(vm.hero.iconUrl, vm.hero.summary),
    secondaryLineBlock,
    metricsBlock,
    secondaryRail,
    overlay,
  });
}

function renderPlanner(vm: AuraViewModel, ctx: AuraCardTemplateContext): TemplateResult {
  const chips = vm.planner.chips.slice(0, ctx.isCompact ? 2 : 3);
  const content = html`
    <div class="planner-strip">
      ${chips.map((chip) => ctx.renderChip(chip, { summaryOnly: true }))}
    </div>
  `;

  return renderSection(ctx.strings.planner, content, { className: "planner" });
}

function renderDetailsLauncher(
  actions: AuraOverlayAction[],
  ctx: AuraCardTemplateContext,
  options: { inline?: boolean } = {},
): TemplateResult {
  const content = html`
    <div class="detail-strip">
      ${actions.map(
        (action) => html`
          <button
            class="detail-btn tone-${action.tone}"
            title=${action.label}
            aria-label=${action.label}
            @click=${() => ctx.openOverlay(action.key)}
          >
            <ha-icon icon=${action.icon}></ha-icon>
          </button>
        `,
      )}
    </div>
  `;

  if (options.inline) return content;
  return renderSection(ctx.strings.details, content, { className: "details-launcher" });
}

function renderDomain(domain: AuraDomainVm, ctx: AuraCardTemplateContext, options: { full?: boolean } = {}): TemplateResult {
  const metrics = options.full ? domain.metrics : domain.metrics.slice(0, ctx.isCompact ? 2 : 3);

  return html`
    <article class="subsection domain-card tone-${domain.tone}">
      <div class="domain-head">
        <div class="domain-title">
          <span class="domain-icon"><ha-icon icon=${domain.icon}></ha-icon></span>
          <span>${domain.title}</span>
        </div>
      </div>
      <div>
        <div class="domain-primary-label">${domain.primaryLabel}</div>
        <div class="domain-primary-value">${domain.primaryValue}</div>
        ${domain.secondary ? html`<div class="domain-secondary">${domain.secondary}</div>` : nothing}
      </div>
      <div class="metrics-grid">
        ${metrics.map(
          (metric) => html`
            <div class="metric-row">
              <ha-icon icon=${metric.icon}></ha-icon>
              <div class="metric-copy">
                <div class="metric-label">${metric.label}</div>
              </div>
              <div class="metric-value">${metric.value}</div>
            </div>
          `,
        )}
      </div>
    </article>
  `;
}

function renderDebug(vm: AuraViewModel, ctx: AuraCardTemplateContext): TemplateResult {
  return renderSection(
    ctx.strings.system,
    html`
      <div class="debug-grid">
        ${vm.debug.fields.map(
          (field) => html`
            <div class="debug-field">
              <div class="debug-field-label">${field.label}</div>
              <div class="debug-field-value">${field.value}</div>
            </div>
          `,
        )}
      </div>
      <div class="fetch-grid">${vm.debug.fetchRows.map((chip) => ctx.renderChip(chip))}</div>
    `,
    { className: "debug-panel", note: ctx.strings.fetchSources },
  );
}

function renderOverlay(
  vm: AuraViewModel,
  _activePersona: AuraActivePersona,
  _actions: AuraOverlayAction[],
  ctx: AuraCardTemplateContext,
): TemplateResult {
  const overlay = ctx.activeOverlay;
  if (!overlay) return html``;

  if (overlay === "forecast") {
    return html`
      <div class="modal-backdrop" @click=${ctx.closeOverlay}>
        <section class="panel modal-card" @click=${stopPropagation}>
          <div class="modal-head">
            <div class="modal-title">
              <ha-icon icon="mdi:weather-partly-cloudy"></ha-icon>
              <span>${ctx.strings.forecast}</span>
            </div>
            <button class="modal-close" @click=${ctx.closeOverlay}>
              ${ctx.strings.close}
            </button>
          </div>
          <div class="modal-body">${renderForecastOverlay(vm, ctx)}</div>
        </section>
      </div>
    `;
  }

  const domain = vm.domains.find((item) => item.key === overlay) || null;
  if (!domain) return html``;

  return html`
    <div class="modal-backdrop" @click=${ctx.closeOverlay}>
      <section class="panel modal-card" @click=${stopPropagation}>
        <div class="modal-head">
          <div class="modal-title">
            <ha-icon icon=${domain.icon}></ha-icon>
            <span>${domain.title}</span>
          </div>
          <button class="modal-close" @click=${ctx.closeOverlay}>
            ${ctx.strings.close}
          </button>
        </div>
        <div class="modal-body">${renderDomain(domain, ctx, { full: true })}</div>
      </section>
    </div>
  `;
}

function renderForecastOverlay(vm: AuraViewModel, ctx: AuraCardTemplateContext): TemplateResult {
  return html`
    <div class="modal-stack">
      <section class="subsection forecast-detail-intro">
        <div class="section-kicker">${ctx.strings.weather}</div>
        <div class="hero-heading">${vm.hero.summary}</div>
        <div class="forecast-summary-line">
          <span>${vm.hero.temperature}</span>
          <span>${vm.hero.range}</span>
          ${vm.hero.verdictMeta ? html`<span>${vm.hero.verdictMeta}</span>` : nothing}
        </div>
      </section>
      <section class="subsection">
        <div class="section-head">
          <div class="section-title">${ctx.strings.forecast}</div>
          <div class="section-note">${vm.forecast.length}</div>
        </div>
        <div class="forecast-detail-grid">
          ${vm.forecast.map(
            (day) => html`
              <div class="forecast-day">
                <div class="forecast-day-label">${day.label}</div>
                ${ctx.renderForecastIcon(day.iconUrl, day.condition)}
                <div class="forecast-day-condition">${day.condition}</div>
                <div class="forecast-temps">
                  <span class="forecast-high">${day.tempHigh}</span>
                  <span class="forecast-low">${day.tempLow}</span>
                </div>
                ${day.badge ? html`<div class="forecast-badge tone-${day.badge.tone}">${day.badge.label}</div>` : nothing}
              </div>
            `,
          )}
        </div>
      </section>
      ${ctx.config.show_debug ? renderDebug(vm, ctx) : nothing}
    </div>
  `;
}

function renderSection(
  title: string,
  content: TemplateResult,
  options: {
    className?: string;
    note?: string | null;
  } = {},
): TemplateResult {
  return html`
    <section class="subsection ${options.className || ""}">
      <div class="section-head">
        <div class="section-title">${title}</div>
        ${options.note ? html`<div class="section-note">${options.note}</div>` : nothing}
      </div>
      ${content}
    </section>
  `;
}

function stopPropagation(event: Event): void {
  event.stopPropagation();
}
