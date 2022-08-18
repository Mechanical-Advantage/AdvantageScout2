<script>
    import { onMount } from "svelte";

    let matches = [
        { teams: [6328, 2713, 6328, 4176, 6367, 5563], uploaded: [true, true, true, true, true, true] },
        { teams: [3323, 8626, 501, 1761, 1922, 2423], uploaded: [true, true, true, true, true, true] },
        { teams: [8604, 6201, 69, 1099, 5000, 6723], uploaded: [true, true, true, true, true, true] },
        { teams: [4909, 5846, 2877, 2084, 1757, 1965], uploaded: [true, true, true, true, true, true] },
        { teams: [6933, 125, 7674, 6529, 95, 5752], uploaded: [true, true, true, true, true, true] },
        { teams: [7822, 5687, 5347, 97, 151, 6763], uploaded: [true, true, true, true, true, true] },
        { teams: [69, 5735, 5000, 5563, 3323, 6201], uploaded: [true, true, true, true, true, true] },
        { teams: [1099, 4311, 8626, 1761, 6723, 2877], uploaded: [true, true, true, true, true, true] },
        { teams: [2423, 6529, 1965, 1757, 6367, 8604], uploaded: [true, true, true, true, true, true] },
        { teams: [7822, 5752, 1474, 6933, 95, 4909], uploaded: [true, true, true, true, true, true] }
    ];

    // let name = "";
    // onMount(async () => {
    //     const response = await fetch("/admin/get_scouts", { method: "GET" });
    //     const data = await response.json();
    //     matches = data;
    // });

    // function deleteRow(rowToBeDeleted) {
    //     data = data.filter((row) => row != rowToBeDeleted);
    // }
</script>

<main>
    <table>
        <thead>
            <tr>
                <th>match</th>
                <th class="red">R1</th>
                <th class="red">R2</th>
                <th class="red">R3</th>
                <th class="blue">B1</th>
                <th class="blue">B2</th>
                <th class="blue">B3</th>
            </tr>
        </thead>

        <tbody>
            {#each matches as match, i}
                <tr />
                <td class={match.teams.includes(6328) ? "matchUs" : "match"}>match {i + 1}</td>
                {#each match.teams as team, i}
                    <td
                        class={team == 6328
                            ? match.uploaded[i]
                                ? "uploadedUs"
                                : "notUploadedUs"
                            : match.uploaded[i]
                            ? "uploaded"
                            : "notUploaded"}
                    >
                        {team}
                    </td>
                {/each}
            {/each}
        </tbody>
    </table>
</main>

<style>
    table {
        border-collapse: collapse;
        width: 100;
    }

    tr {
        border: 1px solid rgb(0, 0, 0);
    }

    td {
        padding: 10px;
        border: 1px solid rgb(0, 0, 0);
        background-color: rgb(200, 200, 200);
        font-weight: bold;
    }

    th {
        padding: 10px;
        border: 1px solid rgb(0, 0, 0);
        background-color: rgb(150, 150, 150);
    }

    .red {
        background-color: rgba(255, 0, 0, 0.5);
    }

    .blue {
        background-color: rgba(0, 0, 255, 0.5);
    }

    .uploaded {
        background-color: rgb(225, 225, 0);
        font-weight: normal;
        color: rgb(0, 0, 0);
    }

    .notUploaded {
        background-color: rgb(200, 200, 200);
        font-weight: normal;
        color: rgb(0, 0, 0);
    }

    .uploadedUs {
        background-color: rgb(225, 225, 0);
        font-weight: bold;
        color: rgb(0, 150, 255);
    }

    .notUploadedUs {
        background-color: rgb(200, 200, 200);
        font-weight: bold;
        color: rgb(0, 150, 225);
    }

    .matchUs {
        background-color: rgb(225, 225, 0);
        font-weight: bold;
        color: rgb(0, 0, 0);
    }

    .match {
        background-color: rgb(200, 200, 200);
        font-weight: bold;
        color: rgb(0, 0, 0);
    }
</style>
