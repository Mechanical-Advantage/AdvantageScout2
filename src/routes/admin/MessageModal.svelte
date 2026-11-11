<script lang="ts">
  import CloseIcon from "@components/icons/CloseIcon.svelte";

  let {
    modal,
    onSend,
    onClose,
  }: {
    modal: { targets: string[]; text: string; centered: boolean; sending: boolean } | null;
    onSend: () => void;
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
      <h3 class="mb-1 text-lg text-fg">Send Message</h3>
      <p class="mb-4 text-sm text-fg-muted opacity-70">
        {modal.targets.length === 1 ? modal.targets[0] : `${modal.targets.length} devices`}
      </p>
      <label class="mb-1.5 block text-sm text-fg-muted" for="message-text">Message</label>
      <textarea
        id="message-text"
        class="textarea textarea-bordered mb-2 w-full"
        bind:value={modal.text}
        disabled={modal.sending}
        placeholder="Enter toast message"
      ></textarea>
      <label class="label mb-3 cursor-pointer justify-start gap-2">
        <input type="checkbox" class="checkbox checkbox-accent" bind:checked={modal.centered} disabled={modal.sending} />
        <span class="label-text text-fg">Centered</span>
      </label>
      <div class="flex justify-end gap-2">
        <button class="btn btn-primary" onclick={onSend} disabled={modal.sending || modal.text.trim().length === 0}>
          {modal.sending ? "Sending..." : "Send"}
        </button>
        <button class="btn btn-outline" onclick={onClose}>Cancel</button>
      </div>
    {/if}
  </div>
  <form method="dialog" class="modal-backdrop"><button>close</button></form>
</dialog>
