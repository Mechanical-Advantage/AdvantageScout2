<script lang="ts">
  import CloseIcon from "@components/icons/CloseIcon.svelte";

  let {
    modal,
    onSave,
    onClose,
  }: {
    modal: { kind: "match" | "super"; editing: string | null; name: string; pod: string } | null;
    onSave: () => void;
    onClose: () => void;
  } = $props();

  let dialogEl: HTMLDialogElement;

  $effect(() => {
    if (modal) dialogEl?.showModal();
    else dialogEl?.close();
  });
</script>

<dialog bind:this={dialogEl} class="modal" onclose={onClose}>
  <div class="modal-box">
    {#if modal}
      <button class="btn btn-sm btn-circle absolute right-2 top-2" onclick={onClose}><CloseIcon /></button>
      <h3 class="mb-1 text-lg text-fg">
        {modal.editing
          ? modal.kind === "match"
            ? "Edit Match Scout"
            : "Edit Super Scout"
          : modal.kind === "match"
            ? "Add Match Scout"
            : "Add Super Scout"}
      </h3>
      <label class="mb-1.5 mt-3 block text-sm text-fg-muted" for="scout-name">Scout Name</label>
      <input
        id="scout-name"
        class="input input-bordered mb-2 w-full"
        bind:value={modal.name}
        placeholder="Enter scout name"
      />
      {#if modal.kind === "match"}
        <label class="mb-1.5 block text-sm text-fg-muted" for="scout-pod">Pod Number</label>
        <input
          id="scout-pod"
          type="number"
          min="1"
          class="input input-bordered mb-2 w-full"
          bind:value={modal.pod}
          placeholder="1"
        />
      {/if}
      <div class="mt-3 flex justify-end gap-2">
        <button class="btn btn-primary" onclick={onSave}>Save</button>
        <button class="btn btn-outline" onclick={onClose}>Cancel</button>
      </div>
    {/if}
  </div>
  <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>
