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

        // hover over the button to see the color change
        // if scout is enabled change hover color to green
        // if scout is disabled change hover color to red
        //class="bg-success py-2 px-4 text-sm font-medium text-gray-900 bg-white border-t border-b border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:hover:text-white dark:hover:bg-gray-600 dark:focus:ring-blue-500 dark:focus:text-white"
        if (scout.enabled) {
            scout.hoverColor = "green";
        } else {
            scout.hoverColor = "red";
        }

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
<!-- <div class="grid grid-cols-4 auto-rows-auto gap-y-2 gap-x-44"> -->
    <div class="flex flex-wrap w-screen fixed">

    {#each scoutList as scout, i}

        <!-- {#if i % cols == 0}
                    <tr>
                        {#each Array(cols) as _, j}
                            {#if scoutList[(i / cols) * cols + j]}
                                <td>
                                    <button
                                        class:enabled={scoutList[(i / cols) * cols + j].enabled}
                                        on:click={() => toggle(scoutList[(i / cols) * cols + j])}
                                    >
                                        {scoutList[(i / cols) * cols + j].name}
                                    </button>
                                </td>
                                <td>
                                    <button class:remove on:click={() => remove(scoutList[(i / cols) * cols + j])}>
                                        &times;
                                    </button>
                                </td>
                            {/if}

                        {/each}
                        
                    </tr>
                {/if} -->

            <div class="item w-32 h-32">
            <div class="tooltip" data-tip="Toggle {scout.name}">
                <button
                    class:enabled={scout.enabled}
                    on:click={() => toggle(scout)}
                    class:hover={scout.hoverColor}
                    class="w-full h-full "

                >
                    {scout.name}
                </button>
            </div>
            </div>
            <!-- <button
                on:click={() => toggle(scoutList[i])}
                class:enabled={scoutList[i].enabled}
                type="button"
                class="text-center bg-error py-2 px-4 text-sm font-medium text-gray-900 rounded-l-lg border border-gray-200 hover:z-10 hover:text-blue-700 focus:z-10 focus:ring-2 focus:ring-blue-700 focus:text-blue-700 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:hover:text-white dark:hover: dark:focus:ring-blue-500 dark:focus:text-white"
            >
                {scout.name}
            </button> -->
            

    {/each}
</div>
<!-- </div> -->

<style>
    div,
    h1 {
        color: #333;
        max-width: 300px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell,
            "Helvetica Neue", sans-serif;
    }
    #name {
        width: 100%;
    }
    form {
        margin-bottom: 0.5em;
    }
    input[type="text"] {
        outline: none;
        margin: 0;
    }
    input[type="text"]:focus {
        border-color: #b53fe8;
        box-shadow: 0 0 2px #b53fe8;
    }

    label {
        display: block;
        text-transform: uppercase;
        font-size: 0.8em;
        color: #777;
        opacity: 1;
    }
    button {
        border: 0;
        cursor: pointer;
        border-radius: 6px;
        padding: 14% 24%;
        font-weight: bold;
        box-shadow: 1px 2px 3px;
        background: #ea4566;
    }
    .enabled {
        background: #11dd42;
    }
    .remove {
        background: #120fbf;
        color: #bfad0f;
        font-size: 12px;
        padding: 10px;
    }
</style>

