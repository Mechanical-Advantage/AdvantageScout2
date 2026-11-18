import { push } from "svelte-spa-router";
import { fetchGameFields } from "@lib/scouts";
import { getDeviceName } from "@lib/device";
import { queueSubmission, flushQueue } from "@lib/upload-queue.svelte";
import { scoutingSession } from "@lib/scouting-store.svelte";

type FormValue = number | string | boolean;

export function createScoutingForm(mode: "pit" | "super") {
  const form = $state({
    loading: true,
    loadError: null as string | null,
    values: {} as Record<string, FormValue>,
  });

  fetchGameFields(mode)
    .then((data) => {
      form.values = { ...(data.fields as Record<string, FormValue>) };
    })
    .catch((e) => {
      form.loadError = e instanceof Error ? e.message : String(e);
    })
    .finally(() => {
      form.loading = false;
    });

  function sanitize(value: FormValue): FormValue {
    return typeof value === "string"
      ? value.replace(/[^\x00-\x7F]/g, "")
      : value;
  }

  function buildPayloadRow(): Record<string, unknown> {
    const row: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(form.values))
      row[key] = sanitize(value);
    row.Mode = mode;
    row.Device = getDeviceName();
    row.Scout = scoutingSession.scout;
    if (mode === "pit") {
      row.Team = Number(scoutingSession.team);
    } else {
      row.Team1 = Number(scoutingSession.team1);
      row.Team2 = Number(scoutingSession.team2);
      row.Team3 = Number(scoutingSession.team3);
      row.Alliance = scoutingSession.alliance;
    }
    return row;
  }

  function submit(): void {
    queueSubmission(buildPayloadRow());
    flushQueue();
    push("/");
  }

  return { form, submit };
}
