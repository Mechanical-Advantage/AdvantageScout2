<script>
    import { spring } from "svelte/motion";
    import { pannable } from "./pannable.js";
    import { createEventDispatcher } from "svelte";
    import { withinBox, movin, withinTrash, activeState } from "./ScoutSelectorStores";

    let m = { x: 0, y: 0 };
    export let name, enabled;
    const dispatch = createEventDispatcher();

    const coords = spring(
        { x: 0, y: 0 },
        {
            stiffness: 0.1,
            damping: 0.1
        }
    );

    function handlePanStart() {
        coords.stiffness = coords.damping = 1;
        $movin = true;
        $activeState = enabled;
    }

    function handlePanMove(event) {
        coords.update(($coords) => ({
            x: $coords.x + event.detail.dx,
            y: $coords.y + event.detail.dy
        }));
    }

    function handlePanEnd(event) {
        $movin = false;
        if ($withinTrash) {
            deleteName();
        } else if (enabled && !$withinBox) {
            console.log("disabled");
            disableName();
            console.log("disabled");
        } else if (!enabled && $withinBox) {
            enableName();
            console.log("enabled");
            this.parentNode.removeChild(this);
        }

        coords.stiffness = 0.2;
        coords.damping = 0.4;
        coords.set({ x: 0, y: 0 });
    }

    function handleMousemove(e) {
        m.x = e.clientX;
        m.y = e.clientY;
    }

    function enableName() {
        dispatch("enable", {
            text: name
        });
    }

    function disableName() {
        dispatch("disable", {
            text: name
        });
    }

    function deleteName() {
        dispatch("delete", {
            text: name
        });
    }

    function doubleClick() {
        if (enabled) {
            disableName();
        } else {
            enableName();
        }
    }
</script>

<div
    class="box"
    use:pannable
    on:panstart={handlePanStart}
    on:panmove={handlePanMove}
    on:panend={handlePanEnd}
    on:dblclick={doubleClick}
    style="transform:
		translate({$coords.x}px,{$coords.y}px);
background-color: {enabled ? '#47b45d' : '#1600d9'}; 
color: {enabled ? '#FFFFFF' : '#FFFFFF'}"
>
    {name}
</div>

<style>
    .box {
        --width: 100px;
        --height: 50px;
        position: absolute;
        width: var(--width);
        height: var(--height);
        border-radius: 4px;
        background-color: #54ec4e;
        cursor: move;
        color: white;
        text-align: center;

        display: flex;
        justify-content: center;
        align-content: center;
        flex-direction: column;
        /* Column | row */
    }
</style>
