<script>
    import ScoutNameBlock from "./ScoutNameBlock.svelte";
    import { onMount, tick } from "svelte";
    import { activeState, mouseCoords, movin, withinBox, withinTrash } from "./ScoutSelectorStores";
    import ScoutList from "./ScoutList.svelte";
    let dropBoxHeight = 300;
    let addScoutEntry = "";
    let disabled = [];
    let enabled = [];

    async function getScouts() {
        const response = await fetch("/admin/get_scouts", { method: "GET" });
        const data = await response.json();
        return data;
    }
    let availableScoutsPromise = getScouts();

    async function doPost(scoutName, actionUrl) {
        const formData = new FormData();
        formData.append("scout", scoutName);
        const res = await fetch(actionUrl, {
            method: "POST",
            body: formData
        });
    }

    function testFunc() {
        alert("Hello World");
    }

    async function processScouts() {
        await availableScoutsPromise;
        let tempName = "";
        availableScoutsPromise.then((data) => {
            for (let i = 0; i < data.length; i++) {
                if (data[i]["enabled"] == true) {
                    enabled.push(data[i]["name"]);
                } else {
                    disabled.push(data[i]["name"]);
                }
            }
            enabled = enabled;
            disabled = disabled;
        });
    }

    let scoutStatus = processScouts();

    let dropBoxRect = document.getElementById("dropBox");
    let trashRect = document.getElementById("trash");
    if (enabled.length > 8) {
        dropBoxHeight = 300 + Math.ceil((enabled.length - 8) / 4) * 125;
    } else {
        dropBoxHeight = 300;
    }
    function mouseCoordHandler(e) {
        if (enabled.length > 8) {
            dropBoxHeight = 300 + Math.ceil((enabled.length - 8) / 4) * 125;
        } else {
            dropBoxHeight = 300;
        }
        console.log($withinBox);
        dropBoxRect = document.getElementById("dropBox");
        let trashRect = document.getElementById("trash");
        $mouseCoords.x = e.clientX;
        $mouseCoords.y = e.clientY;
        if (dropBoxRect !== null) {
            dropBoxRect = dropBoxRect.getBoundingClientRect();
        }
        if (trashRect !== null) {
            trashRect = trashRect.getBoundingClientRect();
        }
        $withinBox =
            dropBoxRect !== null &&
            e.clientX > dropBoxRect.x &&
            e.clientX < dropBoxRect.x + dropBoxRect.width &&
            e.clientY > dropBoxRect.y &&
            e.clientY < dropBoxRect.y + dropBoxRect.height;
        $withinTrash =
            trashRect !== null &&
            e.clientX > trashRect.x &&
            e.clientX < trashRect.x + trashRect.width &&
            e.clientY > trashRect.y &&
            e.clientY < trashRect.y + trashRect.height;
    }

    function mouseUp() {
        if (enabled.length > 8) {
            dropBoxHeight = 300 + Math.ceil((enabled.length - 8) / 4) * 125;
        } else {
            dropBoxHeight = 300;
        }
    }

    function disable(event) {
        console.log("disable");
        enabled = enabled.filter((e) => e !== event.detail.text);
        disabled.unshift(event.detail.text);
        doPost(event.detail.text, "/admin/toggle_scout");
        enabled = enabled;
        disabled = disabled;
    }

    function enable(event) {
        console.log("enable");
        disabled = disabled.filter((e) => e !== event.detail.text);
        enabled.push(event.detail.text);
        doPost(event.detail.text, "/admin/toggle_scout");
        enabled = enabled;
        disabled = disabled;
    }

    function deleteName(event) {
        disabled = disabled.filter((e) => e !== event.detail.text);
        enabled = enabled.filter((e) => e !== event.detail.text);
        doPost(event.detail.text, "/admin/remove_scout");
        enabled = enabled;
    }

    function addName() {
        if (!disabled.includes(addScoutEntry) && !enabled.includes(addScoutEntry)) {
            disabled.unshift(addScoutEntry);
            console.log("Adding Scout");
            if (addScoutEntry != "") {
                doPost(addScoutEntry, "/admin/add_scout");
            }
            addScoutEntry = "";
        }
        disabled = disabled;
    }
</script>

<div class="z-20 w-fit h-fit" on:mousemove={mouseCoordHandler} on:mouseup={mouseUp}>
    <label class="btn modal-button btn-success btn-square w-24 h-24 fixed ml-[630px]" for="entry-modal">
        <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2.5"
            stroke="currentColor"
            class="w-16 h-16"
        >
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
    </label>

    <svg
        id="trash"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke={$withinTrash && $movin ? "red" : "white"}
        class="{$withinTrash && $movin ? 'w-32 h-32 ml-[615px] mt-[110px]' : 'w-24 h-24 ml-[630px] mt-[125px]'} fixed "
    >
        <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
        />
    </svg>

    <div
        id="dropBox"
        style="width:600px;height:{dropBoxHeight}px;border:4px solid {!($movin && $withinBox && !$activeState)
            ? '#FFFFFF'
            : '#00FF00'};"
        class="relative mt-6 ml-3"
    >
        <div on:mousemove={mouseCoordHandler}>
            <div
                class="grid  grid-cols-4 grid-rows-none text-sm gap-x-32 gap-y-16 w-fit h-fit mt-10 ml-[55px] z-30 relative overflow-visible"
            >
                {#each enabled as name (name)}
                    <div class="box row-span-1  col-span-1">
                        <div class="absolute select-none">
                            <ScoutNameBlock {name} enabled={true} on:disable={disable} on:delete={deleteName} />
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    </div>
    <div
        class="grid grid-cols-4 grid-rows-none text-sm gap-x-32 gap-y-16 w-fit h-fit mt-10 ml-[70px] z-30 relative overflow-visible"
    >
        {#each disabled as name (name)}
            <div class="box row-span-1  col-span-1">
                <div class="absolute select-none">
                    <ScoutNameBlock {name} enabled={false} on:enable={enable} on:delete={deleteName} />
                </div>
            </div>
        {/each}
    </div>
    <form on:submit={addName} action="#">
        <input type="checkbox" id="entry-modal" class="modal-toggle" />
        <label for="entry-modal" class="modal cursor-pointer">
            <label class="modal-box relative" for="entry-modal">
                <input
                    type="text"
                    placeholder="Scout Name"
                    class="input input-bordered w-full max-w-xs"
                    bind:value={addScoutEntry}
                />
                <input type="submit" class="btn btn-success ml-7 w-24" on:click={addName} value="Add" />
            </label>
        </label>
    </form>
</div>
