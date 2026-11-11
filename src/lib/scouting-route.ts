import { get } from "svelte/store";
import { location } from "svelte-spa-router";

export function isOnScoutingForm(): boolean {
  const path = get(location);
  return path === "/game" || path.startsWith("/scouting/");
}

export function confirmLeaveScouting(): boolean {
  if (!isOnScoutingForm()) return true;
  return confirm("Stop scouting? Your data will NOT be saved!");
}
