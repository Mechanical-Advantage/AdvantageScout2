<script>
    import { onMount } from "svelte";
    let cols = 3;
    let scoutList = [];

    let name = "";
    onMount(async () => {
        const response = await fetch("/admin/get_scouts", { method: "GET" });
        const data = await response.json();
        scoutList = data;
    });

    const addScout = () => {
        scoutList = [
            ...scoutList,
            {
                name,
                enabled: false
            }
        ];
        doPost(name, "/admin/add_scout");
        name = "";
    };

    const remove = (scout) => {
        console.log(scout);
        doPost(scout.name, "/admin/remove_scout");
        scoutList = scoutList.filter((i) => i !== scout);
    };

    const toggle = (scout) => {
        scout.enabled = !scout.enabled;
        scoutList = scoutList;
        doPost(scout.name, "/admin/toggle_scout");
    };

    async function doPost(scoutName, actionUrl) {
        console.log(actionUrl);
        const formData = new FormData();
        formData.append("scout", scoutName);
        const res = await fetch(actionUrl, {
            method: "POST",
            body: formData
        });
    }
    async function getScouts() {
        const response = await fetch("/admin/get_scouts", { method: "GET" });
        const data = await response.json();
        scoutList = data;
    }
</script>

<div>
    <h1>Available Scouts</h1>

    <form on:submit|preventDefault={addScout}>
        <label for="name">Add a scout</label>
        <input id="name" type="text" bind:value={name} />
    </form>
</div>
<div class="grid grid-cols-3 gap-4 text-sm w-max font-bold text-white text-center">
    {#each scoutList as scout, i}
        <button class:enabled={scoutList[i].enabled} on:click={() => toggle(scoutList[i])}>
            {scoutList[i].name}
        </button>
    {/each}
</div>
