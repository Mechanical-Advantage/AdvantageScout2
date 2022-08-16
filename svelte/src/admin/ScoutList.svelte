<script>
	import { onMount } from "svelte";
	let cols = 3;
  let items = [];

	
	
  let name = "";
		onMount(async () => {
      const response = await fetch("/admin/get_scouts", {method: "GET"})
		  const data = await response.json();
		  items = data;
    });  

  const addItem = () => {
    items = [
      ...items,
      {
        name,
        enabled: false
      }
    ];
    name = "";
  };

  const remove = item => {
    items = items.filter(i => i !== item);
  };

  const toggle = item => {
    item.enabled = !item.enabled;
    items = items;
		doPost(item.name,"/admin/toggle_scout")
		
  };
  async function doPost (scoutname,actionUrl){
    console.log(actionUrl)
    if (actionUrl == "/admin/toggle_scout") {
      const formData = new FormData()
      formData.append("scout",scoutname)
      console.log(scoutname)
      const res = await fetch('/admin/toggle_scout', {
      method: 'POST',
      body: formData
      })
    }
    actionUrl ="none";
  };
  async function getScouts(){
    const response = await fetch("/admin/get_scouts", {method: "GET"})
		const data = await response.json();
		items = data;
  }
</script>

<style>
  div,
  h1 {
    color: #333;
    max-width: 300px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
  }
  #name {
    width: 100%;
  }
  form {
    margin-bottom: 0.5em;
  }
  input[type="text"] {
    outline: none;
    margin: 0;
  }
  input[type="text"]:focus {
    border-color: #b53fe8;
    box-shadow: 0 0 2px #b53fe8;
  }

  label {
    display: block;
    text-transform: uppercase;
    font-size: 0.8em;
    color: #777;
		opacity: 1.0;
  }
	button{
		border:0;
		cursor: pointer;
		border-radius: 6px;
		padding: 8px 12px;
		font-weight: bold;
		box-shadow: 1px 2px 3px;
		background: #ea4566;
	}
		.enabled {
			background: #11dd42;
		}
	.remove{
		background: #120fbf;
        color: #bfad0f;
        font-size: 12px;
	}
</style>

<div>
  <h1>Available Scouts</h1>

  <form on:submit|preventDefault={addItem}>
    <label for="name">Add a scout</label>
    <input id="name" type="text" bind:value={name} />
  </form>

  <ul>
		<tbody>
{#each items as item, i}
    {#if i % cols == 0}
     <tr >
      {#each Array(cols) as _,j}
        {#if items[i/cols*cols + j]}
       <td><button class:enabled={items[i/cols*cols + j].enabled} on:click={() => toggle(items[i/cols*cols + j])}>{items[i/cols*cols + j].name}</button></td>
<td><button class:remove  on:click={() => remove(items[i/cols*cols + j])}>&times;</button></td>  
         {/if}
       {/each}
      </tr>
    {/if}
{/each}
		</tbody>
  </ul>
</div>
