const SERVER_ADDRESS_KEY = "serverAddress";

export function getServerAddress(): string {
  return localStorage.getItem(SERVER_ADDRESS_KEY) ?? "";
}

export function setServerAddress(value: string): void {
  localStorage.setItem(SERVER_ADDRESS_KEY, value.trim());
}
