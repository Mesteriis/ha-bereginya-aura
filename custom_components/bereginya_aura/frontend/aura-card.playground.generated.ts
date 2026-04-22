/* AUTO-GENERATED FILE. DO NOT EDIT DIRECTLY.
 * Source:
 * - frontend/playground/runtime-main.html
 * - frontend/playground/runtime-overrides.css
 * Regenerate with: node scripts/sync-playground.mjs
 */

import { css, html } from "lit";
import type { TemplateResult } from "lit";

import type { AuraViewModel } from "./aura-view-model";
import type { AuraCardTemplateContext, AuraOverlayAction } from "./aura-card.template";

export interface AuraPlaygroundMainScope {
  ctx: AuraCardTemplateContext;
  vm: AuraViewModel;
  activePersona: AuraViewModel["personas"][number] | null;
  actions: AuraOverlayAction[];
  surfaceClass: string;
  heroAriaLabel: string;
  heroArt: TemplateResult;
  secondaryLineBlock: unknown;
  metricsBlock: TemplateResult;
  secondaryRail: unknown;
  overlay: unknown;
}

export function renderAuraPlaygroundMain(scope: AuraPlaygroundMainScope): TemplateResult {
  return html`
<ha-card class="shell" style=${scope.ctx.themeStyle}>
  <div class="surface ${scope.surfaceClass}">
    <section class="panel stage">
      <button
        class="hero-trigger"
        @click=${() => scope.ctx.openOverlay('forecast')}
        aria-label=${scope.heroAriaLabel}
      >
        <div class="hero">
          <div class="hero-art">${scope.heroArt}</div>
          <div class="hero-body">
            <div class="hero-mainline">
              <div class="hero-copy">
                <div class="hero-heading">${scope.vm.hero.summary}</div>
                <div class="hero-verdict tone-${scope.vm.hero.verdictTone}">
                  <ha-icon icon="mdi:flag-variant-outline"></ha-icon>
                  <span>${scope.vm.hero.verdict}</span>
                </div>
              </div>
              <div class="hero-temp">
                <div class="hero-temp-main">${scope.vm.hero.temperature}</div>
              </div>
            </div>
            ${scope.secondaryLineBlock}
            <div class="hero-metrics">${scope.metricsBlock}</div>
          </div>
        </div>
      </button>
    </section>
    ${scope.secondaryRail}
  </div>
  ${scope.overlay}
</ha-card>
  `;
}

export const AURA_PLAYGROUND_SYNC_STYLES = css`
/*
  This file is appended after aura-card.styles.ts.
  Use it for quick manual layout tuning from the playground workflow.

  Example:

  .hero {
    grid-template-columns: 64px minmax(0, 1fr);
  }

  .hero-temp-main {
    font-size: 34px;
  }
*/
`;
