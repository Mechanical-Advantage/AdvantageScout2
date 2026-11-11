import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const distDir = fileURLToPath(new URL("../dist", import.meta.url));

function listFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...listFiles(full));
    } else {
      out.push(full);
    }
  }
  return out;
}

const files = listFiles(distDir)
  .map((f) => relative(distDir, f))
  .sort();

const hash = createHash("sha256");
for (const rel of files) {
  hash.update(rel);
  hash.update(readFileSync(join(distDir, rel)));
}

const version = hash.digest("hex").slice(0, 16);
writeFileSync(join(distDir, "version.txt"), version);
console.log(`Stamped dist/version.txt: ${version}`);
