<script lang="ts">
  import { gameData, pushUndoSnapshot } from "./store.svelte";

  type GameMode = "Auto" | "Tele";

  let { gamePhase }: { gamePhase: GameMode } = $props();

  const CLIMB_POSITIONS = ["Far", "Middle", "Near", "Edge"];

  function climbField(button: "L1" | "L2" | "L3"): string {
    return `${gamePhase}Climb${button}`;
  }

  function hasClimbed(): boolean {
    if (gamePhase === "Auto") return Number(gameData.values[climbField("L1")] ?? 0) > 0;
    return (["L1", "L2", "L3"] as const).some((b) => Number(gameData.values[climbField(b)] ?? 0) > 0);
  }

  const enabled = $derived(hasClimbed());
  const positionField = $derived(`${gamePhase}ClimbPosition`);
  const position = $derived(Number(gameData.values[positionField] ?? 0));

  function cycleClimbPosition() {
    if (!enabled) return;
    pushUndoSnapshot();
    const current = Number(gameData.values[positionField] ?? 0);
    gameData.values[positionField] = (current + 1) % CLIMB_POSITIONS.length;
  }
</script>

<button class="btn btn-accent" onclick={cycleClimbPosition} disabled={!enabled}>
  Climb {CLIMB_POSITIONS[position]}?
</button>
