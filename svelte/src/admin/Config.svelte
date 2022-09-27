<script>
    import Hidden from "./Hidden.svelte";
    import { onMount } from "svelte";

    let child;

    let fieldOrientationAnswer = "";
    let fieldOrintationSelected;
    let fieldOrientationChoices = [
        { id: 1, text: "Red right, Blue left" },
        { id: 2, text: "Red left, Blue right" }
    ];

    let devModeAnswer = "";
    let devModeSelected;
    let devModeChoices = [
        { id: 1, text: "disabled" },
        { id: 2, text: "enabled" }
    ];

    let schedulingMethodAnswer = "";
    let schedulingMethodSelected;
    let SchedulingMethodChoices = [
        { id: 1, text: "manual" },
        { id: 2, text: "auto" }
    ];

    function handleSubmit() {
        alert(`answered question ${selected.id} (${selected.text}) with "${answer}"`);
    }

    //const obj = {"name": "John", "Age": 30};
    //let keys = Object.keys(obj);
    //let values = Object.values(obj);
    //let entries = Object.entries(obj);

    onMount(async () => {
        fetch("/admin/get_devices", {
            method: "GET"
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(" ");
            })
            .catch((error) => {
                console.log(error);
                return [];
            });
    });
</script>

<h1><strong>AdvantageScout Admin Page</strong></h1>
<button on:click={child.show}>Config</button>

<div class="config">
    <Hidden bind:this={child} on:show={(e) => (child.shown = e.detail)}>
        <div>
            <div>
                <h3>Game:</h3>
                <input class="game" />
            </div>
            <div>
                <h3>Event:</h3>
                <input class="event" />
            </div>
            <div class="field-orientation">
                <h3>Field orientation:</h3>
                <select
                    class="field-orientation"
                    value={fieldOrintationSelected}
                    on:change={() => (fieldOrientationAnswer = "")}
                >
                    {#each fieldOrientationChoices as question}
                        <option value={question}>
                            {question.text}
                        </option>
                    {/each}
                </select>
            </div>
            <div class="dev-mode">
                <h3>Dev Mode:</h3>
                <select class="dev-mode" value={devModeSelected} on:change={() => (devModeAnswer = "")}>
                    {#each devModeChoices as question}
                        <option value={question}>
                            {question.text}
                        </option>
                    {/each}
                </select>
            </div>

            <div class="scheduling-method">
                <h3>Scheduling Method:</h3>
                <select
                    class="scheduling-method"
                    value={schedulingMethodSelected}                 
                    on:change={() => (schedulingMethodAnswer = "")}
                >
                    {#each SchedulingMethodChoices as question}
                        <option value={question}>
                            {question.text}
                        </option>
                    {/each}
                </select>
            </div>
        </div>
        <div class="block-schedling">
            <div>
                <h3>Training Length</h3>
                <input id="blockTrainingLength" type="number" placeholder="Enter # of matches..." />
            </div>
            <div>
                <h3>Group Size</h3>
                <input id="blockTrainingLength" type="number" placeholder="Enter # of matches..." />
            </div>
            <div>
                <h3>Break Length</h3>
                <input id="blockTrainingLength" type="number" placeholder="Enter # of matches..." />
            </div>
            <div>
                <h3>Start</h3>
                <input id="blockTrainingLength" type="number" placeholder="Enter # of matches..." />
            </div>
            <div>
                <h3>End</h3>
                <input id="blockTrainingLength" type="number" placeholder="Enter # of matches..." />
            </div>
        </div>
    </Hidden>
</div>

<button class="btn btn-outline">Button</button>
<button class="btn btn-outline btn-primary">Button</button>
<button class="btn btn-outline btn-secondary">Button</button>
<button class="btn btn-outline btn-accent">Button</button>


