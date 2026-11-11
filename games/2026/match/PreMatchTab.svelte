<script lang="ts">
  import { gameData } from "./store.svelte";
  import { scoutingSession } from "@lib/scouting-store.svelte";
  import { fetchGlobalSettings } from "@lib/scouts";
  import CurrentTeam from "./CurrentTeam.svelte";

  const ZONES = [
    { num: 1, y: 10, height: 65 },
    { num: 2, y: 75, height: 60 },
    { num: 3, y: 135, height: 60 },
    { num: 4, y: 195, height: 60 },
    { num: 5, y: 255, height: 55 },
  ];

  const VIEW_WIDTH = 220;

  let fieldOrientation: number = $state(1);
  fetchGlobalSettings()
    .then((settings) => {
      const value = Number(settings["Field Orientation"]);
      if (!Number.isNaN(value)) fieldOrientation = value;
    })
    .catch(() => {
      // No server
    });

  const allianceOnLeft = $derived(
    (scoutingSession.alliance === "Red") === (fieldOrientation === 1),
  );
  const flipped = $derived(!allianceOnLeft);

  function mirrorX(x: number): number {
    return flipped ? VIEW_WIDTH - x : x;
  }

  function mirrorRectX(x: number, width: number): number {
    return flipped ? VIEW_WIDTH - x - width : x;
  }

  const startPosition = $derived(Number(gameData.values["AutoStartPosition"] ?? 0));
  const strokeColor = $derived(scoutingSession.alliance === "Red" ? "#FF0000" : "#002eff");

  function selectZone(num: number): void {
    gameData.values["AutoStartPosition"] = num;
  }

  function startMatch(): void {
    if (startPosition <= 0) return;
    gameData.preMatchDone = true;
  }
</script>

<div class="absolute left-[425px] top-[20px]">
  <CurrentTeam />
</div>

<div class="absolute left-[370px] top-[70px] flex flex-col items-center gap-4">
  <svg viewBox="0 0 {VIEW_WIDTH} 330" width="260" height="390">
    {#each ZONES as zone}
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <rect
        x={mirrorRectX(160, 50)}
        y={zone.y}
        width="50"
        height={zone.height}
        role="button"
        tabindex="0"
        aria-label="Starting position {zone.num}"
        class="cursor-pointer"
        fill={startPosition === zone.num ? strokeColor : "transparent"}
        fill-opacity={startPosition === zone.num ? 0.35 : 0}
        stroke={strokeColor}
        stroke-width="1"
        stroke-dasharray="4 2"
        onclick={() => selectZone(zone.num)}
      />
    {/each}

    <!-- Field outline -->
    <rect
      x={mirrorRectX(10, 200)}
      y="20"
      width="200"
      height="290"
      fill="none"
      stroke={strokeColor}
      stroke-width="3"
      pointer-events="none"
    />

    <!-- Depot -->
    <polyline
      points="{mirrorX(10)},50 {mirrorX(50)},50 {mirrorX(50)},100 {mirrorX(10)},100"
      fill="none"
      stroke={strokeColor}
      stroke-width="3"
      pointer-events="none"
    />

    <!-- Tower -->
    <polyline
      points="{mirrorX(10)},160 {mirrorX(80)},160 {mirrorX(80)},200 {mirrorX(10)},200"
      fill="none"
      stroke={strokeColor}
      stroke-width="3"
      pointer-events="none"
    />

    <!-- Bumps -->
    <rect x={mirrorRectX(180, 30)} y="75" width="30" height="60" fill={strokeColor} pointer-events="none" />
    <rect x={mirrorRectX(180, 30)} y="195" width="30" height="60" fill={strokeColor} pointer-events="none" />

    <!-- Starting line -->
    <line
      x1={mirrorX(180)}
      y1="20"
      x2={mirrorX(180)}
      y2="310"
      stroke="#808080"
      stroke-width="3"
      pointer-events="none"
    />

    <!-- Zone numbers -->
    {#each ZONES as zone}
      <text
        x={mirrorX(185)}
        y={zone.y + zone.height / 2}
        text-anchor="middle"
        dominant-baseline="middle"
        font-size="14"
        fill={startPosition === zone.num ? "white" : strokeColor}
        pointer-events="none"
      >
        {zone.num}
      </text>
    {/each}
  </svg>

  <p class="text-sm text-fg-muted">
    {startPosition > 0 ? `Starting position ${startPosition} selected` : "Tap your robot's starting position"}
  </p>

  <button class="btn btn-accent w-40 {startPosition > 0 ? '' : 'btn-disabled'}" onclick={startMatch}>
    Start
  </button>
</div>
