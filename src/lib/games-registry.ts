import type { Component } from "svelte";

export interface GameModule {
  Match: Component;
  Pit: Component;
  Super: Component;
}

const modules = import.meta.glob("../../games/*/index.ts") as Record<
  string,
  () => Promise<{ default: GameModule }>
>;

function yearFromPath(path: string): string | null {
  const match = path.match(/\/games\/([^/]+)\/index\.ts$/);
  return match ? match[1] : null;
}

export function availableGameYears(): string[] {
  return Object.keys(modules)
    .map(yearFromPath)
    .filter((y): y is string => y !== null);
}

export async function loadGameModule(year: string): Promise<GameModule | null> {
  for (const [path, loader] of Object.entries(modules)) {
    if (yearFromPath(path) === year) {
      const mod = await loader();
      return mod.default;
    }
  }
  return null;
}
