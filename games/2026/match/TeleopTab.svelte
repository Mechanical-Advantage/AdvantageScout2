<script lang="ts">
  import { gameData } from "./store.svelte";
  import NodesButton from "./NodesButton.svelte";
  import ButtonModeToggle from "./ButtonModeToggle.svelte";
  import TowerClimb from "./TowerClimb.svelte";
  import ClimbPositions from "./ClimbPositions.svelte";
  import ClimbTimer from "./ClimbTimer.svelte";
  import LocationSelector from "./LocationSelector.svelte";
  import GameShiftButton from "./GameShiftButton.svelte";
  import CurrentTeam from "./CurrentTeam.svelte";
  import UndoButton from "./UndoButton.svelte";

  gameData.liveLocation = "Floor";
</script>

<div class="absolute left-[425px] top-[30px]">
  <CurrentTeam />
</div>

<div class="absolute left-[300px] top-[169px]">
  <GameShiftButton />
</div>

<div class="absolute left-[600px] top-[14px] flex items-center gap-3">
  <TowerClimb gamePhase="Tele" buttonType="L1" />
  <TowerClimb gamePhase="Tele" buttonType="L2" />
  <TowerClimb gamePhase="Tele" buttonType="L3" />
  <ClimbPositions gamePhase="Tele" />
</div>

<div class="absolute left-[60px] top-[70px] flex flex-col gap-[70px]">
  <NodesButton gameMode="Tele" level={3} type="Success" />
  <NodesButton gameMode="Tele" level={2} type="Success" />
  <NodesButton gameMode="Tele" level={1} type="Success" />
</div>

<div class="absolute left-[400px] top-[310px]">
  <ButtonModeToggle />
</div>

<div class="absolute left-[680px] top-[130px]">
  <LocationSelector gameMode="Tele" />
</div>

<div class="absolute left-[900px] top-[70px] flex flex-col gap-[70px]">
  <div class="h-20 w-20 pointer-events-none"></div>
  <NodesButton gameMode="Tele" level={2} type="Fail" />
  <NodesButton gameMode="Tele" level={1} type="Fail" />
</div>

<div class="absolute left-[900px] top-[96px]">
  <ClimbTimer />
</div>

<div class="absolute left-[850px] top-[480px]">
  <UndoButton />
</div>
