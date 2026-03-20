import { build } from "esbuild";
import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "..");
const entryPoint = resolve(
  repoRoot,
  "custom_components/bereginya_aura/frontend/bereginya-aura-card.ts",
);
const outFile = resolve(
  repoRoot,
  "custom_components/bereginya_aura/frontend/bereginya-aura-card.js",
);
const outGzip = `${outFile}.gz`;
const checkOnly = process.argv.includes("--check");

const result = await build({
  entryPoints: [entryPoint],
  bundle: false,
  charset: "utf8",
  format: "esm",
  legalComments: "none",
  platform: "browser",
  target: "es2022",
  write: false,
});

const jsBuffer = Buffer.from(result.outputFiles[0].contents);
const gzBuffer = gzipSync(jsBuffer);

if (checkOnly) {
  const currentJs = await readFile(outFile);
  const currentGz = await readFile(outGzip);
  if (!currentJs.equals(jsBuffer)) {
    throw new Error("Frontend JS artifact is out of date. Run npm run build:frontend.");
  }
  if (!currentGz.equals(gzBuffer)) {
    throw new Error("Frontend gzip artifact is out of date. Run npm run build:frontend.");
  }
  process.stdout.write("Frontend artifacts are up to date.\n");
} else {
  await writeFile(outFile, jsBuffer);
  await writeFile(outGzip, gzBuffer);
  process.stdout.write("Frontend artifacts rebuilt.\n");
}
