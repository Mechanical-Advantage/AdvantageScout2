<script lang="ts">
  import { gameData } from "./store.svelte";
  import NodesButton from "./NodesButton.svelte";
  import LocationSelector from "./LocationSelector.svelte";
  import CurrentTeam from "./CurrentTeam.svelte";
  import UndoButton from "./UndoButton.svelte";
  import DropButton from "./DropButton.svelte";
  import HighGoalIcon from "./icons/HighGoalIcon.svelte";
  import LowGoalIcon from "./icons/LowGoalIcon.svelte";
  import LowbarIcon from "./icons/LowbarIcon.svelte";
  import PortIcon from "./icons/PortIcon.svelte";
  import ChevalIcon from "./icons/ChevalIcon.svelte";
  import RampartsIcon from "./icons/RampartsIcon.svelte";
  import MoatIcon from "./icons/MoatIcon.svelte";
  import DrawIcon from "./icons/DrawIcon.svelte";
  import SallyIcon from "./icons/SallyIcon.svelte";
  import WallIcon from "./icons/WallIcon.svelte";
  import TerrainIcon from "./icons/TerrainIcon.svelte";

  function back(): void {
    gameData.preMatchDone = false;
  }
</script>

<div class="absolute left-[350px] top-[20px]">
  <button class="btn btn-outline" onclick={back}>Back</button>
</div>

<div class="absolute left-[460px] top-[20px]">
  <CurrentTeam />
</div>

<div class="absolute left-[60px] top-[90px] flex flex-col gap-10">
  <NodesButton
    gameMode="Auto"
    node="HighBoulder"
    type="Success"
    label="High Goal"
    icon={HighGoalIcon}
    trackCollect
  />
  <NodesButton
    gameMode="Auto"
    node="LowBoulder"
    type="Success"
    label="Low Goal"
    icon={LowGoalIcon}
    trackCollect
  />
</div>

<div class="absolute left-[750px] top-[450px]">
  <DropButton gameMode="Auto" />
</div>

<div class="absolute left-[850px] top-[90px] flex flex-col gap-10">
  <NodesButton
    gameMode="Auto"
    node="HighBoulder"
    type="Fail"
    label="High Goal"
    icon={HighGoalIcon}
    trackCollect
  />
  <NodesButton
    gameMode="Auto"
    node="LowBoulder"
    type="Fail"
    label="Low Goal"
    icon={LowGoalIcon}
    trackCollect
  />
</div>

<div
  class="absolute left-[60px] top-[90px] flex w-[800px] origin-top scale-[0.75] flex-col gap-4"
>
  <div class="flex items-center justify-center gap-30">
    <div class="flex flex-col items-center gap-1">
      <div class="flex items-center gap-20">
        <NodesButton gameMode="Auto" node="LowbarCross" type="Success" label="Low Bar" icon={LowbarIcon} />
        <NodesButton gameMode="Auto" node="LowbarCross" type="Fail" label="Low Bar" icon={LowbarIcon} />
      </div>
    </div>
  </div>
  <div class="flex items-center justify-center gap-30">
    <div class="flex flex-col items-center gap-1">
      <div class="flex items-center gap-20">
        <NodesButton gameMode="Auto" node="PortCross" type="Success" label="Portcullis" icon={PortIcon} />
        <NodesButton gameMode="Auto" node="PortCross" type="Fail" label="Portcullis" icon={PortIcon} />
      </div>
    </div>
    <div class="flex flex-col items-center gap-1">
      <div class="flex items-center gap-20">
        <NodesButton gameMode="Auto" node="ChevalCross" type="Success" label="Cheval" icon={ChevalIcon} />
        <NodesButton gameMode="Auto" node="ChevalCross" type="Fail" label="Cheval" icon={ChevalIcon} />
      </div>
    </div>
  </div>
  <div class="flex items-center justify-center gap-30">
    <div class="flex flex-col items-center gap-1">
      <div class="flex items-center gap-20">
        <NodesButton gameMode="Auto" node="RampartsCross" type="Success" label="Ramparts" icon={RampartsIcon} />
        <NodesButton gameMode="Auto" node="RampartsCross" type="Fail" label="Ramparts" icon={RampartsIcon} />
      </div>
    </div>
    <div class="flex flex-col items-center gap-1">
      <div class="flex items-center gap-20">
        <NodesButton gameMode="Auto" node="MoatCross" type="Success" label="Moat" icon={MoatIcon} />
        <NodesButton gameMode="Auto" node="MoatCross" type="Fail" label="Moat" icon={MoatIcon} />
      </div>
    </div>
  </div>
  <div class="flex items-center justify-center gap-30">
    <div class="flex flex-col items-center gap-1">
      <div class="flex items-center gap-20">
        <NodesButton gameMode="Auto" node="DrawCross" type="Success" label="Drawbridge" icon={DrawIcon} />
        <NodesButton gameMode="Auto" node="DrawCross" type="Fail" label="Drawbridge" icon={DrawIcon} />
      </div>
    </div>
    <div class="flex flex-col items-center gap-1">
      <div class="flex items-center gap-20">
        <NodesButton gameMode="Auto" node="SallyCross" type="Success" label="Sally" icon={SallyIcon} />
        <NodesButton gameMode="Auto" node="SallyCross" type="Fail" label="Sally" icon={SallyIcon} />
      </div>
    </div>
  </div>
  <div class="flex items-center justify-center gap-30">
    <div class="flex flex-col items-center gap-1">
      <div class="flex items-center gap-20">
        <NodesButton gameMode="Auto" node="WallCross" type="Success" label="Wall" icon={WallIcon} />
        <NodesButton gameMode="Auto" node="WallCross" type="Fail" label="Wall" icon={WallIcon} />
      </div>
    </div>
    <div class="flex flex-col items-center gap-1">
      <div class="flex items-center gap-20">
        <NodesButton gameMode="Auto" node="TerrainCross" type="Success" label="Terrain" icon={TerrainIcon} />
        <NodesButton gameMode="Auto" node="TerrainCross" type="Fail" label="Terrain" icon={TerrainIcon} />
      </div>
    </div>
  </div>
</div>

<div class="absolute left-[750px] top-[160px]">
  <LocationSelector />
</div>

<div class="absolute left-[850px] top-[480px]">
  <UndoButton />
</div>
