import { Capacitor, WebView } from "@capacitor/core";
import { Filesystem, Directory, Encoding } from "@capacitor/filesystem";
import { api } from "./api.svelte";
import { isOnScoutingForm } from "./scouting-route";
import { RSYNC_BLOCK_SIZE, computeSignatures, applyDelta, type FileSignature, type FileDelta } from "./rsync-delta";

interface DeltaManifest {
  version: string;
  blockSize: number;
  files: FileDelta[];
}

let appliedVersion: string | null = null;

let activeFiles: Map<string, Uint8Array> | null = null;

async function readDirRecursive(dirPath: string, relPrefix: string, out: Map<string, Uint8Array>): Promise<void> {
  const { files: entries } = await Filesystem.readdir({ path: dirPath, directory: Directory.Data });
  for (const entry of entries) {
    const rel = relPrefix ? `${relPrefix}/${entry.name}` : entry.name;
    const fullPath = `${dirPath}/${entry.name}`;
    if (entry.type === "directory") {
      await readDirRecursive(fullPath, rel, out);
    } else if (entry.name !== "version.txt") {
      const { data } = await Filesystem.readFile({ path: fullPath, directory: Directory.Data });
      out.set(rel, base64ToBytes(data as string));
    }
  }
}

async function readLocalBundleFromDisk(): Promise<Map<string, Uint8Array> | null> {
  try {
    const localVersion = await getRunningVersion();
    const files = new Map<string, Uint8Array>();
    await readDirRecursive(`frontend-update/${localVersion}`, "", files);
    return files.size > 0 ? files : null;
  } catch {
    return null;
  }
}

async function getLocalFiles(): Promise<Map<string, Uint8Array>> {
  if (activeFiles) return activeFiles;
  if (Capacitor.isNativePlatform()) {
    const fromDisk = await readLocalBundleFromDisk();
    if (fromDisk) {
      activeFiles = fromDisk;
      return fromDisk;
    }
  }
  return new Map();
}

export const frontendUpdateState = $state<{
  phase: "downloading" | "installing" | null;
  downloadProgress: { current: number; max: number } | null;
}>({ phase: null, downloadProgress: null });

async function getRunningVersion(): Promise<string> {
  if (appliedVersion) return appliedVersion;
  try {
    const res = await fetch("/version.txt");
    if (!res.ok) return "unknown";
    return (await res.text()).trim();
  } catch {
    return "unknown";
  }
}

function base64ToBytes(b64: string): Uint8Array {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++)
    binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function isTextMime(mime: string): boolean {
  return (
    mime.startsWith("text/") ||
    mime.includes("javascript") ||
    mime.includes("json") ||
    mime.includes("svg")
  );
}

async function applyBundleNative(version: string, files: Map<string, Uint8Array>): Promise<void> {
  const root = `frontend-update/${version}`;

  await Filesystem.rmdir({
    path: root,
    directory: Directory.Data,
    recursive: true,
  }).catch(() => {});

  for (const [path, bytes] of files) {
    await Filesystem.writeFile({
      path: `${root}/${path}`,
      directory: Directory.Data,
      data: bytesToBase64(bytes),
      recursive: true,
    });
  }

  await Filesystem.writeFile({
    path: `${root}/version.txt`,
    directory: Directory.Data,
    data: version,
    encoding: Encoding.UTF8,
  });

  const { path: previousPath } = await WebView.getServerBasePath().catch(
    () => ({ path: "" }),
  );
  const previousVersionMatch = previousPath.match(
    /frontend-update\/([^/]+)\/?$/,
  );

  const { uri } = await Filesystem.getUri({
    path: root,
    directory: Directory.Data,
  });
  const nativePath = uri.replace(/^file:\/\//, "");
  await WebView.setServerBasePath({ path: nativePath });
  await WebView.persistServerBasePath();

  if (previousVersionMatch && previousVersionMatch[1] !== version) {
    await Filesystem.rmdir({
      path: `frontend-update/${previousVersionMatch[1]}`,
      directory: Directory.Data,
      recursive: true,
    }).catch(() => {});
  }
}

async function applyBundleWeb(decoded: Map<string, { bytes: Uint8Array; mime: string }>): Promise<void> {
  const textDecoder = new TextDecoder();
  const textContents = new Map<string, string>();
  for (const [path, { bytes, mime }] of decoded) {
    if (isTextMime(mime)) textContents.set(path, textDecoder.decode(bytes));
  }

  const indexHtml = textContents.get("index.html");
  if (!indexHtml) throw new Error("Bundle is missing index.html");
  textContents.delete("index.html");

  const blobUrls = new Map<string, string>();
  for (const [path, { bytes, mime }] of decoded) {
    blobUrls.set(
      path,
      URL.createObjectURL(new Blob([bytes as BlobPart], { type: mime })),
    );
  }
  for (const [path, text] of textContents) {
    let rewritten = text;
    for (const [otherPath, url] of blobUrls) {
      if (otherPath === path) continue;
      const filename = otherPath.split("/").pop()!;
      rewritten = rewritten.split(filename).join(url);
    }
    const mime = decoded.get(path)!.mime;
    URL.revokeObjectURL(blobUrls.get(path)!);
    blobUrls.set(
      path,
      URL.createObjectURL(new Blob([rewritten], { type: mime })),
    );
    textContents.set(path, rewritten);
  }

  const scriptMatch = indexHtml.match(
    /<script[^>]+type="module"[^>]+src="([^"]+)"/,
  );
  if (!scriptMatch)
    throw new Error("Bundle's index.html has no module entry script");
  const entryPath = scriptMatch[1].replace(/^\//, "");
  const entryUrl = blobUrls.get(entryPath);
  if (!entryUrl)
    throw new Error(`Entry script ${entryPath} missing from bundle`);

  for (const match of indexHtml.matchAll(
    /<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"/g,
  )) {
    const cssPath = match[1].replace(/^\//, "");
    const cssUrl = blobUrls.get(cssPath);
    if (cssUrl) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = cssUrl;
      document.head.appendChild(link);
    }
  }

  const target = document.getElementById("app");
  if (!target) throw new Error("Missing #app root element");
  window.__advantagescoutUnmount?.();
  target.innerHTML = "";
  await import(/* @vite-ignore */ entryUrl);
}

