const PREFER_WIFI_KEY = "advantagescout_prefer_wifi";

export function getPreferWifi(): boolean {
  return localStorage.getItem(PREFER_WIFI_KEY) === "true";
}

export function setPreferWifi(value: boolean): void {
  localStorage.setItem(PREFER_WIFI_KEY, value ? "true" : "false");
}
