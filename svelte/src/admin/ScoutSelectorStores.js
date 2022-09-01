import {writable} from "svelte/store";

export const mouseCoords= writable({x: 0, y: 0});
export const withinBox= writable(false);
export const movin = writable(false);
export const withinTrash = writable(false);
export const activeState = writable(false);