let checkInFlight: Promise<string> | null = null;

export function checkForFrontendUpdate(): Promise<string> {
  if (checkInFlight) return checkInFlight;
  checkInFlight = runCheck().finally(() => {
    checkInFlight = null;
  });
  return checkInFlight;
}

let lastFailure: { version: string; at: number } | null = null;
const FAILURE_RETRY_COOLDOWN_MS = 60_000;

async function runCheck(): Promise<string> {
  try {
    const [localVersion, remoteRes] = await Promise.all([
      getRunningVersion(),
      api.fetch("/api/frontend_version"),
    ]);
    if (!remoteRes.ok)
      return `Could not check frontend version (${remoteRes.status}).`;
    const { version: remoteVersion } = (await remoteRes.json()) as {
      version: string;
    };

    if (localVersion === remoteVersion) {
      return `Frontend up to date (${remoteVersion}).`;
    }

    if (
      lastFailure &&
      lastFailure.version === remoteVersion &&
      Date.now() - lastFailure.at < FAILURE_RETRY_COOLDOWN_MS
    ) {
      return `Skipping retry of ${remoteVersion} (failed recently; will retry later).`;
    }

    if (isOnScoutingForm()) {
      return `Deferring update to ${remoteVersion} (now on the scouting form).`;
    }

    try {
      frontendUpdateState.phase = "downloading";

      const localFiles = await getLocalFiles();
      const fileSignatures: FileSignature[] = [];
      for (const [path, data] of localFiles) {
        fileSignatures.push({ path, size: data.length, blocks: await computeSignatures(data, RSYNC_BLOCK_SIZE) });
      }
      console.log(
        `[frontend-update] diffing against ${localFiles.size} local file(s)` +
          (localFiles.size === 0 ? " (none found -- this transfer will be a full download)" : ""),
      );

      let deltaRes: Response;
      try {
        deltaRes = await api.fetch(
          "/api/frontend_delta",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ files: fileSignatures }),
          },
          (current, max) => {
            frontendUpdateState.downloadProgress = { current, max };
          },
        );
      } finally {
        frontendUpdateState.downloadProgress = null;
      }
      if (!deltaRes.ok) throw new Error(`Server returned ${deltaRes.status}`);
      const manifest = (await deltaRes.json()) as DeltaManifest;
      const copyOps = manifest.files.reduce((n, f) => n + f.ops.filter((op) => "c" in op).length, 0);
      const literalOps = manifest.files.reduce((n, f) => n + f.ops.filter((op) => "d" in op).length, 0);
      const literalB64Bytes = manifest.files.reduce((n, f) => n + (f.literal?.length ?? 0), 0);
      console.log(
        `[frontend-update] delta response: ${copyOps} copy op(s), ${literalOps} literal span(s), ` +
          `${literalB64Bytes} base64 byte(s) of literal data across ${manifest.files.length} file(s)`,
      );

      frontendUpdateState.phase = "installing";
      try {
        const rawFiles = new Map<string, Uint8Array>();
        for (const fileDelta of manifest.files) {
          rawFiles.set(fileDelta.path, await applyDelta(fileDelta, localFiles, manifest.blockSize));
        }

        if (Capacitor.isNativePlatform()) {
          await applyBundleNative(manifest.version, rawFiles);
        } else {
          const withMime = new Map<string, { bytes: Uint8Array; mime: string }>();
          for (const fileDelta of manifest.files) {
            withMime.set(fileDelta.path, { bytes: rawFiles.get(fileDelta.path)!, mime: fileDelta.mime });
          }
          await applyBundleWeb(withMime);
        }

        activeFiles = rawFiles;
      } catch (e) {
        lastFailure = { version: manifest.version, at: Date.now() };
        throw e;
      }
      lastFailure = null;
      appliedVersion = manifest.version;

      return Capacitor.isNativePlatform()
        ? `Updated frontend ${localVersion} -> ${manifest.version} (persisted — survives app restart).`
        : `Updated frontend ${localVersion} -> ${manifest.version} (applied for this session).`;
    } finally {
      frontendUpdateState.phase = null;
    }
  } catch (e) {
    const message = `Frontend update failed: ${e instanceof Error ? e.message : String(e)}`;

    console.error("[frontend-update]", message);
    return message;
  }
}
