<script>
    import Config from "./Config.svelte";
    import ScoutList from "./ScoutList.svelte";
    import MatchTable from "./MatchTable.svelte";
    import ActiveScouts from "./ActiveScouts.svelte";
    import ScoutPrefsv2 from "./ScoutPrefsv2.svelte";
    import Devices from "./Devices.svelte";
    import ConfigModal from "./ConfigModal.svelte";
</script>

<div class="relative">
    <ActiveScouts />
</div>
<div class="absolute ml-[50px] mt-[100px]">
    <MatchTable />
</div>

<div class="absolute top-10 ml-[900px]">
    <ScoutPrefsv2 />
</div>

<div class="absolute top-10 ml-[1250px]">
    <Devices/>
</div>

<div class="absolute bottom">
    <ConfigModal />   
</div>