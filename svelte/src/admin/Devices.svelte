<script>
    import {onMount} from "svelte";
    // [
    //     {
    //         name: "Scout Laptop",
    //         last_heartbeat: 1649192664,
    //         last_route: "127.0.0.1",
    //         last_battery: 100,
    //         last_charging: 1,
    //         last_status: 0,
    //         last_team: 4909,
    //         last_match: 18,
    //         last_scoutname: "John Doe"
    //     },
    //     {
    //         name: "6328 Scout 2",
    //         last_heartbeat: 1649122185,
    //         last_route: "COM5",
    //         last_battery: 87,
    //         last_charging: 0,
    //         last_status: 1,
    //         last_team: 5687,
    //         last_match: 1312,
    //         last_scoutname: "Aryan Kulkarni"
    //     },
    //     {
    //         name: "6328 Scout 3",
    //         last_heartbeat: 1649122182,
    //         last_route: "COM6",
    //         last_battery: 88,
    //         last_charging: 0,
    //         last_status: 1,
    //         last_team: 95,
    //         last_match: 1312,
    //         last_scoutname: "Aum Patel"
    //     },
    //     {
    //         name: "6328 Scout 4",
    //         last_heartbeat: 1649122179,
    //         last_route: "COM7",
    //         last_battery: 90,
    //         last_charging: 0,
    //         last_status: 1,
    //         last_team: 6328,
    //         last_match: 1312,
    //         last_scoutname: "Ayush Kulkarni"
    //     },
    //     {
    //         name: "6328 Scout 5",
    //         last_heartbeat: 1649122153,
    //         last_route: "COM8",
    //         last_battery: 82,
    //         last_charging: 0,
    //         last_status: 1,
    //         last_team: 5563,
    //         last_match: 1312,
    //         last_scoutname: "Advaith Dasu"
    //     },
    //     {
    //         name: "6328 Scout 1",
    //         last_heartbeat: 1649119104,
    //         last_route: "COM4",
    //         last_battery: 88,
    //         last_charging: 0,
    //         last_status: 1,
    //         last_team: 125,
    //         last_match: 1312,
    //         last_scoutname: "Keith White"
    //     },
    //     {
    //         name: "6328 Scout 6",
    //         last_heartbeat: 1649113662,
    //         last_route: "COM9",
    //         last_battery: 100,
    //         last_charging: 0,
    //         last_status: 0,
    //         last_team: 2877,
    //         last_match: 1223,
    //         last_scoutname: "John Doe"
    //     },
    //     {
    //         name: "6328 Scout 7",
    //         last_heartbeat: 1648338548,
    //         last_route: "forwarder/COM3",
    //         last_battery: 43,
    //         last_charging: 1,
    //         last_status: 0,
    //         last_team: 1757,
    //         last_match: 60,
    //         last_scoutname: "John Doe"
    //     },
    //     {
    //         name: "6328 Scout 9",
    //         last_heartbeat: 1648338548,
    //         last_route: "forwarder/COM5",
    //         last_battery: 45,
    //         last_charging: 1,
    //         last_status: 0,
    //         last_team: 6529,
    //         last_match: 60,
    //         last_scoutname: "John Doe"
    //     },
    //     {
    //         name: "6328 Scout 10",
    //         last_heartbeat: 1648338548,
    //         last_route: "forwarder/COM6",
    //         last_battery: 36,
    //         last_charging: 1,
    //         last_status: 0,
    //         last_team: 1761,
    //         last_match: 60,
    //         last_scoutname: "John Doe"
    //     },
    //     {
    //         name: "6328 Scout 8",
    //         last_heartbeat: 1648334565,
    //         last_route: "forwarder/COM4",
    //         last_battery: 30,
    //         last_charging: 0,
    //         last_status: 0,
    //         last_team: 1965,
    //         last_match: 52,
    //         last_scoutname: "John Doe"
    //     },
    //     {
    //         name: "KWLT",
    //         last_heartbeat: 1646270198,
    //         last_route: "192.168.1.202",
    //         last_battery: 100,
    //         last_charging: 1,
    //         last_status: 1,
    //         last_team: 8242,
    //         last_match: 50,
    //         last_scoutname: "Jonathan McGurrin"
    //     },
    //     {
    //         name: "scoutingPC",
    //         last_heartbeat: 1643162807,
    //         last_route: "127.0.0.1",
    //         last_battery: 100,
    //         last_charging: 1,
    //         last_status: 0,
    //         last_team: 8499,
    //         last_match: 74,
    //         last_scoutname: "John Doe"
    //     },
    //     {
    //         name: "Scout Laptop #2",
    //         last_heartbeat: 1626909514,
    //         last_route: "192.168.1.184",
    //         last_battery: 81,
    //         last_charging: 0,
    //         last_status: 0,
    //         last_team: null,
    //         last_match: null,
    //         last_scoutname: "John Doe"
    //     }
    // ];

    let devices = [];
    onMount(async () => {
        const response = await fetch("/admin/get_devices", { method: "GET" });
        const data = await response.json();
        devices = data;
    });


</script>

<div class="bg-[#1E3A8A]">
<div class="overflow-x-auto bg-blue-200">
    <table class="table">
    <thead>
      <tr>
        <th>Device Name</th>
        <th>Heartbeat</th>
        <th>Route</th>
        <th>Battery</th>
        <th>Charging</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody >
        {#each devices as device}
        <tr>
            
            <td >{device.name}</td>
            <td>{device.last_heartbeat}</td>
            <td>{device.last_route}</td>
            <td>{device.last_battery}</td>
            <td>{device.last_charging}</td>
            <td>{device.last_status}</td>
        </tr>
        {/each}

    </tbody>

    </table>



</div>
</div>
 
