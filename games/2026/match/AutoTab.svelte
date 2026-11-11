<script lang="ts">
  import { gameData } from "./store.svelte";
  import NodesButton from "./NodesButton.svelte";
  import ButtonModeToggle from "./ButtonModeToggle.svelte";
  import TowerClimb from "./TowerClimb.svelte";
  import LocationSelector from "./LocationSelector.svelte";
  import CurrentTeam from "./CurrentTeam.svelte";
  import UndoButton from "./UndoButton.svelte";

  function back(): void {
    gameData.preMatchDone = false;
  }
</script>

<div class="absolute left-[350px] top-[30px]">
  <button class="btn btn-outline" onclick={back}>Back</button>
</div>

<div class="absolute left-[425px] top-[30px]">
  <CurrentTeam />
</div>

<div class="absolute left-[60px] top-[40px] flex flex-col gap-[70px]">
  <NodesButton gameMode="Auto" level={3} type="Success" />
  <NodesButton gameMode="Auto" level={2} type="Success" />
  <NodesButton gameMode="Auto" level={1} type="Success" />
</div>

<div class="absolute left-[400px] top-[280px]">
  <ButtonModeToggle />
</div>

<div class="absolute left-[300px] top-[150px]">
  <TowerClimb gamePhase="Auto" buttonType="L1" />
</div>

<div class="absolute left-[680px] top-[80px]">
  <LocationSelector gameMode="Auto" />
</div>

<div class="absolute left-[900px] top-[40px] flex flex-col gap-[70px]">
  <div class="h-20 w-20 pointer-events-none"></div>
  <NodesButton gameMode="Auto" level={2} type="Fail" />
  <NodesButton gameMode="Auto" level={1} type="Fail" />
</div>

<div class="absolute left-[850px] top-[480px]">
  <UndoButton />
</div>
