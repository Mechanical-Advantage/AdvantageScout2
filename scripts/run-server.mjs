import { spawn } from "node:child_process";
import process from "node:process";
import fs from "node:fs";
import path from "node:path";

const isWindows = process.platform === "win32";

const possibleVenvDirs = [".venv", "venv", "env"];
let pythonPath = null;

for (const dir of possibleVenvDirs) {
  const binSubdir = isWindows ? "Scripts" : "bin";
  const exeName = isWindows ? "python.exe" : "python3";
  const altExeName = isWindows ? "python.exe" : "python";

  const potentialPath1 = path.join(process.cwd(), dir, binSubdir, exeName);
  const potentialPath2 = path.join(process.cwd(), dir, binSubdir, altExeName);

  if (fs.existsSync(potentialPath1)) {
    pythonPath = potentialPath1;
    break;
  } else if (fs.existsSync(potentialPath2)) {
    pythonPath = potentialPath2;
    break;
  }
}

const args = process.argv.slice(2);

const child = spawn(pythonPath, args, {
  stdio: "inherit",
  shell: true,
});

child.on("close", (code) => {
  process.exit(code);
});
