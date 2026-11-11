<script lang="ts">
  import { onMount } from "svelte";
  import { Capacitor } from "@capacitor/core";
  import { App as CapacitorApp } from "@capacitor/app";
  import Router from "svelte-spa-router";
  import AppHeader from "./components/AppHeader.svelte";
  import Toast from "./components/Toast.svelte";
  import Home from "./routes/Home.svelte";
  import Admin from "./routes/Admin.svelte";
  import Game from "./routes/Game.svelte";
  import SetupModal from "./routes/SetupModal.svelte";
  import Match from "./routes/scouting/Match.svelte";
  import Pit from "./routes/scouting/Pit.svelte";
  import Super from "./routes/scouting/Super.svelte";
  import { startHeartbeat } from "./lib/heartbeat";
  import { flushQueue } from "./lib/upload-queue.svelte";
  import { UPLOAD_CHECK_INTERVAL, BLE_RECONNECT_INTERVAL } from "./lib/config";
  import { api } from "./lib/api.svelte";
  import { isOnScoutingForm } from "./lib/scouting-route";

  const routes = {
    "/": Home,
    "/admin": Admin,
    "/game": Game,
    "/setupmodal": SetupModal,
    "/scouting/match": Match,
    "/scouting/pit": Pit,
    "/scouting/super": Super,
  };

  onMount(() => {
    startHeartbeat();
    flushQueue();
    setInterval(flushQueue, UPLOAD_CHECK_INTERVAL);

    if (Capacitor.isNativePlatform()) {
      const tryConnect = () => {
        if (api.status !== "connected" && api.status !== "connecting") {
          api.connect().catch(() => {
            // Reflect the failure reactively
          });
        }
      };
      tryConnect();
      setInterval(tryConnect, BLE_RECONNECT_INTERVAL);

      CapacitorApp.addListener("backButton", ({ canGoBack }) => {
        if (canGoBack) {
          history.back();
        } else {
          CapacitorApp.exitApp();
        }
      });
    }

    window.addEventListener("beforeunload", (e) => {
      if (!isOnScoutingForm()) return;
      e.preventDefault();
      e.returnValue = "";
    });
  });
</script>

<main class="min-h-screen bg-bg text-fg">
  <div class="px-4 py-1">
    <AppHeader />
    <Router {routes} />
  </div>
  <Toast />
</main>
