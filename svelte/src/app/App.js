import AppComponent from "./AppComponent.svelte";
import Game from "./game/Game.js";

export default class App {
    #appComponent = null;
    #game = null;

    constructor() {
        console.log("Hello, this is the module for the app!", isWeb, gameConfig);
        this.#appComponent = new AppComponent({
            target: document.body
        });
        this.#game = new Game(document.getElementById("game"));
    }
}
