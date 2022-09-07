<script>
    import Config from "./Config.svelte";
    import ScoutList from "./ScoutList.svelte";
    import MatchTable from "./MatchTable.svelte";
    import ActiveScouts from "./ActiveScouts.svelte";
    import ScoutPrefsv2 from "./ScoutPrefsv2.svelte";
</script>

<main class="max-w mx-auth px-4">
    <div class="pt-4 pb-12">
        <ScoutPrefsv2 />
    </div>
    <div>
        <ActiveScouts />
    </div>
</main>
