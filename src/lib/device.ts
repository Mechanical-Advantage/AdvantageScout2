const DEVICE_NAME_KEY = "advantagescout_device_name";

export function getDeviceName(): string {
  return localStorage.getItem(DEVICE_NAME_KEY) ?? "";
}

export function setDeviceName(name: string): void {
  localStorage.setItem(DEVICE_NAME_KEY, name);
}

export function hasDeviceName(): boolean {
  return getDeviceName().trim().length > 0;
}
