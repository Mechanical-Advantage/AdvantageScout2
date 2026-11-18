<script lang="ts">
  import ScoutText from "./ScoutText.svelte";
  import ScoutRating from "./ScoutRating.svelte";

  let {
    values,
    index,
    team,
  }: {
    values: Record<string, number | string | boolean>;
    index: 1 | 2 | 3;
    team: string;
  } = $props();

  const botStateField = $derived(`SuperTeamBotState${index}`);
  const botState = $derived(Number(values[botStateField] ?? 1));
  const dnp = $derived(Number(values[`SuperTeamDNP${index}`] ?? 0) === 1);
  const watch = $derived(Number(values[`SuperTeamWatch${index}`] ?? 0) === 1);
</script>

<div class="flex flex-col gap-3 rounded-lg border border-border p-3">
  <h2 class="font-heading text-lg font-bold text-fg">Team {team}</h2>

  <ScoutText {values} field="SuperTeam{index}Comment" label="Comment" multiline placeholder="Notes on this team..." />

  <ScoutRating {values} field="SuperTeamRating{index}" label="Team Rating" color="range-success" />
  <ScoutRating {values} field="SuperTeamDriveRating{index}" label="Drive Rating" color="range-success" />
  <ScoutRating {values} field="SuperTeamRobotRating{index}" label="Robot Rating" color="range-success" />

  <div class="flex gap-2">
    <button
      class="btn btn-sm {dnp ? 'btn-error' : 'btn-outline'}"
      onclick={() => (values[`SuperTeamDNP${index}`] = dnp ? 0 : 1)}
    >
      DNP
    </button>
    <button
      class="btn btn-sm {watch ? 'btn-secondary' : 'btn-outline'}"
      onclick={() => (values[`SuperTeamWatch${index}`] = watch ? 0 : 1)}
    >
      Watch?
    </button>
  </div>

  <div class="flex flex-col gap-1">
    <p class="text-sm text-fg">Bot State</p>
    <label class="label cursor-pointer justify-start gap-2 p-0">
      <input type="radio" class="radio radio-sm radio-success" name="botstate{index}" checked={botState === 1} onchange={() => (values[botStateField] = 1)} />
      <span class="label-text text-xs text-fg">No Issues</span>
    </label>
    <label class="label cursor-pointer justify-start gap-2 p-0">
      <input type="radio" class="radio radio-sm radio-warning" name="botstate{index}" checked={botState === 2} onchange={() => (values[botStateField] = 2)} />
      <span class="label-text text-xs text-fg">Comms Issue</span>
    </label>
    <label class="label cursor-pointer justify-start gap-2 p-0">
      <input type="radio" class="radio radio-sm radio-warning" name="botstate{index}" checked={botState === 3} onchange={() => (values[botStateField] = 3)} />
      <span class="label-text text-xs text-fg">Power Issues</span>
    </label>
    <label class="label cursor-pointer justify-start gap-2 p-0">
      <input type="radio" class="radio radio-sm radio-warning" name="botstate{index}" checked={botState === 4} onchange={() => (values[botStateField] = 4)} />
      <span class="label-text text-xs text-fg">Major Malfunction</span>
    </label>
    <label class="label cursor-pointer justify-start gap-2 p-0">
      <input type="radio" class="radio radio-sm radio-error" name="botstate{index}" checked={botState === 5} onchange={() => (values[botStateField] = 5)} />
      <span class="label-text text-xs text-fg">Fell Over</span>
    </label>
    <label class="label cursor-pointer justify-start gap-2 p-0">
      <input type="radio" class="radio radio-sm radio-error" name="botstate{index}" checked={botState === 6} onchange={() => (values[botStateField] = 6)} />
      <span class="label-text text-xs text-fg">Did Not Show</span>
    </label>
  </div>
</div>
