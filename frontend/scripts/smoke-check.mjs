import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, "..");

const requiredFiles = [
  "app/layout.tsx",
  "app/page.tsx",
  "next.config.mjs",
  "package.json",
  "tsconfig.json",
];

for (const relativePath of requiredFiles) {
  const absolutePath = path.join(frontendRoot, relativePath);
  if (!fs.existsSync(absolutePath)) {
    throw new Error(`Missing required frontend file: ${relativePath}`);
  }
}

await import(pathToFileURL(path.join(frontendRoot, "next.config.mjs")).href);

console.log("Frontend smoke check passed.");
