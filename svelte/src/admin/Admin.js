import AdminComponent from "./AdminComponent.svelte";
import ScoutList from "./ScoutList.svelte";

export default class App {
    #adminComponent = null;

    constructor() {
        console.log("Hello, this is the module for the pls admin page!");
        this.#adminComponent = new AdminComponent({
            target: document.body
            
        });
    
    }
}
