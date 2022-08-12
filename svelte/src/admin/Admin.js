import AdminComponent from "./AdminComponent.svelte";

export default class App {
    #adminComponent = null;

    constructor() {
        console.log("Hello, this is the module for the admin page!");
        this.#adminComponent = new AdminComponent({
            target: document.body
        });
    }
}
