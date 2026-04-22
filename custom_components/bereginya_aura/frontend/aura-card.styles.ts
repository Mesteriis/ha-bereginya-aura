import { css } from "lit";
import { AURA_PLAYGROUND_SYNC_STYLES } from "./aura-card.playground.generated";

const AURA_CARD_BASE_STYLES = css`
  :host {
    display: block;
    color: var(--aura-text-primary);
  }

  * {
    box-sizing: border-box;
  }

  ha-card.shell {
    position: relative;
    overflow: hidden;
    width: 100%;
    min-width: 0;
    container-type: inline-size;
    container-name: aura-card;
    border-radius: var(--aura-radius-lg);
    border: 1px solid var(--aura-glass-border);
    background:
      radial-gradient(circle at 18% 14%, var(--aura-bg-glow), transparent 28%),
      radial-gradient(circle at 86% 12%, rgba(255, 255, 255, 0.06), transparent 18%),
      linear-gradient(165deg, var(--aura-bg-start), var(--aura-bg-end));
    box-shadow: var(--aura-glass-shadow);
    color: var(--aura-text-primary);
  }

  .surface {
    position: relative;
    padding: 14px;
    display: grid;
    gap: 10px;
  }

  .surface::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0));
    pointer-events: none;
  }

  .panel {
    position: relative;
    overflow: hidden;
    border-radius: var(--aura-radius-md);
    border: 1px solid var(--aura-glass-border);
    background: var(--aura-glass-bg);
    box-shadow: var(--aura-glass-shadow), inset 0 1px 0 var(--aura-glass-inner);
    backdrop-filter: blur(var(--aura-blur));
    -webkit-backdrop-filter: blur(var(--aura-blur));
  }

  .stage {
    padding: 14px;
    display: grid;
    gap: 10px;
  }

  .panel::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0));
    pointer-events: none;
  }

  .tab-btn:hover,
  .tab-btn:focus-visible,
  .chip:hover,
  .chip:focus-visible {
    transform: translateY(-1px);
    border-color: rgba(255, 255, 255, 0.26);
    background: rgba(255, 255, 255, 0.08);
    outline: none;
  }

  .planner-strip {
    display: flex;
    flex-wrap: wrap;
    gap: var(--aura-space-2);
    min-width: 0;
    align-items: flex-start;
    justify-content: flex-start;
  }

  .hero-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, max-content));
    gap: 8px 18px;
    min-width: 0;
    align-items: center;
    justify-content: start;
  }

  .persona-tabs,
  .tracker-list {
    display: flex;
    flex-wrap: wrap;
    gap: var(--aura-space-2);
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    max-width: 100%;
    padding: 8px 10px;
    border-radius: 999px;
    border: 1px solid var(--aura-glass-border);
    background: rgba(255, 255, 255, 0.04);
    color: var(--aura-text-primary);
    transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
  }

  .chip-tone-safe {
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--aura-accent-safe) 24%, transparent);
  }

  .chip-tone-warning {
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--aura-accent-warning) 24%, transparent);
  }

  .chip-tone-danger {
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--aura-accent-danger) 24%, transparent);
  }

  .chip-tone-info {
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--aura-accent-neutral) 24%, transparent);
  }

  .chip-main {
    min-width: 0;
    display: grid;
    gap: 2px;
  }

  .chip-label {
    font-size: 11px;
    font-weight: 600;
    line-height: 1.1;
  }

  .chip-detail {
    font-size: 10px;
    color: var(--aura-text-secondary);
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .hero {
    display: grid;
    grid-template-columns: 72px minmax(0, 1fr);
    gap: 10px;
    align-items: start;
  }

  .hero-trigger {
    all: unset;
    display: block;
    cursor: pointer;
    border-radius: 24px;
  }

  .hero-trigger:focus-visible {
    outline: 1px solid rgba(255, 255, 255, 0.24);
    outline-offset: 4px;
  }

  .hero-trigger:hover .hero-art,
  .hero-trigger:focus-visible .hero-art {
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }

  .hero-art {
    width: 72px;
    min-height: 72px;
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background:
      radial-gradient(circle at 50% 30%, rgba(112, 207, 255, 0.18), transparent 46%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03));
    display: grid;
    place-items: center;
    overflow: hidden;
  }

  .hero-art img {
    width: 76%;
    height: 76%;
    object-fit: contain;
    display: block;
    filter: saturate(0.9);
  }

  .hero-art ha-icon {
    --mdc-icon-size: 32px;
    color: color-mix(in srgb, var(--aura-accent-neutral) 78%, white);
  }

  .hero-body {
    min-width: 0;
    display: grid;
    align-content: start;
    gap: 6px;
  }

  .hero-mainline {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 10px;
    align-items: center;
  }

  .hero-copy {
    min-width: 0;
    display: grid;
    align-content: start;
    gap: 6px;
  }

  .hero-heading {
    font-size: 20px;
    line-height: 1.02;
    letter-spacing: -0.04em;
    font-weight: 700;
  }

  .hero-verdict {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    width: fit-content;
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.02em;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .tone-safe {
    color: var(--aura-accent-safe);
  }

  .tone-warning {
    color: var(--aura-accent-warning);
  }

  .tone-danger {
    color: var(--aura-accent-danger);
  }

  .tone-neutral,
  .tone-info {
    color: var(--aura-accent-neutral);
  }

  .hero-note {
    font-size: 10px;
    color: var(--aura-text-secondary);
    line-height: 1.35;
  }

  .hero-secondaryline {
    font-size: 12px;
    color: var(--aura-text-secondary);
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .hero-metric {
    min-width: 0;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 0;
    border: 0;
    background: none;
    white-space: nowrap;
  }

  .hero-metric ha-icon {
    --mdc-icon-size: 18px;
    color: var(--aura-text-secondary);
  }

  .hero-metric-label,
  .metric-label,
  .section-kicker {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--aura-text-muted);
  }

  .hero-metric-value,
  .metric-value {
    font-size: 14px;
    font-weight: 600;
    color: var(--aura-text-primary);
    line-height: 1.15;
  }

  .hero-metrics .hero-metric-value {
    font-size: 15px;
    line-height: 1;
  }

  .hero-temp {
    min-width: 0;
    text-align: right;
    display: grid;
    align-content: start;
    gap: 0;
    justify-items: end;
  }

  .hero-temp-main {
    font-size: 38px;
    line-height: 0.88;
    font-weight: 700;
    letter-spacing: -0.06em;
  }

  .subsection {
    position: relative;
    border-radius: var(--aura-radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.025);
    padding: var(--aura-space-3);
  }

  .secondary-rail {
    display: grid;
    gap: 8px;
  }

  .rail-block {
    display: grid;
    gap: 8px;
    min-width: 0;
  }

  .rail-head {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    align-items: baseline;
    min-width: 0;
  }

  .rail-title {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--aura-text-muted);
  }

  .rail-note {
    font-size: 10px;
    color: var(--aura-text-secondary);
    white-space: nowrap;
  }

  .section-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--aura-space-3);
    margin-bottom: 10px;
  }

  .section-title {
    font-size: 14px;
    font-weight: 600;
    line-height: 1.1;
  }

  .section-note {
    font-size: 11px;
    color: var(--aura-text-secondary);
  }

  .forecast-ribbon {
    display: grid;
    grid-auto-flow: column;
    grid-auto-columns: minmax(88px, 1fr);
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 2px;
    scrollbar-width: thin;
  }

  .forecast-day {
    border-radius: var(--aura-radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    padding: 10px;
    display: grid;
    justify-items: center;
    gap: 6px;
    min-width: 88px;
  }

  .forecast-day img {
    width: 36px;
    height: 36px;
    object-fit: contain;
  }

  .forecast-day ha-icon {
    --mdc-icon-size: 26px;
    color: var(--aura-text-secondary);
  }

  .forecast-day-label {
    font-size: 11px;
    font-weight: 700;
  }

  .forecast-temps {
    display: flex;
    gap: 8px;
    align-items: baseline;
    font-size: 12px;
  }

  .forecast-high {
    font-weight: 700;
  }

  .forecast-low {
    color: var(--aura-text-secondary);
  }

  .forecast-badge {
    padding: 4px 8px;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    font-size: 11px;
    line-height: 1;
  }

  .details-launcher {
    display: grid;
    gap: 6px;
    align-items: start;
  }

  .actions-card {
    padding: 10px;
  }

  .planner-card {
    padding: 10px 12px;
  }

  .planner-card .section-head {
    margin-bottom: 8px;
  }

  .planner-card .planner-strip {
    gap: 8px;
  }

  .detail-strip {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 6px;
    align-items: stretch;
  }

  .detail-btn {
    width: 100%;
    min-width: 0;
    aspect-ratio: 1;
    display: grid;
    place-items: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.04);
    color: var(--aura-text-primary);
    padding: 0;
    cursor: pointer;
    transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
    text-align: center;
  }

  .detail-btn:hover,
  .detail-btn:focus-visible {
    transform: translateY(-1px);
    border-color: rgba(255, 255, 255, 0.24);
    background: rgba(255, 255, 255, 0.08);
    outline: none;
  }

  .detail-btn ha-icon {
    --mdc-icon-size: 20px;
  }

  .secondary-rail .chip {
    padding: 8px 10px;
  }

  .secondary-rail .chip-label {
    font-size: 11px;
  }

  .secondary-rail .chip-detail {
    font-size: 9px;
  }

  .secondary-rail .chip ha-icon {
    --mdc-icon-size: 18px;
  }

  .secondary-rail .forecast-day {
    min-width: 78px;
    padding: 7px;
    gap: 4px;
  }

  .forecast-detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(108px, 1fr));
    gap: 10px;
  }

  .modal-stack {
    display: grid;
    gap: 12px;
  }

  .forecast-detail-intro {
    display: grid;
    gap: 8px;
  }

  .forecast-detail-intro .hero-heading {
    font-size: clamp(18px, 2.3vw, 24px);
  }

  .forecast-summary-line {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 12px;
    color: var(--aura-text-secondary);
  }

  .forecast-detail-grid .forecast-day {
    min-width: 0;
    padding: 12px 10px;
  }

  .forecast-day-condition {
    font-size: 11px;
    line-height: 1.25;
    color: var(--aura-text-secondary);
    text-align: center;
    min-height: 28px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .secondary-rail .forecast-day img {
    width: 30px;
    height: 30px;
  }

  .matrix {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: var(--aura-space-3);
  }

  .matrix.compact {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 10px;
  }

  .domain-card {
    padding: var(--aura-space-3);
    display: grid;
    gap: 12px;
  }

  .domain-card.tone-safe {
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--aura-accent-safe) 14%, transparent);
  }

  .domain-card.tone-warning {
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--aura-accent-warning) 14%, transparent);
  }

  .domain-card.tone-danger {
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--aura-accent-danger) 16%, transparent);
  }

  .domain-head {
    display: flex;
    justify-content: space-between;
    gap: var(--aura-space-2);
    align-items: start;
  }

  .domain-title {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
    font-size: 15px;
    font-weight: 600;
  }

  .domain-icon {
    width: 32px;
    height: 32px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    display: inline-grid;
    place-items: center;
    flex: 0 0 auto;
  }

  .domain-icon ha-icon {
    --mdc-icon-size: 18px;
  }

  .domain-primary-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--aura-text-muted);
  }

  .domain-primary-value {
    margin-top: 4px;
    font-size: 20px;
    line-height: 1;
    font-weight: 700;
    letter-spacing: -0.03em;
  }

  .domain-secondary {
    margin-top: 6px;
    font-size: 12px;
    color: var(--aura-text-secondary);
    line-height: 1.35;
  }

  .metrics-grid {
    display: grid;
    gap: 8px;
  }

  .metric-row {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 10px;
    align-items: center;
    min-width: 0;
  }

  .metric-row ha-icon {
    --mdc-icon-size: 16px;
    color: var(--aura-text-secondary);
  }

  .metric-copy {
    min-width: 0;
    display: grid;
    gap: 2px;
  }

  .metric-value {
    text-align: right;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
  }

  .tab-btn {
    border: 1px solid var(--aura-glass-border);
    border-radius: 999px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.04);
    color: var(--aura-text-secondary);
    cursor: pointer;
    transition: transform 160ms ease, border-color 160ms ease, background 160ms ease, color 160ms ease;
  }

  .tab-btn.is-active {
    color: var(--aura-text-primary);
    border-color: rgba(255, 255, 255, 0.22);
    background: rgba(255, 255, 255, 0.08);
  }

  .persona-body {
    margin-top: 10px;
    display: grid;
    gap: 12px;
  }

  .persona-hero {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: var(--aura-space-3);
    align-items: start;
  }

  .persona-name {
    font-size: 18px;
    line-height: 1;
    font-weight: 700;
    letter-spacing: -0.03em;
  }

  .persona-advisor {
    margin-top: 8px;
    font-size: 13px;
    color: var(--aura-text-secondary);
    line-height: 1.45;
  }

  .persona-pack {
    padding: 10px 12px;
    border-radius: var(--aura-radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    max-width: 280px;
  }

  .persona-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: var(--aura-space-2);
  }

  .persona-metric {
    padding: 10px 12px;
    border-radius: var(--aura-radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    display: grid;
    gap: 6px;
  }

  .tracker-pill {
    min-width: 0;
    padding: 10px 12px;
    border-radius: var(--aura-radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
    display: grid;
    gap: 6px;
  }

  .tracker-top {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    align-items: baseline;
  }

  .tracker-name {
    font-size: 13px;
    font-weight: 700;
  }

  .tracker-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 12px;
    color: var(--aura-text-secondary);
  }

  .surface.is-compact .section-note {
    font-size: 10px;
  }

  .surface.is-compact .hero-metrics,
  .surface.is-compact .planner-strip,
  .surface.is-compact .persona-tabs,
  .surface.is-compact .tracker-list,
  .surface.is-compact .detail-strip {
    gap: 8px;
  }

  .surface.is-compact .persona-metric,
  .surface.is-compact .tracker-pill,
  .surface.is-compact .forecast-day {
    padding: 8px 10px;
  }

  details.debug-panel[open] summary {
    margin-bottom: var(--aura-space-3);
  }

  summary {
    list-style: none;
    cursor: pointer;
  }

  summary::-webkit-details-marker {
    display: none;
  }

  .debug-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px;
  }

  .debug-field {
    padding: 10px;
    border-radius: var(--aura-radius-sm);
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.03);
  }

  .debug-field-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--aura-text-muted);
  }

  .debug-field-value {
    margin-top: 6px;
    font-size: 13px;
    color: var(--aura-text-primary);
    word-break: break-word;
  }

  .fetch-grid {
    margin-top: var(--aura-space-3);
    display: flex;
    flex-wrap: wrap;
    gap: var(--aura-space-2);
  }

  .skeleton {
    min-height: 360px;
    display: grid;
    gap: var(--aura-space-3);
  }

  .skeleton-block {
    border-radius: var(--aura-radius-md);
    background:
      linear-gradient(105deg, rgba(255, 255, 255, 0.02) 20%, rgba(255, 255, 255, 0.08) 50%, rgba(255, 255, 255, 0.02) 80%),
      rgba(255, 255, 255, 0.04);
    background-size: 240% 100%;
    animation: auraShimmer 1.4s linear infinite;
  }

  .skeleton-block.hero {
    min-height: 210px;
  }

  .skeleton-block.ribbon {
    min-height: 112px;
  }

  .skeleton-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--aura-space-3);
  }

  .error-state {
    padding: var(--aura-space-5);
    min-height: 220px;
    display: grid;
    place-items: center;
    text-align: center;
    gap: var(--aura-space-2);
  }

  .error-state ha-icon {
    --mdc-icon-size: 32px;
    color: var(--aura-accent-danger);
  }

  .debug-transcript {
    padding: var(--aura-space-4);
    font: 12px/1.5 "JetBrains Mono", "SFMono-Regular", ui-monospace, monospace;
    white-space: pre-wrap;
    color: var(--aura-text-primary);
    margin: 0;
  }

  .modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 40;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 18px;
    background: rgba(3, 9, 16, 0.78);
  }

  .modal-card {
    width: min(620px, 100%);
    max-height: min(82vh, 760px);
    overflow: hidden;
    display: grid;
    grid-template-rows: auto minmax(0, 1fr);
    background: var(--aura-glass-bg-strong);
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    contain: layout paint;
    will-change: transform;
  }

  .modal-head {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    padding: 14px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .modal-title {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  .modal-body {
    overflow: auto;
    padding: 16px;
    display: grid;
    gap: 12px;
    overscroll-behavior: contain;
  }

  .modal-close {
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.05);
    color: var(--aura-text-primary);
    padding: 8px 12px;
    cursor: pointer;
  }

  @keyframes auraShimmer {
    100% {
      background-position: -140% 0;
    }
  }

  @container aura-card (max-width: 720px) {
    .surface {
      padding: 12px;
    }

    .stage {
      padding: 12px;
    }

    .hero-heading {
      font-size: 18px;
    }

    .hero-temp-main {
      font-size: 32px;
    }

    .hero-metric {
      min-width: 0;
    }
  }

  @container aura-card (max-width: 640px) {
    .hero {
      grid-template-columns: 72px minmax(0, 1fr);
      gap: 10px;
    }

    .hero-mainline {
      grid-template-columns: 1fr;
      gap: 8px;
    }

    .hero-temp {
      text-align: left;
      justify-items: start;
    }

    .hero-temp-main {
      font-size: 32px;
    }

    .hero-metrics {
      grid-template-columns: repeat(2, minmax(0, max-content));
      gap: 8px 14px;
    }

    .planner-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      overflow: visible;
    }

    .planner-strip .chip {
      min-width: 0;
      max-width: 100%;
    }
  }

  @container aura-card (max-width: 560px) {
    .hero {
      grid-template-columns: 72px minmax(0, 1fr);
    }
  }

  @container aura-card (max-width: 400px) {
    .surface {
      padding: 14px;
    }

    .hero {
      grid-template-columns: 60px minmax(0, 1fr);
    }

    .hero-art {
      width: 60px;
      min-height: 60px;
    }

    .hero-temp-main {
      font-size: 28px;
    }

    .persona-hero {
      grid-template-columns: 1fr;
    }

    .hero-metrics {
      grid-template-columns: repeat(2, minmax(0, max-content));
      gap: 8px 12px;
    }

    .skeleton-grid {
      grid-template-columns: 1fr;
    }
  }

  @container aura-card (max-width: 340px) {
  }
`;

export const AURA_CARD_STYLES = [AURA_CARD_BASE_STYLES, AURA_PLAYGROUND_SYNC_STYLES];
