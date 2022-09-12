<script>
    import DragDropList from "./ScoutPrefList.svelte";
    import { onMount } from "svelte";

    let removesItems = false;
    let addPrefName = "";
    let addPrefTeam = "";
    let bulkEntryTeams = [];
    let bulkEntryNames = [];
    let numberOfBulkEntries = 3;

    let data = [
        { team: "6328", scout: "Ayush" },
        { team: "254", scout: "Aryan" },
        { team: "118", scout: "Keith" },
        { team: "3467", scout: "Connor" },
        { team: "1678", scout: "Manthan" }
    ];
    onMount(async () => {
        const response = await fetch("/admin/get_scoutprefs", { method: "GET" });
        const prefs = await response.json();
        data = prefs;
    });
    async function doPost(data, actionUrl) {
        const formData = new FormData();
        console.log("data length".data.length);
        for (let i = 0; i < data.length; i++) {
            formData.append("team", data[i]["team"]);
            formData.append("scout", data[i]["scout"]);
        }

        const res = await fetch(actionUrl, {
            method: "POST",
            data: JSON.stringify(formData)
        });
    }
    async function getScoutPrefs() {
        const response = await fetch("/admin/get_scoutprefs", { method: "GET" });
        const prefs = await response.json();
        data = prefs;
    }
    function addPref() {
        let present = false;
        for (let i = 0; i < data.length; i++) {
            if (data[i].team === addPrefTeam && data[i].scout === addPrefName) {
                present = true;
                break;
            }
        }
        if (!present && addPrefTeam !== "" && addPrefName !== "") {
            data.push({ team: addPrefTeam, scout: addPrefName });
            addPrefName = "";
            addPrefTeam = "";
            data = data;
        }
        console.log("trying to post");
        doPost(data, "/admin/set_scoutprefs");
    }

    function addBulkEntry() {
        numberOfBulkEntries++;
        numberOfBulkEntries = numberOfBulkEntries;
    }
    function resetBulk() {
        numberOfBulkEntries = 3;
        bulkEntryTeams = [];
        bulkEntryNames = [];
    }
    function submitBulk() {
        for (let i = 0; i < numberOfBulkEntries; i++) {
            for (let k = 0; k < numberOfBulkEntries; k++) {
                if (
                    bulkEntryNames[i] !== null &&
                    bulkEntryTeams !== null &&
                    bulkEntryNames[i] !== undefined &&
                    bulkEntryTeams[i] !== undefined
                ) {
                    addPrefName = bulkEntryNames[i];
                    addPrefTeam = bulkEntryTeams[k];
                    addPref();
                }
            }
        }
        resetBulk();
        addPrefName = "";
        addPrefTeam = "";
    }
</script>

<main class="fixed">
    <p />

    <div class="form-control w-[100px] fixed z-40">
        <label class="cursor-pointer label fixed ml-[282px] mt-[90px]">
            <span class="label-text text-white font-bold fixed">Delete</span>
            <input
                type="checkbox"
                scout="removesItems"
                bind:checked={removesItems}
                class="checkbox checkbox-lg checkbox-accent fixed mt-[60px] ml-[5px]"
            />
        </label>
    </div>

    <label class="btn modal-button btn-success btn-square w-20 h-20 z-50 fixed ml-[270px]" for="entry-modal-2">
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2.5"
            stroke="currentColor"
            class="w-14 h-14"
        >
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
    </label>

    <div class="w-[250px] fixed">
        <DragDropList bind:data {removesItems} />
    </div>

    <form on:submit={addPref} action="#">
        <input type="checkbox" id="entry-modal-2" class="modal-toggle" />
        <label for="entry-modal-2" class="modal cursor-pointer">
            <label class="modal-box relative" for="entry-modal-2">
                <input
                    type="text"
                    placeholder="Scout Name"
                    class="input input-bordered w-1/3 max-w-xs"
                    bind:value={addPrefName}
                />
                <input
                    type="text"
                    placeholder="Team #"
                    class="input input-bordered w-1/3 max-w-xs"
                    bind:value={addPrefTeam}
                />
                <input type="submit" class="btn btn-success ml-7 w-24" on:click={addPref} value="Add" />
                <label
                    type="button"
                    for="bulk-modal"
                    class="btn btn-circle btn-warning modal-button fixed btn-xs text-4xs -mt-[10px] -ml-[10px]"
                    on:click={resetBulk}
                >
                    ...
                </label>
            </label>
        </label>
    </form>

    <form on:submit={addPref} action="#">
        <input type="checkbox" id="bulk-modal" class="modal-toggle" />
        <label for="bulk-modal" class="modal cursor-pointer">
            <label class="modal-box relative h-fit" for="bulk-modal">
                {#each Array(numberOfBulkEntries) as _, i}
                    <input
                        type="text"
                        placeholder="Scout Name"
                        class="input input-bordered w-1/3 max-w-xs mt-3"
                        bind:value={bulkEntryNames[i]}
                    />
                    <input
                        type="text"
                        placeholder="Team #"
                        class="input input-bordered w-1/3 max-w-xs mt-3 ml-2"
                        bind:value={bulkEntryTeams[i]}
                    />
                {/each}
                <button class="btn fixed -ml-[180px] mt-[60px] btn-xs" on:click={addBulkEntry}>
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke-width="1.5"
                        stroke="currentColor"
                        class="w-5 h-5"
                    >
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                    </svg>
                </button>
                <input
                    type="submit"
                    class="btn btn-success w-16 fixed ml-3 mt-5"
                    on:click={submitBulk}
                    value="Submit"
                />

                <!--                <input type="submit" class="btn btn-success ml-7 w-24" on:click={addPref} value="Add"/>-->
            </label>
        </label>
    </form>
</main>

<style>
    main {
        text-align: center;
    }

    .checkboxContainer {
        width: 100%;
        display: flex;
        justify-content: center;
        padding: 1em;
    }

    .checkboxContainer input {
        margin-right: 0.5em;
    }
</style>
