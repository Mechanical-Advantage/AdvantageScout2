const SHOW_CHUNK_PROGRESS_KEY = "advantagescout_show_chunk_progress";

function loadShowChunkProgress(): boolean {
  return localStorage.getItem(SHOW_CHUNK_PROGRESS_KEY) === "true";
}

export const devTools = $state<{ showChunkProgress: boolean }>({
  showChunkProgress: loadShowChunkProgress(),
});

export function setShowChunkProgress(value: boolean): void {
  devTools.showChunkProgress = value;
  localStorage.setItem(SHOW_CHUNK_PROGRESS_KEY, value ? "true" : "false");
}
