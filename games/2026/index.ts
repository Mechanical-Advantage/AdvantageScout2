import Match from "./Match.svelte";
import Pit from "./Pit.svelte";
import Super from "./Super.svelte";
import type { GameModule } from "@lib/games-registry";

const gameModule: GameModule = { Match, Pit, Super };
export default gameModule;
