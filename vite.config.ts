import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tailwindcss(), svelte(), tsconfigPaths()],
  publicDir: "assets",
  server: {
    host: true,
    port: 5173,
  },
});
