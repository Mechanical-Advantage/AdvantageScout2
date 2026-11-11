import { mount, unmount } from "svelte";
import "./app.css";
import App from "./App.svelte";

let currentInstance: object | null = null;

export function mountApp(target: HTMLElement): object {
  target.innerHTML = "";
  currentInstance = mount(App, { target });
  window.__advantagescoutUnmount = () => {
    if (currentInstance) {
      unmount(currentInstance);
      currentInstance = null;
    }
  };
  return currentInstance;
}

mountApp(document.getElementById("app")!);
