const SETTINGS_KEY = "advantagescout_settings";

export interface Settings {
  serverAddress: string;
  preferWifi: boolean;
  showChunkProgress: boolean;
}

const DEFAULTS: Settings = {
  serverAddress: "",
  preferWifi: false,
  showChunkProgress: false,
};

function load(): Settings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...DEFAULTS, ...(JSON.parse(raw) as Partial<Settings>) };
  } catch {
    // fall through to defaults
  }
  return { ...DEFAULTS };
}

export const settings = $state<Settings>(load());

export function updateSettings(patch: Partial<Settings>): void {
  Object.assign(settings, patch);
  if (typeof patch.serverAddress === "string")
    settings.serverAddress = patch.serverAddress.trim();
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    // storage unavailable; settings still apply for this session
  }
}

export function resetSettings(): void {
  Object.assign(settings, DEFAULTS);
}
