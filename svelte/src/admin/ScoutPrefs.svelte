<script>
	import { onMount } from "svelte";
	let cols = 3;
        let scoutPrefs = [];

	
	
  let scout = "";
  let team = "";
	onMount(async () => {
        const response = await fetch("/admin/get_scoutprefs", {method: "GET"})
	    const data = await response.json();
	    scoutPrefs = data;
    });  
  const updatePrefs =() => {
        if (action == 0 || action == 1) {
            record = scoutPrefs.splice(index, 1)[0]
            scoutPrefs.splice(index + ((action == 0) ? -1 : 1), 0, record)
        } else if (action == 2) {
            scoutPrefs.splice(index, 1)
        }
        

  const addScoutPref = () => {
    scoutPrefs = [
      ...scoutPrefs,
      {
        team,
        scout 
      }
    ];
    doPost(team,scout, "/admin/set_scoutprefs")
    name = "";
  };

   
  async function doPost (data,actionUrl){
      const formData = new FormData()
      const res = await fetch(actionUrl, {
      method: 'POST',
      data: json.stringify(formData)
      })
  };
  async function getScoutPrefs(){
    const response = await fetch("/admin/get_scoutprefs", {method: "GET"})
		const data = await response.json();
		scoutPrefs = data;
  }
</script>

<div>
    <h1>Scout Preferences</h1>

    <form on:submit|preventDefault={addScoutPref}>
        <label for="scout">Add a preference</label>
        <input id="scout" type="text" bind:value={scout} />
        <input id="team" type="text" bind:value={team} />
    </form>

    <ul>
        <tbody>
            {#each scoutPrefs as pref}
                <tr>
                    <td>{pref.team}</td>
                    <td>{pref.scout}</td>
                    <td>>&#x2191;</td>
                    <td>&#x2193;</td>
                    <td>&#x1F5D1;</td>
                </tr>
            {/each}
        </tbody>
    </ul>
</div>

<style>
    div,
    h1 {
        color: #333;
        max-width: 300px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell,
            "Helvetica Neue", sans-serif;
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
        opacity: 1;
    }
    button {
        border: 0;
        cursor: pointer;
        border-radius: 6px;
        #padding: 14% 24%;
        width: 150px;
        height: 40px;
        font-weight: bold;
        box-shadow: 1px 2px 3px;
        background: #ea4566;
    }
    .enabled {
        background: #11dd42;
    }
    .remove {
        #background: #120fbf;
        background: #fefefe;
        color: #ff0000;
        font-size: 22px;
        width: 40px;
        height: 40px;
        padding: 10px;
        border-right: 40px;
    }
</style>
