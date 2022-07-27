import GameComponent from "./GameComponent.svelte";

export default class Game {
    #gameComponent = null;

    constructor(root) {
        console.log("Hello, this is the module for the 2022 game!", root);
        this.#gameComponent = new GameComponent({
            target: root
        });
    }

    // EXAMPLE METHODS
    setMode(mode) {}
    getData() {}
}
