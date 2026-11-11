<script lang="ts">
  import { gameData, pushUndoSnapshot } from "./store.svelte";

  type GameMode = "Auto" | "Tele";
  type ClimbButton = "L1" | "L2" | "L3";

  let { gamePhase, buttonType }: { gamePhase: GameMode; buttonType: ClimbButton } = $props();

  function fieldName(): string {
    return `${gamePhase}Climb${buttonType}`;
  }

  const state = $derived(Number(gameData.values[fieldName()] ?? 0));
  
  const style = ["btn-accent", "btn-secondary", "btn-success"];

  function cycleClimb() {
    pushUndoSnapshot();
    const field = fieldName();
    const current = Number(gameData.values[field] ?? 0);
    gameData.values[field] = (current + 1) % 3;
  }
</script>

<button class="btn {style[state]}" onclick={cycleClimb}>
  Climb {buttonType}?
</button>
