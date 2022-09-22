<script>
    import { color } from "./stores.js";
    import { otherColor } from "./stores.js";

    export let text = "🟦🟥";

    function toggle() {
        if (text === "🟦🟥") {
            text = "🟥🟦";
            color.update((color) => (color = "red"));
            otherColor.update((color) => (color = "blue"));
        } else if (text === "🟥🟦") {
            text = "🟦🟥";
            color.update((color) => (color = "blue"));
            otherColor.update((color) => (color = "red"));
        }
    }
</script>

<main>
    <button on:click={toggle}>{text}</button>
</main>

<style>
</style>
