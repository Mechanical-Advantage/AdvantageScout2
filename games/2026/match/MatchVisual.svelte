<script lang="ts">
  import { gameData, loadMatchFields } from "./store.svelte";
  import AutoTab from "./AutoTab.svelte";
  import TeleopTab from "./TeleopTab.svelte";
  import PostgameTab from "./PostgameTab.svelte";
  import PreMatchTab from "./PreMatchTab.svelte";

  const AUTO_SCALE_TO_FIT = true;
  const CANVAS_WIDTH = 1024;
  const CANVAS_HEIGHT = 576;

  const TABS = [
    {
      title: "Auto",
      color: "#f01818",
      inactiveBg: "#f0181840",
      activeBg: "#f01818bb",
    },
    {
      title: "Teleop",
      color: "#2ef018",
      inactiveBg: "#2ef01840",
      activeBg: "#2ef018bb",
    },
    {
      title: "Postgame",
      color: "#7618f0",
      inactiveBg: "#7618f040",
      activeBg: "#7618f0bb",
    },
  ] as const;

  loadMatchFields();

  gameData.activeTab = 0;
  gameData.preMatchDone = false;
  gameData.liveLocation = "Floor";
  gameData.gameShift = 0;
  gameData.fuelButtonTap = false;
  gameData.fuelButtonAmount = 1;
  gameData.fuelButtonSpeedMs = 200;
  gameData.fuelCycleCountSuccess = 0;
  gameData.fuelCycleCountFail = 0;
  gameData.values["PostgameGameShift"] = 0;
  gameData.values["PostgameActiveTab"] = 0;

  function setActiveTab(index: number): void {
    gameData.activeTab = index;
    gameData.values["PostgameActiveTab"] = index;
  }

  let wrapperEl: HTMLDivElement | undefined = $state();
  let scale = $state(1);

  function updateScale(el: HTMLDivElement) {
    if (!AUTO_SCALE_TO_FIT) {
      scale = 1;
      return;
    }
    const width = el.clientWidth;
    
    let trailing = 0;
    for (let node = el.parentElement; node && node !== document.body; node = node.parentElement) {
      const cs = getComputedStyle(node);
      trailing += parseFloat(cs.paddingBottom) + parseFloat(cs.marginBottom) + parseFloat(cs.borderBottomWidth);
    }
    const availableHeight = window.innerHeight - el.getBoundingClientRect().top - trailing;
    if (width <= 0 || availableHeight <= 0) return;
    scale = Math.min(width / CANVAS_WIDTH, availableHeight / CANVAS_HEIGHT);
  }

  $effect(() => {
    if (!wrapperEl) return;
    updateScale(wrapperEl);
    if (!AUTO_SCALE_TO_FIT) return;
    const recompute = () => updateScale(wrapperEl!);
    const ro = new ResizeObserver(recompute);
    ro.observe(wrapperEl);
    window.addEventListener("resize", recompute);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", recompute);
    };
  });
</script>

<div class="relative -mx-4 flex flex-col">
  {#if gameData.loading}
    <p class="px-4 text-fg-muted">Loading match fields...</p>
  {:else if gameData.loadError}
    <p class="px-4 text-danger">Failed to load fields: {gameData.loadError}</p>
  {:else if !gameData.preMatchDone}
    <div
      bind:this={wrapperEl}
      class="relative w-full"
      style="height: {CANVAS_HEIGHT * scale}px;"
    >
      <div
        class="absolute left-0 top-0 origin-top-left"
        style="width: {CANVAS_WIDTH}px; height: {CANVAS_HEIGHT}px; transform: scale({scale});"
      >
        <PreMatchTab />
      </div>
    </div>
  {:else}
    <div class="flex">
      {#each TABS as tab, i}
        <button
          class="flex-1 border-b-[3px] py-2.5 text-sm duration-180 {gameData.activeTab ===
          i
            ? 'font-bold text-fg opacity-100'
            : 'font-medium text-fg opacity-70'}"
          style="background-color: {gameData.activeTab === i
            ? tab.activeBg
            : tab.inactiveBg}; border-bottom-color: {gameData.activeTab === i
            ? tab.color
            : 'transparent'};"
          onclick={() => setActiveTab(i)}
        >
          {tab.title}
        </button>
      {/each}
    </div>

    <div
      bind:this={wrapperEl}
      class="relative w-full"
      style="height: {CANVAS_HEIGHT * scale}px;"
    >
      <div
        class="absolute left-0 top-0 origin-top-left"
        style="width: {CANVAS_WIDTH}px; height: {CANVAS_HEIGHT}px; transform: scale({scale});"
      >
        <div
          class="absolute inset-0 {gameData.activeTab === 0
            ? ''
            : 'pointer-events-none opacity-0'}"
        >
          <AutoTab />
        </div>
        <div
          class="absolute inset-0 {gameData.activeTab === 1
            ? ''
            : 'pointer-events-none opacity-0'}"
        >
          <TeleopTab />
        </div>
        <div
          class="absolute inset-0 {gameData.activeTab === 2
            ? ''
            : 'pointer-events-none opacity-0'}"
        >
          <PostgameTab />
        </div>
      </div>
    </div>
  {/if}
</div>
