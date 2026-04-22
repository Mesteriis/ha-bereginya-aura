import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "..");
const templateSrc = resolve(
  repoRoot,
  "custom_components/bereginya_aura/frontend/playground/runtime-main.html",
);
const stylesSrc = resolve(
  repoRoot,
  "custom_components/bereginya_aura/frontend/playground/runtime-overrides.css",
);
const generatedOut = resolve(
  repoRoot,
  "custom_components/bereginya_aura/frontend/aura-card.playground.generated.ts",
);

function escapeTemplateLiteral(text) {
  return text.replace(/\\/g, "\\\\").replace(/`/g, "\\`").replace(/\$\{/g, "\\${");
}

function compileHtmlTemplate(source) {
  const normalized = source.replace(/="\{\{([\s\S]*?)\}\}"/g, (_match, expr) => `={{${expr.trim()}}}`);
  let result = "";
  let cursor = 0;
  const pattern = /{{([\s\S]*?)}}/g;
  let match;
  while ((match = pattern.exec(normalized)) !== null) {
    const literal = normalized.slice(cursor, match.index);
    result += escapeTemplateLiteral(literal);
    result += `\${${match[1].trim()}}`;
    cursor = match.index + match[0].length;
  }
  result += escapeTemplateLiteral(normalized.slice(cursor));
  return result.trim();
}

const [htmlSource, cssSource] = await Promise.all([
  readFile(templateSrc, "utf8"),
  readFile(stylesSrc, "utf8"),
]);

const compiledHtml = compileHtmlTemplate(htmlSource);
const compiledCss = escapeTemplateLiteral(cssSource).trim();

const generated = `/* AUTO-GENERATED FILE. DO NOT EDIT DIRECTLY.
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
  return html\`
${compiledHtml}
  \`;
}

export const AURA_PLAYGROUND_SYNC_STYLES = css\`
${compiledCss}
\`;
`;

await writeFile(generatedOut, generated);
process.stdout.write("Playground runtime synced into frontend/aura-card.playground.generated.ts\n");
