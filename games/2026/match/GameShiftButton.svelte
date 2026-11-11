<script lang="ts">
  import { gameData } from "./store.svelte";

  const SHIFT_NAMES = ["ST", "S1", "S2", "S3", "S4", "SE"] as const;
  const SHIFT_LABELS = ["Transition", "Shift 1", "Shift 2", "Shift 3", "Shift 4", "Endgame"];
  const SHIFT_COLORS = ["#ff0000", "#ff9600", "#ffff00", "#19c819", "#0033ff", "#a000a0"];

  const color = $derived(SHIFT_COLORS[gameData.gameShift]);
  const textDark = $derived(gameData.gameShift === 2);

  function advanceShift() {
    gameData.gameShift = (gameData.gameShift + 1) % SHIFT_NAMES.length;
    gameData.values["PostgameGameShift"] = gameData.gameShift;
  }
</script>

<button
  class="min-w-[200px] badge rounded-md py-3 text-m {textDark
    ? 'text-black'
    : 'text-white'}"
  style="background-color: {color};"
  onclick={advanceShift}
>
  {SHIFT_LABELS[gameData.gameShift]}
</button>
