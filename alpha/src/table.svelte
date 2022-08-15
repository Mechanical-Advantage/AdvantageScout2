<!-- <script>

let columns = ["Device Name", "Route", "Heartbeat", ""]
	let data = [
    ["Device 1", "111.111.111", "1"],
    ["Device 2", "222.222.222", "2"],
    ["Device 2", "333.333.333", "3"],

  ]
	
	// function addRow() {
	// 	data = [...data, [...newRow]]
	// 	newRow = columns
	// }
	
	function deleteRow(rowToBeDeleted) {
		data = data.filter(row => row != rowToBeDeleted)
	}

</script>

<main>

    <table>
        <thead>
            {#each columns as column}
                <th>{column}</th>
            {/each}
        </thead>
        
        {#each data as row}
            <tr>
                {#each row as cell}
                <td contenteditable="false" bind:innerHTML={cell} />
                {/each}
                <button on:click={() => deleteRow(row)}>
                    X
                </button>
            </tr>
        {/each}
        
        
    </table>

</main>

<style>

table {
    border-collapse: collapse;
    width: 100;
}

tr {
    border-bottom: 1px solid #ccc;

}

td {
    padding: 10px;
    border-right: 1px solid #ccc;
}

thead {
    background-color: rgb(0, 153, 255);
}

</style> -->
