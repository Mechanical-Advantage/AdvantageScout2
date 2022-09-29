<!-- <script>
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

    // if device.last_battery is between 70 - 100, bg-green-500
    // if device.last_battery is between 30 - 69, bg-yellow-500
    // if device.last_battery is between 0 - 29, bg-red-500

    const batteryColor = (battery , charge) => {
        let batteryCharge;
        let chargeStatus;
        if (charge == 1) {

             chargeStatus =  "animate-pulse duration-30000 ";
        }
        else if (battery < 30){
            chargeStatus = "animate-pulse duration-1000 ";

        }

        if (battery >= 70) {
             batteryCharge=  "text-black bg-green-500";
        } else if (battery >= 30) {
            batteryCharge = "text-black bg-yellow-500";
        } else {
            batteryCharge = "text-white bg-red-500";
        }
        return batteryCharge + " " + chargeStatus;

    };

    const scoutStatus = (status) => {
        if (status == 0) {
            return "Auto"
        }
        else if (status == 1) {
            return "Teleop"
        }
        else if (status == 2) {
            return "Endgame"
        }
        else if (status == 3) {
            return "Pit Scout"
        }
    };


</script>



    <table class="table-auto border-separate border-spacing-2">
    <thead>
      <tr class="border-slate-700">
        <th>Device Name</th>
        <th>Heartbeat</th>
        <th>Route</th>
        <th>Battery</th>
        <th>Status</th>
        <th>Team</th>
        <th>Match</th>
        <th>Scout Name</th>
      </tr>
    </thead>
    <tbody class="rounded-md">
        {#each devices as device}
        <tr >
            
            <td >{device.name}</td>
            <td class="{((device.last_heartbeat > 1646270198) ? "bg-red-900" : "bg-[#f59e0b]")}" >{device.last_heartbeat}</td>
            <td>{device.last_route}</td>
            <td class="{batteryColor(device.last_battery, device.last_charging)}">{device.last_battery}</td>
            <td>{scoutStatus(device.last_status)}</td>
            <td>{device.last_team != null ? device.last_team : "No Team"}</td>
            <td>{device.last_match != null ? device.last_match : "No Matches"}</td>
            <td>{device.last_scoutname != null ? device.last_scoutname : "No Scout"}</td>

        </tr>
        {/each}

    </tbody>

    </table>




  -->
