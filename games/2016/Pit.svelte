<script lang="ts">
  import { createScoutingForm } from "@lib/scouting-form.svelte";
  import ScoutSelect from "@components/scout/ScoutSelect.svelte";
  import ScoutText from "@components/scout/ScoutText.svelte";
  import ScoutNumber from "@components/scout/ScoutNumber.svelte";
  import ScoutCheck from "@components/scout/ScoutCheck.svelte";
  import ScoutRating from "@components/scout/ScoutRating.svelte";

  const { form, submit } = createScoutingForm("pit");

  const canSubmit = $derived(
    String(form.values["PitDriveTrain"] ?? "").trim() !== "" &&
      String(form.values["PitProgrammingLanguage"] ?? "").trim() !== "" &&
      Number(form.values["PitDriveSpeed"] ?? 0) > 0 &&
      Number(form.values["PitWidth"] ?? 0) > 0 &&
      Number(form.values["PitLength"] ?? 0) > 0 &&
      Number(form.values["PitBuildQuality"] ?? 0) > 0 &&
      Number(form.values["PitBumperQuality"] ?? 0) > 0 &&
      Number(form.values["PitElectricalQuality"] ?? 0) > 0,
  );
</script>

{#if form.loading}
  <p class="text-fg-muted">Loading pit fields...</p>
{:else if form.loadError}
  <p class="text-danger">Failed to load fields: {form.loadError}</p>
{:else}
  <div class="flex flex-col gap-3">
    <ScoutSelect
      values={form.values}
      field="PitDriveTrain"
      label="Drive Train"
      options={["Tank", "West Coast", "Mecanum", "Swerve", "H-Drive", "Other (see comment)"]}
    />
    <ScoutSelect
      values={form.values}
      field="PitProgrammingLanguage"
      label="Programming Language"
      options={["Java", "C++", "Python", "LabVIEW", "ROS", "Other (see comment)"]}
    />
    <ScoutNumber
      values={form.values}
      field="PitDriveSpeed"
      label="Drive Speed (ft/s)"
    />
    <ScoutNumber values={form.values} field="PitWidth" label="Width (in)" />
    <ScoutNumber values={form.values} field="PitLength" label="Length (in)" />
    <ScoutNumber values={form.values} field="PitHeight" label="Height (in)" />

    <ScoutRating
      values={form.values}
      field="PitBuildQuality"
      label="Build Quality"
    />
    <ScoutRating
      values={form.values}
      field="PitBumperQuality"
      label="Bumper Quality"
    />
    <ScoutRating
      values={form.values}
      field="PitElectricalQuality"
      label="Electrical Quality"
    />

    <ScoutCheck values={form.values} field="PitCanClimb" label="Can climb" />
    <ScoutCheck
      values={form.values}
      field="PitCanCrossMoat"
      label="Can cross moat"
    />
    <ScoutCheck
      values={form.values}
      field="PitCanFloorIntake"
      label="Can floor intake"
    />
    <ScoutCheck
      values={form.values}
      field="PitHasAdvantageKit"
      label="Has AdvantageKit"
    />
    <ScoutCheck
      values={form.values}
      field="PitHasAdvantageScope"
      label="Has AdvantageScope"
    />
    <ScoutCheck values={form.values} field="PitHaveAuto" label="Has auto" />

    <ScoutText
      values={form.values}
      field="PitComment"
      label="Comment"
      multiline
    />

    <button
      class="btn {canSubmit ? 'btn-primary' : 'btn-disabled'} w-full"
      onclick={submit}>Save</button
    >
  </div>
{/if}
