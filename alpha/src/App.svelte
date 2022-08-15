<script>
	import Hidden from './Hidden.svelte';
	import { onMount } from "svelte";

	let child;

	let fieldOrientationAnswer = '';
	let fieldOrintationSelected;
	let fieldOrientationChoices = [
		{id: 1, text: 'Red right, Blue left'},
		{id: 2, text: 'Red left, Blue right'}
	];

	let devModeAnswer = '';
	let devModeSelected;
	let devModeChoices = [
		{id: 1, text: 'disabled'},
		{id: 2, text: 'enabled'}
	]

	let schedulingMethodAnswer = '';
	let schedulingMethodSelected;
	let SchedulingMethodChoices = [
		{id: 1, text: 'manual'},
		{id: 2, text: 'auto'}
	]

	function handleSubmit() {
		alert(`answered question ${selected.id} (${selected.text}) with "${answer}"`);
	}

	//const obj = {"name": "John", "Age": 30};
	//let keys = Object.keys(obj);
	//let values = Object.values(obj);
	//let entries = Object.entries(obj);

	onMount(async () => {
fetch("http://127.0.0.1:8000/get_devices", {
	  method: "GET"
  })
  .then(response => response.json())
  .then(data => {
		console.log(data);
  }).catch(error => {
    console.log(error);
    return [];
  });
});
</script>

<h1><strong>AdvantageScout Admin Page</strong></h1>
<button on:click={child.show}>Dev Tools</button>

<Hidden bind:this={child} on:show={e => child.shown = e.detail}>
	<h2><strong>Config</strong></h2>
	<h3>Game:</h3>
	<input>
	<h3>Event:</h3>
	<input>
	<h3>Field orientation:</h3>
	<select value={fieldOrintationSelected} on:change="{() => fieldOrientationAnswer = ''}">
		{#each fieldOrientationChoices as question}
			<option value={question}>
				{question.text}	
			</option>
		{/each}
	</select>
	<h3>Dev Mode:</h3>
	<select value={devModeSelected} on:change="{() => devModeAnswer = ''}">
		{#each devModeChoices as question}
			<option value={question}>
				{question.text}	
			</option>
		{/each}
	</select>
	<h3>Scheduling Method:</h3>
	<select value={schedulingMethodSelected} on:change="{() => schedulingMethodAnswer = ''}">
		{#each SchedulingMethodChoices as question}
			<option value={question}>
				{question.text}	
			</option>
		{/each}
	</select>
</Hidden>


<style>
	h3 {
		width: 200px;
		max-width: 100%;
		font-size: 15px;
		line-height: 2px;
	}

	h2 {
		font-size: 20px;
		line-height: 1.5px;
	}

	h1 {
		font-size: 30px;
		line-height: 1.5px;
	}

	.grid-container {
  		display: grid;
		grid-template-columns: 80px 200px auto 40px;

	}
</style>