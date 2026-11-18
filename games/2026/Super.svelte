<script lang="ts">
  import { createScoutingForm } from "@lib/scouting-form.svelte";
  import { scoutingSession } from "@lib/scouting-store.svelte";
  import ScoutSuperTeam from "@components/scout/ScoutSuperTeam.svelte";

  const { form, submit } = createScoutingForm("super");

  const canSubmit = $derived(
    String(form.values["SuperTeam1Comment"] ?? "").trim() !== "" &&
      String(form.values["SuperTeam2Comment"] ?? "").trim() !== "" &&
      String(form.values["SuperTeam3Comment"] ?? "").trim() !== "",
  );
</script>

{#if form.loading}
  <p class="text-fg-muted">Loading super fields...</p>
{:else if form.loadError}
  <p class="text-danger">Failed to load fields: {form.loadError}</p>
{:else}
  <div class="grid gap-3 md:grid-cols-3">
    <ScoutSuperTeam
      values={form.values}
      index={1}
      team={scoutingSession.team1}
    />
    <ScoutSuperTeam
      values={form.values}
      index={2}
      team={scoutingSession.team2}
    />
    <ScoutSuperTeam
      values={form.values}
      index={3}
      team={scoutingSession.team3}
    />
  </div>

  <button
    class="btn {canSubmit ? 'btn-primary' : 'btn-disabled'} mt-4 w-full"
    onclick={submit}>Upload</button
  >
{/if}
