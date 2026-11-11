<script lang="ts">
  import CloseIcon from "@components/icons/CloseIcon.svelte";

  let {
    modal,
    onRename,
    onClearStorage,
    onClose,
  }: {
    modal: { device: string; rename: string; error: string; busy: boolean } | null;
    onRename: () => void;
    onClearStorage: () => void;
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
      <h3 class="mb-1 text-lg text-fg">Edit Device</h3>
      <p class="mb-4 text-sm text-fg-muted opacity-70">{modal.device}</p>
      <label class="mb-1.5 block text-sm text-fg-muted" for="rename">New name</label>
      <input
        id="rename"
        class="input input-bordered mb-2 w-full"
        bind:value={modal.rename}
        disabled={modal.busy}
        placeholder="Enter new device name"
      />
      {#if modal.error}
        <p class="mb-2 text-sm text-danger">{modal.error}</p>
      {/if}
      <div class="mt-3 flex justify-end gap-2">
        <button class="btn btn-primary" onclick={onRename} disabled={modal.busy}>
          {modal.busy ? "Renaming..." : "Rename"}
        </button>
        <button class="btn btn-outline" onclick={onClearStorage} disabled={modal.busy}>Clear Storage</button>
      </div>
      <div class="mt-2 flex justify-end">
        <button class="btn btn-outline btn-sm" onclick={onClose}>Cancel</button>
      </div>
    {/if}
  </div>
  <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>
